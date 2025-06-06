from datetime import datetime, timedelta
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from ..repositories.repository_factory import get_repository
import time

class PredictService:
    def __init__(self):
        self.repo = get_repository()
        self.model = None

    def treinar(self):
        print("🔍 Iniciando treinamento do modelo de previsão...")

    def prever(self):
        if not self.model:
            raise ValueError("O modelo ainda não foi treinado. Por favor, treine o modelo antes de realizar previsões.")

    def _registrar_alertas(self, morro_id: str):
        caixas_alerta = self.repo.listar_caixas_alerta_por_morro(morro_id)
        for caixa in caixas_alerta:
            if not self.repo.alerta_ativo_para_caixa(caixa["caixa_id"]):
                self.repo.registrar_alerta(morro_id, caixa["caixa_id"])
                print(f"🔔 Alerta registrado para a caixa '{caixa['caixa_id']}'.")

    def _desligar_alertas_se_necessario(self, morro_id: str):
        alertas_ativos = self.repo.listar_alertas_ativos(morro_id)
        agora = datetime.utcnow()
        for alerta in alertas_ativos:
            if alerta["data_inicio"] < agora - timedelta(minutes=10):
                self.repo.desligar_alerta(alerta["alerta_id"])
                print(f"🔕 Alerta desligado para a caixa '{alerta['caixa_id']}' após 10 minutos sem risco.")
