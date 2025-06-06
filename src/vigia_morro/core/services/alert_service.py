from ..repositories.repository_factory import get_repository
import time
import serial

class AlertService:
    def __init__(self):
        self.repo = get_repository()

    def monitorar_alertas(self, serial_url: str, morro_id: str):
        print(f"📡 Monitorando alertas para o Morro '{morro_id}' na URL {serial_url}...")
        try:
            with serial.serial_for_url(serial_url, baudrate=115200) as ser:
                while True:
                    alertas_ativos = self.repo.listar_alertas_ativos(morro_id)
                    if alertas_ativos:
                        ser.write(b"1\n")  # Enviar comando para ligar a sirene
                        print("✅ Sirene ligada devido a alertas ativos.")
                    else:
                        ser.write(b"0\n")  # Enviar comando para desligar a sirene
                        print("✅ Sirene desligada, nenhum alerta ativo.")
                    time.sleep(1)  # Esperar 1 segundo antes de verificar novamente
        except Exception as e:
            raise RuntimeError(f"Erro ao monitorar alertas: {e}")
