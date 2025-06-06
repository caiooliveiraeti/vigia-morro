from ...core.repositories.oracle_repository import OracleRepository

# Instância única do repositório Oracle para todo o sistema
_repo_instance = OracleRepository()

def get_repository():
    return _repo_instance