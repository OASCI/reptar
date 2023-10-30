SHELL := /usr/bin/env bash
PYTHON_VERSION := 3.11
PYTHON_VERSION_CONDENSED := 311
PACKAGE_NAME := reptar
REPO_PATH := $(shell git rev-parse --show-toplevel)
CONDA_NAME := $(PACKAGE_NAME)-dev
CONDA_BASE_PATH = $(shell conda info --base)
CONDA_PATH := $(CONDA_BASE_PATH)/envs/$(CONDA_NAME)
CONDA := conda run -n $(CONDA_NAME)
DOCS_URL := https://reptar.oasci.org

###   ENVIRONMENT   ###

.PHONY: conda-setup
conda-setup:
	conda remove -y --name $(CONDA_NAME) --all
	conda create -y -n $(CONDA_NAME) python=$(PYTHON_VERSION)
	conda install -y conda-lock -n $(CONDA_NAME)
	conda install -y -c conda-forge poetry pre-commit tomli tomli-w -n $(CONDA_NAME)
	$(CONDA) pip install conda_poetry_liaison

.PHONY: write-conda-lock
write-conda-lock:
	- rm $(REPO_PATH)/conda-lock.yml
	$(CONDA) conda config --env --add channels conda-forge/label/libint_dev
	$(CONDA) conda env export --from-history | grep -v "^prefix" > environment.yml
	$(CONDA) conda-lock -f environment.yml -p linux-64 -p osx-64
	$(CONDA) cpl-deps $(REPO_PATH)/pyproject.toml --env_path $(CONDA_PATH)
	$(CONDA) cpl-clean $(CONDA_PATH)

.PHONY: from-conda-lock
from-conda-lock:
	$(CONDA) conda-lock install -n $(CONDA_NAME) $(REPO_PATH)/conda-lock.yml
	$(CONDA) pip install conda_poetry_liaison
	$(CONDA) cpl-clean $(CONDA_PATH)

.PHONY: pre-commit-install
pre-commit-install:
	$(CONDA) pre-commit install

# Reads `pyproject.toml`, solves environment, then writes lock file.
.PHONY: poetry-lock
poetry-lock:
	$(CONDA) poetry lock --no-interaction
	$(CONDA) poetry export --without-hashes > requirements.txt

.PHONY: install
install:
	$(CONDA) poetry install --no-interaction

.PHONY: refresh
refresh: conda-setup from-conda-lock pre-commit-install install formatting validate



.PHONY: validate
validate:
	- $(CONDA) pre-commit run --all-files

.PHONY: formatting
formatting:
	- $(CONDA) pyupgrade --exit-zero-even-if-changed --py311-plus **/*.py
	- $(CONDA) isort --settings-path pyproject.toml ./
	- $(CONDA) black --config pyproject.toml ./




#* Linting
.PHONY: test
test:
	$(CONDA) pytest -c pyproject.toml --cov=$(PACKAGE_NAME) --cov-report=xml tests/

.PHONY: check-codestyle
check-codestyle:
	$(CONDA) poetry run isort --diff --check-only --settings-path pyproject.toml $(PACKAGE_NAME) tests
	$(CONDA) poetry run black --diff --check --config pyproject.toml $(PACKAGE_NAME) tests
	$(CONDA) poetry run pylint $(PACKAGE_NAME) tests

.PHONY: mypy
mypy:
	$(CONDA) poetry run mypy --config-file pyproject.toml --explicit-package-bases $(PACKAGE_NAME) tests

.PHONY: check-safety
check-safety:
	$(CONDA) poetry check
	$(CONDA) poetry run safety check --full-report
	$(CONDA) poetry run bandit -ll --recursive $(PACKAGE_NAME)

.PHONY: lint
lint: test check-codestyle mypy check-safety



#* Cleaning
.PHONY: pycache-remove
pycache-remove:
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

.PHONY: dsstore-remove
dsstore-remove:
	find . | grep -E ".DS_Store" | xargs rm -rf

.PHONY: mypycache-remove
mypycache-remove:
	find . | grep -E ".mypy_cache" | xargs rm -rf

.PHONY: ipynbcheckpoints-remove
ipynbcheckpoints-remove:
	find . | grep -E ".ipynb_checkpoints" | xargs rm -rf

.PHONY: pytestcache-remove
pytestcache-remove:
	find . | grep -E ".pytest_cache" | xargs rm -rf

.PHONY: psi-remove
psi-remove:
	find . | grep -E ".clean" | xargs rm -rf
	find . | grep -E "timer.dat" | xargs rm -rf

.PHONY: coverage-remove
coverage-remove:
	find . | grep -E ".coverage" | xargs rm -rf

.PHONY: build-remove
build-remove:
	rm -rf build/

.PHONY: cleanup
cleanup: pycache-remove dsstore-remove mypycache-remove ipynbcheckpoints-remove pytestcache-remove psi-remove coverage-remove


#* Build
.PHONY: build
build:
	$(CONDA) poetry build

#* Documentation
.PHONY: docs
docs:
	rm -rf ./docs/html/
	$(CONDA) sphinx-build -nT ./docs/source/ ./docs/html/
	touch ./docs/html/.nojekyll

.PHONY: open-docs
open-docs:
	xdg-open ./docs/html/index.html 2>/dev/null

.PHONY: update-defs
update-defs:
	$(CONDA) ./docs/convert_definitions.py

.PHONY: docs-multiversion
docs-multiversion:
	rm -rf ./docs/html/
	$(CONDA) sphinx-multiversion -nT ./docs/source/ ./docs/html/
	touch ./docs/html/.nojekyll

	# Create html redirect to main
	echo "<head>" > ./docs/html/index.html
	echo "  <meta http-equiv='refresh' content='0; URL=$(DOCS_URL)/main/index.html'>" >> ./docs/html/index.html
	echo "</head>" >> ./docs/html/index.html
