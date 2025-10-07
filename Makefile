SHELL := /bin/bash

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
	@echo "\nActivate with: source $(VENV)/bin/activate"

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel

# Minimal deps to run the demo scripts in scripts/*.py
install: venv
	$(PIP) install \
		pyeapi \
		requests \
		jinja2

freeze:
	@mkdir -p scripts
	$(PIP) freeze > scripts/requirements.txt
	@echo "Wrote scripts/requirements.txt"

clean:
	rm -rf $(VENV)
	@echo "Removed $(VENV)"


