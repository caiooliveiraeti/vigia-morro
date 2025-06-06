import os
import requests
import time
from ..repositories.repository_factory import get_repository

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")  # Obtém a API key da variável de ambiente
        self.base_url = os.getenv("OPENWEATHER_API_URL")  # URL do serviço
        self.repo = get_repository()

    def consultar_e_gravar(self, morro_id: str, latitude: float, longitude: float):
        print(f"🌦️ Consultando dados meteorológicos para o Morro '{morro_id}' usando a API One Call 3.0...")
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
            "lang": "pt",
            "exclude": "minutely,hourly,daily,alerts"  # Apenas dados do campo 'current'
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Extrair dados do campo 'current'
            current = data.get("current", {})
            temperatura = current.get("temp")
            umidade = current.get("humidity")
            descricao = current.get("weather", [{}])[0].get("description", "N/A")
            rain = current.get("rain", 0)
            chovendo = 1 if rain != "0" else 0  # Verifica se há chuva nos dados

            if temperatura is None or umidade is None:
                raise ValueError("Dados incompletos retornados pela API.")

            # Gravar no banco de dados
            self.repo.salvar_dados_meteorologicos(morro_id, temperatura, umidade, descricao, chovendo)
            print(f"✅ Dados meteorológicos gravados: {temperatura}°C, {umidade}%, {descricao}, Chovendo: {'Sim' if chovendo else 'Não'}.")
        except requests.RequestException as e:
            print(f"⚠️ Erro ao consultar a API de meteorologia: {e}")
        except ValueError as e:
            print(f"⚠️ Erro nos dados retornados pela API: {e}")

    def iniciar_crawler(self):
        print("📡 Iniciando crawler de meteorologia para todos os morros...")
        try:
            while True:
                morros = self.repo.listar_morros()
                if not morros:
                    print("⚠️ Nenhum morro cadastrado para monitorar.")
                    break

                for morro in morros:
                    morro_id = morro["morro_id"]
                    latitude, longitude = morro["coordenadas"]
                    self.consultar_e_gravar(morro_id, latitude, longitude)

                print("Aguardando 15 segs antes da próxima consulta...")
                time.sleep(15)
        except KeyboardInterrupt:
            print("\n👋 Crawler encerrado pelo usuário.")
