from .core.services.caixa_service import CaixaService
from .core.services.morro_service import MorroService
from .core.services.alert_service import AlertService  # Importando o AlertService
import questionary

morro_service = MorroService()
caixa_service = CaixaService()

def executar():
    while True:
        escolha = questionary.select(
            "O que você deseja fazer?",
            choices=[
                "1. Adicionar Morro",
                "2. Listar Morros",
                "3. Remover Morro",
                "4. Adicionar Caixa",
                "5. Listar Caixas",
                "6. Remover Caixa",
                "7. Cadastrar Leitura",
                "8. Importar Leituras de CSV",
                "9. Exportar Leituras de um Morro",
                "11. Conectar SensorBox (Serial)",
                "12. Conectar AlertBox (Serial)",
                "99. Sair"
            ]
        ).ask()

        if escolha is None:  # Handle interruption gracefully
            print("\n👋 Encerrando...")
            break

        try:
            if escolha.startswith("1."):
                nome = questionary.text("Nome do morro:").ask()
                lat = float(questionary.text("Latitude:").ask())
                lon = float(questionary.text("Longitude:").ask())
                morro_service.adicionar_morro(nome, [lat, lon])

            elif escolha.startswith("2."):
                morro_service.listar_morros()

            elif escolha.startswith("3."):
                morro_id = questionary.text("ID do morro a remover:").ask()
                if not morro_service.repo.morro_existe(morro_id):
                    print(f"⚠️ Morro '{morro_id}' não encontrado.")
                    continue
                morro_service.remover_morro(morro_id)

            elif escolha.startswith("4."):
                tipo = questionary.select("Tipo da caixa:", choices=["sensor", "alerta"]).ask()
                nome_versao = questionary.text("Nome da versão da caixa:").ask()
                morro_id = questionary.text("ID do morro vinculado:").ask()
                if not morro_service.repo.morro_existe(morro_id):
                    print(f"⚠️ Morro '{morro_id}' não encontrado.")
                    continue
                codigo_patrimonio = questionary.text("Código de patrimônio da caixa:").ask()
                caixa_service.adicionar_caixa(tipo, nome_versao, morro_id, codigo_patrimonio)

            elif escolha.startswith("5."):
                caixa_service.listar_caixas()

            elif escolha.startswith("6."):
                caixa_id = questionary.text("ID da caixa a remover:").ask()
                if not caixa_service.repo.caixa_existe(caixa_id):
                    print(f"⚠️ Caixa '{caixa_id}' não encontrada.")
                    continue
                caixa_service.remover_caixa(caixa_id)

            elif escolha.startswith("7."):
                codigo_patrimonio = questionary.text("Código de patrimônio da caixa:").ask()
                if not caixa_service.repo.caixa_codigo_existe(codigo_patrimonio):
                    print(f"⚠️ Caixa com código de patrimônio '{codigo_patrimonio}' não encontrada.")
                    continue
                nome_metrica = questionary.text("Nome da métrica:").ask()
                valor = float(questionary.text("Valor medido:").ask())
                timestamp = questionary.text("Timestamp (UTC, formato ISO 8601):").ask()
                caixa_service.cadastrar_leitura(codigo_patrimonio, nome_metrica, valor, timestamp)

            elif escolha.startswith("8."):
                csv_file_path = questionary.text("Caminho do arquivo CSV:").ask()
                caixa_service.importar_leituras_csv(csv_file_path)

            elif escolha.startswith("9."):
                morro_id = questionary.text("ID do morro:").ask()
                if not morro_service.repo.morro_existe(morro_id):
                    print(f"⚠️ Morro '{morro_id}' não encontrado.")
                    continue

                formato = questionary.select(
                    "Escolha o formato de exportação:",
                    choices=["CSV", "JSON"]
                ).ask()

                output_path = questionary.text("Caminho para salvar o arquivo:").ask()

                if formato == "CSV":
                    caixa_service.exportar_medicoes_morro_csv(morro_id, output_path)
                elif formato == "JSON":
                    caixa_service.exportar_medicoes_morro_json(morro_id, output_path)

            elif escolha.startswith("11."):
                serial_url = questionary.text("Serial URL (ex: rfc2217://localhost:4400):").ask()
                if not serial_url:
                    serial_url = "rfc2217://localhost:4400"
                try:
                    caixa_service.conectar_caixas(serial_url)
                except Exception as e:
                    print(f"⚠️ Erro ao monitorar SensorBox: {e}")

            elif escolha.startswith("12."):
                morro_id = questionary.text("ID do morro:").ask()
                if not morro_service.repo.morro_existe(morro_id):
                    print(f"⚠️ Morro '{morro_id}' não encontrado.")
                    continue

                serial_url = questionary.text("Serial URL (ex: rfc2217://localhost:4401):").ask()
                if not serial_url:
                    serial_url = "rfc2217://localhost:4401"

                try:
                    alert_service = AlertService()
                    alert_service.monitorar_alertas(serial_url, morro_id)
                except Exception as e:
                    print(f"⚠️ Erro ao monitorar AlertBox: {e}")

            elif escolha.startswith("99."):
                print("👋 Encerrando...")
                break

        except Exception as e:
            print(f"⚠️ Erro: {e}")
