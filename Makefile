SHELL := /bin/bash

VENV_DIR  := .venv
PYTHON    := $(if $(wildcard $(VENV_DIR)/bin/python3),$(abspath $(VENV_DIR)/bin/python3),python3)
PIP       := $(if $(wildcard $(VENV_DIR)/bin/pip),$(abspath $(VENV_DIR)/bin/pip),pip)
PYTEST    := $(if $(wildcard $(VENV_DIR)/bin/pytest),$(abspath $(VENV_DIR)/bin/pytest),pytest)
JUPYTEXT  := $(if $(wildcard $(VENV_DIR)/bin/jupytext),$(abspath $(VENV_DIR)/bin/jupytext),jupytext)

help:
	@awk -F ':|##' '/^[^\t].+:.*##/ { printf "\033[36mmake %-28s\033[0m -%s\n", $$1, $$NF }' $(MAKEFILE_LIST) | sort

.PHONY: venv
venv:
	rm -rf .venv || true
	python3 -m venv .venv

.PHONY: clean
clean: ## install dependencies into the active environment
	$(PIP) install --upgrade pip && $(PIP) install --progress-bar on -r requirements.txt
	rm -f src/infragraph/visualizer/frontend/js/vis-network.min.js
	wget --no-check-certificate https://unpkg.com/vis-network@9.1.2/standalone/umd/vis-network.min.js -O src/infragraph/visualizer/frontend/js/vis-network.min.js

.PHONY: generate
generate: ## generate artifacts using OpenApiArt
	$(PYTHON) generate.py
	cp -f artifacts/infragraph/*.py src/infragraph/
	cp -f artifacts/infragraph.proto src/infragraph/
	rm -rf src/docs || true
	mkdir src/docs
	cp -f artifacts/*.* src/docs

.PHONY: test
test: ## run unit tests on the src/infragraph files
	$(PIP) uninstall -y infragraph && \
	$(MAKE) pre-test-notebook && \
	$(PYTEST) -s

.PHONY: package
package: generate ## create sdist/wheel packages from OpenAPIArt generated artifacts
	rm -rf dist || true
	$(PYTHON) -m build
	tar tvzf dist/infragraph*.tar.gz
	$(PYTHON) -m zipfile --list dist/infragraph*.whl

.PHONY: install
install: package ## pip install infragraph package
	$(PIP) install dist/infragraph*.whl --force-reinstall

.PHONY: deploy
PYPI_TOKEN=__invalid_token__
deploy: ## deploy packages to pypi.org
	$(PYTHON) -m twine upload -u __token__ -p $(PYPI_TOKEN) dist/*

.PHONY: openapi-html
openapi-html: ## generate OpenAPI HTML from artifacts/openapi.yaml using redocly
	npx @redocly/cli build-docs artifacts/openapi.yaml -o docs/src/openapi.html

.PHONY: docs
docs: openapi-html ## generate local documentation to docs/site
	$(PYTHON) docs/generate_yaml.py && \
	$(PYTHON) -m mkdocs build --config-file docs/mkdocs.yml --site-dir site

.PHONY: yaml
yaml: ## generate yaml contents for docs
	$(PYTHON) docs/generate_yaml.py

.PHONY: pre-test-notebook
pre-test-notebook:
	rm -rf src/tests/test_notebooks
	$(JUPYTEXT) --to notebook src/infragraph/notebooks/*.py
	cd src && $(PYTHON) notebook_to_test_script.py
	rm -rf src/infragraph/notebooks/*.ipynb
