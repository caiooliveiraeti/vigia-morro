import uuid
from datetime import datetime
from ..repositories.repository_factory import get_repository
import csv
import json

class CaixaService:
    def __init__(self):
        self.repo = get_repository()

    def adicionar_caixa(self, tipo: str, nome_versao: str, morro_id: str, codigo_patrimonio: str):
        if self.repo.caixa_codigo_existe(codigo_patrimonio):
            raise ValueError(f"Caixa com código de patrimônio '{codigo_patrimonio}' já cadastrada.")

        if not self.repo.morro_existe(morro_id):
            raise ValueError(f"Morro '{morro_id}' não cadastrado.")

        versao_id = self.repo.get_versao_id_by_nome(nome_versao)
        if not versao_id:
            raise ValueError(f"Versão '{nome_versao}' não cadastrada.")

        caixa_id = str(uuid.uuid4())  # Generate a UUID for the caixa_id
        self.repo.inserir_caixa(caixa_id, tipo, versao_id, morro_id, [0, 0], codigo_patrimonio)
        print(f"✅ Caixa com código de patrimônio '{codigo_patrimonio}' adicionada com sucesso ao morro '{morro_id}'.")

    def listar_caixas(self):
        caixas = self.repo.listar_caixas()
        if not caixas:
            print("📭 Nenhuma caixa cadastrada.")
            return
        print(f"{'Código Patrimônio':<20} | {'Tipo':<10} | {'Morro (Nome)':<30} | {'Coordenadas':<30} | {'Status':<10} | {'Sensores':<30}")
        print("-" * 150)
        for caixa in caixas:
            coords = f"({caixa['coordenadas'][0]}, {caixa['coordenadas'][1]})"
            status = "Ativo" if caixa.get("ativo", False) else "Inativo"
            print(f"{caixa['codigo_patrimonio']:<20} | {caixa['tipo']:<10} | {caixa['morro_nome']:<30} | {coords:<30} | {status:<10} | {caixa['sensores']:<30}")

    def remover_caixa(self, codigo_patrimonio: str):
        if not self.repo.caixa_codigo_existe(codigo_patrimonio):
            raise ValueError(f"Caixa com código de patrimônio '{codigo_patrimonio}' não encontrada.")
        caixa_id = self.repo.get_caixa_id_by_codigo(codigo_patrimonio)
        self.repo.remover_caixa(caixa_id)
        print(f"🗑️ Caixa com código de patrimônio '{codigo_patrimonio}' removida com sucesso.")

    def cadastrar_leitura(self, codigo_patrimonio: str, nome_metrica: str, valor: float, timestamp: str):
        if not self.repo.caixa_codigo_existe(codigo_patrimonio):
            raise ValueError(f"Caixa com código de patrimônio '{codigo_patrimonio}' não encontrada.")

        # Use current UTC time if timestamp is empty
        if not timestamp:
            timestamp_utc = datetime.utcnow()
        else:
            try:
                timestamp_utc = datetime.fromisoformat(timestamp)
            except ValueError:
                raise ValueError("O timestamp deve estar no formato ISO 8601 (YYYY-MM-DDTHH:MM:SS).")

        tipo_metrica_id = self.repo.get_tipo_metrica_id_by_nome(nome_metrica)
        if not tipo_metrica_id:
            raise ValueError(f"Métrica '{nome_metrica}' não encontrada.")

        caixa_id = self.repo.get_caixa_id_by_codigo(codigo_patrimonio)
        self.repo.salvar_leitura({
            "caixa_id": caixa_id,
            "tipo_metrica_id": tipo_metrica_id,
            "valor": valor,
            "timestamp": timestamp_utc
        })
        print(f"✅ Métrica '{nome_metrica}' registrada para a caixa '{codigo_patrimonio}' com valor '{valor}' no timestamp '{timestamp_utc}'.")

    def importar_leituras_csv(self, csv_file_path: str):
        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    timestamp = row.get("timestamp")
                    codigo_patrimonio = row.get("codigo_patrimonio")
                    tipo_metrica = row.get("tipo_metrica")
                    medida = row.get("medida")

                    # Validate required fields
                    if not codigo_patrimonio or not tipo_metrica or not medida:
                        print(f"⚠️ Linha inválida no arquivo CSV: {row}")
                        continue

                    # Use current UTC time if timestamp is missing
                    if not timestamp:
                        timestamp_utc = datetime.utcnow()
                    else:
                        try:
                            timestamp_utc = datetime.fromisoformat(timestamp)
                        except ValueError:
                            print(f"⚠️ Timestamp inválido: {timestamp}")
                            continue

                    # Convert medida to float
                    try:
                        medida = float(medida)
                    except ValueError:
                        print(f"⚠️ Medida inválida: {medida}")
                        continue

                    # Register the metric
                    try:
                        self.cadastrar_leitura(codigo_patrimonio, tipo_metrica, medida, timestamp_utc.isoformat())
                    except Exception as e:
                        print(f"⚠️ Erro ao cadastrar leitura: {e}")
                        continue

                print("✅ Importação de leituras concluída com sucesso.")
        except FileNotFoundError:
            print(f"❌ Arquivo CSV não encontrado: {csv_file_path}")
        except Exception as e:
            print(f"❌ Erro ao importar leituras: {e}")

    def exportar_medicoes_morro(self, morro_id: str, output_csv_path: str):
        if not self.repo.morro_existe(morro_id):
            raise ValueError(f"Morro '{morro_id}' não encontrado.")

        if not self.repo.caixa_existe(morro_id):
            raise ValueError(f"Não há caixas cadastradas para o morro '{morro_id}'.")

        leituras = self.repo.listar_leituras_por_morro(morro_id)
        if not leituras:
            raise ValueError(f"Não há medições registradas para o morro '{morro_id}'.")

        with open(output_csv_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["caixa_id", "codigo_patrimonio", "tipo_metrica", "valor", "timestamp"])
            for leitura in leituras:
                writer.writerow([
                    leitura["caixa_id"],
                    leitura["codigo_patrimonio"],
                    leitura["tipo_metrica"],  # Include metric type name
                    leitura["valor"],
                    leitura["timestamp"]
                ])

        print(f"✅ Medições do morro '{morro_id}' exportadas com sucesso para '{output_csv_path}'.")

    def _exportar_medicoes(self, morro_id: str, output_path: str, formato: str):
        if not self.repo.morro_existe(morro_id):
            raise ValueError(f"Morro '{morro_id}' não encontrado.")

        leituras = self.repo.listar_leituras_por_morro(morro_id)
        if not leituras:
            raise ValueError(f"Não há medições registradas para o morro '{morro_id}'.")

        if formato == "csv":
            with open(output_path, mode='w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["id_morro", "nome_morro", "id_caixa", "nome_caixa", "tipo_metrica", "valor", "timestamp"])
                for leitura in leituras:
                    writer.writerow([
                        leitura["morro_id"],
                        leitura["nome_morro"],
                        leitura["caixa_id"],
                        leitura["nome_caixa"],
                        leitura["tipo_metrica"],
                        leitura["valor"],
                        leitura["timestamp"]
                    ])
        elif formato == "json":
            with open(output_path, mode='w', encoding='utf-8') as file:
                json.dump(leituras, file, indent=4, default=str)
        else:
            raise ValueError("Formato de exportação inválido. Use 'csv' ou 'json'.")

        print(f"✅ Medições do morro '{morro_id}' exportadas com sucesso para '{output_path}'.")

    def exportar_medicoes_morro_csv(self, morro_id: str, output_csv_path: str):
        self._exportar_medicoes(morro_id, output_csv_path, "csv")

    def exportar_medicoes_morro_json(self, morro_id: str, output_json_path: str):
        self._exportar_medicoes(morro_id, output_json_path, "json")

    def conectar_caixas(self, serial_url: str):
        print("📡 Conectando à serial...")
        try:
            import serial
            with serial.serial_for_url(serial_url, baudrate=115200) as ser:
                print("✅ Conexão estabelecida. Pressione Ctrl+C para encerrar.")
                while True:
                    try:
                        linha = ser.readline().decode("utf-8").strip()
                        if linha.startswith("DATA:"):
                            dados = {
                                item.split("=")[0]: item.split("=")[1]
                                for item in linha.replace("DATA:", "").split(",")
                            }
                            mid = dados.get("MID")
                            cid = dados.get("CID")

                            if not mid or not cid:
                                print("⚠️ Dados inválidos: MID ou cid ausentes.")
                                continue

                            if not self.repo.morro_existe(mid):
                                print(f"⚠️ Morro com ID '{mid}' não encontrado.")
                                continue

                            if not self.repo.caixa_codigo_existe(cid):
                                print(f"⚠️ Caixa com código de patrimônio '{cid}' não encontrada.")
                                continue

                            if "H" in dados:
                                valor_umidade = float(dados["H"])
                                self.cadastrar_leitura(cid, "Umidade", valor_umidade, datetime.utcnow().isoformat())

                            if "T" in dados:
                                valor_temperatura = float(dados["T"])
                                self.cadastrar_leitura(cid, "Temperatura", valor_temperatura, datetime.utcnow().isoformat())
                    except KeyboardInterrupt:
                        print("\n👋 Conexão encerrada pelo usuário.")
                        break
        except Exception as e:
            raise RuntimeError(f"Erro ao conectar à serial: {e}")

    def conectar_alertbox(self, serial_url: str, comando: str):
        print(f"📡 Enviando comando para AlertBox na URL {serial_url}...")
        try:
            import serial
            with serial.serial_for_url(serial_url, baudrate=115200) as ser:
                if comando == "LIGAR":
                    ser.write(b"1\n")
                    print("✅ Comando enviado: Ligar Sirene.")
                elif comando == "DESLIGAR":
                    ser.write(b"0\n")
                    print("✅ Comando enviado: Desligar Sirene.")
        except Exception as e:
            raise RuntimeError(f"Erro ao conectar ao AlertBox: {e}")