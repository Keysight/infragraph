SHELL := /bin/bash

help:
	@awk -F ':|##' '/^[^\t].+:.*##/ { printf "\033[36mmake %-28s\033[0m -%s\n", $$1, $$NF }' $(MAKEFILE_LIST) | sort

.PHONY: generate
generate: ## generate artifacts using OpenApiArt
	pip install -r requirements.txt
	python3 generate.py

.PHONY: package
package: generate ## create sdist/wheel packages from OpenAPIArt generated artifacts
	rm -rf dist
	python3 -m build
	tar tvzf dist/infragraph*.tar.gz
	python3 -m zipfile --list dist/infragraph*.whl

.PHONY: install
install: package ## pip install infragraph package
	pip install dist/infragraph*.whl --force-reinstall