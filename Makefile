# Spec 08 - reproducibility entrypoints. Spec 09 - dashboard targets.
#
# Notes:
# - Legacy scripts 01..07 use paths relative to src/, so make run executes them
#   from that directory instead of editing legacy code.
# - make report validates Spec 07 artifacts; it does not reimplement the report.
# - make dashboard-build derives static JSON in docs/data/ from validated
#   outputs only; make dashboard serves docs/ locally (GitHub Pages serves the
#   same folder in production).

WINDOWS_VENV_PYTHON := .venv/Scripts/python.exe
POSIX_VENV_PYTHON := .venv/bin/python

ifneq ($(wildcard $(WINDOWS_VENV_PYTHON)),)
PYTHON ?= $(WINDOWS_VENV_PYTHON)
else ifneq ($(wildcard $(POSIX_VENV_PYTHON)),)
PYTHON ?= $(POSIX_VENV_PYTHON)
else
PYTHON ?= python
endif

export PYTHONPATH := src

.PHONY: install lint test run audit report all dashboard dashboard-build dashboard-test

install:
	$(PYTHON) -m pip install -r requirements.txt pytest ruff

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest tests/

run:
	cd src && $(PYTHON) 01_etl.py
	cd src && $(PYTHON) 02_estoque_projetado.py
	cd src && $(PYTHON) 03_analise_vendas.py
	cd src && $(PYTHON) 04_analise_estoque.py
	cd src && $(PYTHON) 05_precificacao.py
	cd src && $(PYTHON) 06_projecao_compras.py
	cd src && $(PYTHON) 07_recomendacoes.py

audit:
	$(PYTHON) src/io.py
	$(PYTHON) src/02_quality_audit.py
	$(PYTHON) src/inventory_reconciliation.py
	$(PYTHON) src/analysis/sales_analysis.py
	$(PYTHON) src/analysis/assortment_analysis.py
	$(PYTHON) src/analysis/pricing_analysis.py
	$(PYTHON) src/analysis/projection_analysis.py
	$(PYTHON) src/analysis/recommendation_triage.py

report:
	$(PYTHON) -m pytest tests/test_hypothesis_report.py tests/test_outputs.py

dashboard-build:
	$(PYTHON) src/dashboard_build.py

dashboard:
	$(PYTHON) -m http.server 8000 --directory docs

dashboard-test:
	$(PYTHON) -m pytest tests/test_dashboard.py

all: lint run audit report test
