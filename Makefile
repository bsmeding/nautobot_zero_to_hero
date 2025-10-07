SHELL := /bin/bash

# Prerequisites:
# - make: sudo apt install -y make (Ubuntu/Debian/WSL)
# - python3.12-venv: sudo apt install -y python3.12-venv (Ubuntu/Debian/WSL)
# See scripts/README.md for detailed installation instructions

# Virtualenv location
VENV ?= .venv
PYTHON ?= python3
PIP := $(VENV)/bin/pip

.PHONY: help venv install freeze clean

help:
	@echo "Available targets:"
	@echo "  make venv     - create virtualenv at $(VENV)"
	@echo "  make install  - create venv and install demo dependencies"
	@echo "  make freeze   - write locked dependencies to scripts/requirements.txt"
	@echo "  make clean    - remove virtualenv"
	@echo ""
	@echo "After running 'make install':"
	@echo "  - If you have auto-activation (direnv/autoenv): venv activates automatically"
	@echo "  - Otherwise, manually activate with: source $(VENV)/bin/activate"

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel

# Minimal deps to run the demo scripts in scripts/*.py
install: venv
	$(PIP) install \
		pyeapi \
		requests \
		jinja2
	@echo ""
	@echo "✅ Virtual environment created and dependencies installed!"
	@echo ""
	@echo "⚠️  Don't forget to activate it with:"
	@echo "    source $(VENV)/bin/activate"

freeze:
	@mkdir -p scripts
	$(PIP) freeze > scripts/requirements.txt
	@echo "Wrote scripts/requirements.txt"

clean:
	rm -rf $(VENV)
	@echo "Removed $(VENV)"


