SHELL := /bin/bash

CONTAINER_NAME = abatilo/bitly
FORMATTER_NAME = abatilo/black
LINTER_NAME = abatilo/pylint
TESTER_NAME = abatilo/pytest

.PHONY: help
help: ## View help information
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: build_formatter
build_formatter: ## Builds the container to run formatting commands in
	docker build \
		-t $(FORMATTER_NAME) \
		-f ./ci/black/Dockerfile \
		.

.PHONY: format
format: build_formatter ## Formats the code to the `black` standard
	docker run \
		--mount type=bind,src=`pwd`,dst=/src \
		--workdir /src \
		-it $(FORMATTER_NAME) \
		/src/bitly \
		/src/tests

.PHONY: build_linter
build_linter: ## Builds the container to run linting commands in
	docker build \
		-t $(LINTER_NAME) \
		-f ./ci/pylint/Dockerfile \
		.

.PHONY: lint
lint: build_linter ## Runs `pylint`
	docker run \
		--mount type=bind,src=`pwd`,dst=/src \
		--workdir /src \
		-it $(LINTER_NAME) \
		/src/bitly \
		/src/tests

.PHONY: build_tester
build_tester: ## Builds the container to run tests in
	docker build \
		-t $(TESTER_NAME) \
		-f ./ci/pytest/Dockerfile \
		.

.PHONY: test
test: build_tester ## Runs `pytest`
	docker run \
		--mount type=bind,src=`pwd`,dst=/src \
		--workdir /src \
		-it $(TESTER_NAME) \
		--cov=/src/bitly --cov-branch --cov-fail-under=100 \
		/src/tests/

.PHONY: html_coverage
html_coverage: build_tester ## Runs `pytest` and writes out a coverage report in html
	docker run \
		--mount type=bind,src=`pwd`,dst=/src \
		--workdir /src \
		-it $(TESTER_NAME) \
		--cov=/src/bitly --cov-branch --cov-report=html \
		/src/tests/


.PHONY: check
check: format lint test ## Runs code quality checks

.PHONY: build
build: ## Build the final container for running this application
	docker build -t $(CONTAINER_NAME) .

.PHONY: run
run: build ## Run this application locally, within a container
	docker run -it -p8000:8000 $(CONTAINER_NAME)
