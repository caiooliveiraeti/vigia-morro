import uuid
from ..repositories.repository_factory import get_repository

class MorroService:
    def __init__(self):
        self.repo = get_repository()

    def adicionar_morro(self, nome: str, coordenadas: list):
        morro_id = str(uuid.uuid4())  # Generate a UUID for the morro_id
        if self.repo.morro_existe(morro_id):
            raise ValueError(f"Morro '{morro_id}' já cadastrado.")

        self.repo.inserir_morro(morro_id, nome, coordenadas)
        print(f"✅ Morro '{morro_id}' cadastrado com sucesso.")

    def listar_morros(self):
        morros = self.repo.listar_morros()
        if not morros:
            print("📭 Nenhum morro cadastrado.")
            return
        print(f"{'ID':<40} | {'Nome':<20} | {'Coordenadas':<30}")
        print("-" * 95)
        for morro in morros:
            coords = f"({morro['coordenadas'][0]}, {morro['coordenadas'][1]})"
            print(f"{morro['morro_id']:<40} | {morro['nome']:<20} | {coords:<30}")

    def remover_morro(self, morro_id: str):
        if not self.repo.morro_existe(morro_id):
            raise ValueError(f"Morro '{morro_id}' não encontrado.")
        self.repo.remover_morro(morro_id)
        print(f"🗑️ Morro '{morro_id}' removido com sucesso.")