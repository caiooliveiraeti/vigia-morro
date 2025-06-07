from datetime import datetime, timedelta
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
from ..repositories.repository_factory import get_repository
import time

class PredictService:
    def __init__(self):
        self.repo = get_repository()
        self.model = None

    def _obter_dados_para_previsao(self, morro_id, resolucao_minutos):
        """
        Obtém e organiza os dados de solo e meteorologia para um morro específico ou para todos os morros.
        """
        if morro_id:
            print(f"🔄 Obtendo dados para o morro ID: {morro_id}...")
            leituras_solo = self.repo.obter_leituras_solo_por_morro(morro_id, resolucao_minutos)
            meteorologia = self.repo.obter_meteorologia_por_morro(morro_id, resolucao_minutos)
        else:
            print("🔄 Obtendo dados para todos os morros...")
            leituras_solo = self.repo.obter_leituras_solo_para_treino(resolucao_minutos)
            meteorologia = self.repo.obter_meteorologia_para_treino(resolucao_minutos)

        # Criar DataFrames
        df_solo = pd.DataFrame(leituras_solo)
        df_meteorologia = pd.DataFrame(meteorologia)

        if df_solo.empty or df_meteorologia.empty:
            print(f"⚠️ Dados insuficientes para {'o morro ID: ' + morro_id if morro_id else 'todos os morros'}.")
            return None

        # Reorganizar os dados de solo
        df_solo_pivot = df_solo.pivot_table(
            index=["datetime_formatado", "morro_id"],
            columns="tipo_metrica",
            values=["media", "maxima", "minima"]
        ).reset_index()
        df_solo_pivot.columns = [
            f"{col[1]}_solo_{col[0]}" if col[1] else col[0] for col in df_solo_pivot.columns
        ]

        # Realizar o merge
        df = pd.merge(df_meteorologia, df_solo_pivot, left_on=["datetime_formatado", "morro_id"], right_on=["datetime_formatado", "morro_id"], how="inner")

        if df.empty:
            print(f"⚠️ Nenhum dado combinado para {'o morro ID: ' + morro_id if morro_id else 'todos os morros'}.")
            return None

        print(f"✅ Dados organizados para {'o morro ID: ' + morro_id if morro_id else 'todos os morros'}.")
        return df

    def treinar(self):
        print("🔍 Iniciando treinamento do modelo de previsão...")
        resolucao_minutos = 10

        # Obter dados agregados para treinamento
        df = self._obter_dados_para_previsao(None, resolucao_minutos)
        if df is None:
            print("⚠️ Dados insuficientes para treinamento.")
            return

        # Ajustar as regras para identificar risco de desmoronamento
        print("🔧 Ajustando regras para identificar risco de desmoronamento...")
        df["risco_desmoronamento"] = (
            (df["umidade_media"] > 65) &  # Reduzir ainda mais o limite de umidade do ar
            (df["umidade_solo_media"] > 45) &  # Reduzir ainda mais o limite de umidade do solo
            (df["temperatura_solo_media"] < 22) &  # Aumentar ainda mais o limite de temperatura do solo
            (df["chovendo"] == 1) &  # Está chovendo
            ((df["umidade_solo_maxima"] - df["umidade_solo_minima"]) > 10)  # Reduzir ainda mais a variação mínima de umidade do solo
        ).astype(int)

        # Preparar os dados para o treinamento
        X = df[[
            "chovendo",
            "temperatura_media", "umidade_media",
            "umidade_solo_media", "umidade_solo_maxima", "umidade_solo_minima",
            "temperatura_solo_media", "temperatura_solo_maxima", "temperatura_solo_minima"
        ]]
        print("📊 Preparando os dados para o treinamento...")
        print(X.head())
        y = df["risco_desmoronamento"]
        print("📊 Rótulos de risco de desmoronamento:")
        print(y.head())

        print("📊 Dividindo os dados em treino e teste...")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Ajustar hiperparâmetros do modelo para evitar overfitting
        print("🌲 Configurando o modelo RandomForest...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42
        )

        # Avaliar o modelo com validação cruzada
        print("🔍 Avaliando o modelo com validação cruzada...")
        scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring="accuracy")
        print(f"📊 Validação cruzada - Acurácia média: {scores.mean():.2f} (+/- {scores.std():.2f})")

        # Treinar o modelo
        print("🚀 Treinando o modelo...")
        self.model.fit(X_train, y_train)

        # Avaliar o modelo no conjunto de teste
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"✅ Treinamento concluído. Acurácia no conjunto de teste: {accuracy:.2f}")

    def prever(self):
        if not self.model:
            raise ValueError("O modelo ainda não foi treinado. Por favor, treine o modelo antes de realizar previsões.")

        resolucao_minutos = 5

        try:
            while True:
                print("🔄 Iniciando processo de previsão em loop contínuo. Pressione Ctrl+C para interromper.")
                
                # Obter todos os morros
                morros = self.repo.listar_morros()

                for morro in morros:
                    morro_id = morro["morro_id"]
                    print(f"🔍 Realizando previsão para o morro: {morro['nome']} (ID: {morro_id})")

                    # Obter e organizar os dados
                    df = self._obter_dados_para_previsao(morro_id, resolucao_minutos)
                    if df is None:
                        self._desligar_alertas_se_necessario(morro_id)
                        continue

                    # Preparar os dados para previsão
                    X = df[[
                        "chovendo",
                        "temperatura_media", "umidade_media",
                        "umidade_solo_media", "umidade_solo_maxima", "umidade_solo_minima",
                        "temperatura_solo_media", "temperatura_solo_maxima", "temperatura_solo_minima"
                    ]]

                    # Prever risco
                    previsoes = self.model.predict(X)

                    # Verificar se há previsões com risco
                    if any(risco == 1 for risco in previsoes):
                        print(f"⚠️ Risco identificado no morro: {morro['nome']}")
                        self._registrar_alertas(morro_id)
                    else:
                        print(f"✅ Nenhum risco identificado no morro: {morro['nome']}")
                        self._desligar_alertas_se_necessario(morro_id)

                # Aguardar antes de repetir o loop
                time.sleep(15)

        except KeyboardInterrupt:
            print("\n🛑 Previsão interrompida pelo usuário.")

    def _registrar_alertas(self, morro_id: str):
        print(f"🔔 Registrando alertas para o morro ID: {morro_id}...")
        caixas_alerta = self.repo.listar_caixas_alerta_por_morro(morro_id)
        for caixa in caixas_alerta:
            if not self.repo.alerta_ativo_para_caixa(caixa["caixa_id"]):
                self.repo.registrar_alerta(morro_id, caixa["caixa_id"])
                print(f"🔔 Alerta registrado para a caixa '{caixa['caixa_id']}'.")

    def _desligar_alertas_se_necessario(self, morro_id: str):
        print(f"🔕 Verificando alertas para desligar no morro ID: {morro_id}...")
        alertas_ativos = self.repo.listar_alertas_ativos(morro_id)
        agora = datetime.utcnow()
        for alerta in alertas_ativos:
            if alerta["data_inicio"] < agora - timedelta(minutes=10):
                self.repo.desligar_alerta(alerta["alerta_id"])
                print(f"🔕 Alerta desligado para a caixa '{alerta['caixa_id']}' após 10 minutos sem risco.")
