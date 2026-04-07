.PHONY: setup clean secrets

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

setup: $(VENV) secrets
	@echo ""
	@echo "✓ Setup complete. Activate the venv:"
	@echo "  source $(VENV)/bin/activate"
	@echo ""
	@echo "Then run:"
	@echo "  pr-review https://bitbucket.org/workspace/repo/pull-requests/42"

$(VENV):
	python3.10 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .

secrets:
	@if [ ! -f config/.secrets.toml ]; then \
		cp config/.secrets.toml.example config/.secrets.toml; \
		echo ""; \
		echo "Created config/.secrets.toml from template."; \
		echo "→ Edit it and add your Bitbucket App Password."; \
		echo ""; \
	fi

clean:
	rm -rf $(VENV) *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
