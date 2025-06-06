# Variáveis
PYTHON=python3
VENV_DIR=.venv
ACTIVATE=source $(VENV_DIR)/bin/activate
REQUIREMENTS=requirements.txt

# Alvo padrão para rodar o projeto
run: venv install
	@set -a; \
	if [ -f config/.env-local ]; then \
		. config/.env-local; \
	fi; \
	set +a; \
	$(ACTIVATE) && $(PYTHON) -m src.vigia_morro

# Alvo para criar o ambiente virtual
venv:
	$(PYTHON) -m venv $(VENV_DIR)

# Alvo para instalar dependências (somente se requirements.txt mudou)
install: $(VENV_DIR)/.requirements-installed

$(VENV_DIR)/.requirements-installed: requirements.txt
	@echo "Instalando dependências do $(REQUIREMENTS)..."
	$(ACTIVATE) && pip install -r $(REQUIREMENTS)
	@touch $(VENV_DIR)/.requirements-installed

# Alvo para remover o ambiente virtual
clean-venv:
	@echo "Removendo o ambiente virtual..."
	rm -rf $(VENV_DIR)

# Alvo para reiniciar o ambiente virtual
rebuild: clean-venv venv install
	@echo "Ambiente virtual recriado com sucesso."

