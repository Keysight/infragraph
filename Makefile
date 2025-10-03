SHELL := /bin/bash

help:
	@awk -F ':|##' '/^[^\t].+:.*##/ { printf "\033[36mmake %-28s\033[0m -%s\n", $$1, $$NF }' $(MAKEFILE_LIST) | sort


.PHONY: clean
clean: ## recreate clean virtual environment
	rm -rf .venv || true
	python3 -m venv .venv
	source .venv/bin/activate && pip install -r requirements.txt

.PHONY: generate
generate: ## generate artifacts using OpenApiArt
	source .venv/bin/activate && \
	python3 generate.py
	cp -f artifacts/infragraph/*.py src/infragraph/
	rm -rf src/docs || true
	mkdir src/docs
	cp -f artifacts/*.* src/docs

.PHONY: test
test: ## run unit tests on the src/infragraph files
	source .venv/bin/activate && \
	pip uninstall -y infragraph && \
	pytest -s

.PHONY: package
package: generate ## create sdist/wheel packages from OpenAPIArt generated artifacts
	rm -rf dist || true
	source .venv/bin/activate && \
	python3 -m build
	tar tvzf dist/infragraph*.tar.gz
	python3 -m zipfile --list dist/infragraph*.whl

.PHONY: install
install: package ## pip install infragraph package
	source .venv/bin/activate && \
	pip3 install dist/infragraph*.whl --force-reinstall

.PHONY: deploy
PYPI_TOKEN=__invalid_token__
deploy: ## deploy packages to pypi.org
	source .venv/bin/activate && \
	python3 -m twine upload -u __token__ -p $(PYPI_TOKEN) dist/*

.PHONY: docs
docs: ## generate local documentation to docs/site
	source .venv/bin/activate && \
	python3 docs/generate_yaml.py
	python3 -m mkdocs build --config-file docs/mkdocs.yml --site-dir site

.PHONY: yaml
yaml: ## generate yaml contents for docs
	source .venv/bin/activate && \
	python3 docs/generate_yaml.py
