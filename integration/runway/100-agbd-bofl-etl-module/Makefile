# This makefile is used to execute the same functionality against a module
# that is executed using the gitlab build pipelines.
#
# The following tasks are supported by the makefile
#
# Integration Testing Functionality
#
#   The test-suite tasks use the configurations defined in the integration directory to deploy the module
#   to AWS for running integration tests.
#
#   The test-suite only deploys one integration test namespace at a time to AWS. The default test namespace
#   used is "test1". If the "test2" namespace is desired, the TEST_ENV=test2 env variable can be set to deploy,
#   test, and destroy the test2 integration test. Currently, the gitlab pipelines only support test1 and test2
#   namespaces for integration testing. Additional test namespaces can be added to the integration directory
#   for local use but they will not run on gitlab.
#
#   The test-suite tasks use the runtests_local.sh script located at
#   https://gitlab-tools.swacorp.com/swa-common/ccp/docker/module-test-suite/-/blob/master/scripts/runtests_local.sh
#
#   Variables that can be overridden in runtests_local.sh by exporting these environment variables
#      LINUX_TEST_USER - If set to any value, this will enable --network=host on docker runs
#      AWS_DEFAULT_REGION - If not set, "us-east-1" is used by default
#      TO_BE_REPLACED_NS - Used to override the networking-tier-namespace value used when testing use of a vpc
#                          deployed to a different namespace from the one used when deploying this module
#      TEST_ENV - The test namespace to run for integration tests. If not set, "test1" is used
#

CI := $(if $(CI),yes,no)
ROOT_DIR := $(PWD)
MODULENAME := $(shell basename $(PWD))
SHELL := /bin/bash

ifeq ($(CI), yes)
	POETRY_OPTS = "-v"
endif

.EXPORT_ALL_VARIABLES:
	MODULENAME=$(MODULENAME)

.PHONY: all clean clean-all dependency-check help \
	setup setup-local test-coverage test-suite test-suite-deploy test-suite-destroy \
	test-suite-run test-suite-setup variables veracode local-deploy run-glue-jupyter-lab \


help: ## show this message
	@awk \
		'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' \
		$(MAKEFILE_LIST)

all: test-coverage test-suite  # run everything

clean: ## cleanup local files
	rm -rf \
		./.coveragerc \
		./integration/gitlab \
		./integration/jenkins \
		./integration/local \
		./integration/pip_cache \
		./integration/runtests_local.sh \
		./integration/runtests.sh \
		./integration/runway \
		./integration/set_py_version.sh \
		./integration/update_integration.py \
		./test-coverage.sh

clean-all: clean ## **[USE WITH CAUTION]** deletes all local docker images, networks, containers, and caches
	docker system prune --all --force

dependency-check: ## run OWASP dependency check on module
	@echo "Starting dependency-check task for $(MODULENAME)..."
	@docker compose up \
		--build \
		--force-recreate \
		--pull always \
		dependency-check;
	@echo "Finished dependency-check task for $(MODULENAME)"
	@echo ""

fix-black: ## automatically fix all black errors
	@poetry run black .

fix-imports: ## automatically fix all import sorting errors
	@poetry run ruff check . --fix-only --fixable I001

fix-ruff: ## automatically fix everything ruff can fix (implies fix-imports)
	@poetry run ruff check . --fix-only

lint:  lint-black lint-ruff lint-pyright ## run all linters

lint-black: ## run black
	@echo "Running black... If this fails, run 'make fix-black' to resolve."
	@poetry run black . --check --color --diff
	@echo ""

lint-pyright: ## run pyright
	@echo "Running pyright..."
	@npm exec -- pyright --venvpath ./
	@echo ""

lint-ruff: ## run ruff
	@echo "Running ruff... If this fails, run 'make fix-ruff' to resolve some error automatically, others require manual action."
	@poetry run ruff check .
	@echo ""

run-pre-commit: ## run pre-commit for all files
	@if [[ -f .pre-commit-config.yaml ]]; then \
		poetry run pre-commit run  $(PRE_COMMIT_OPTS) \
			--all-files \
			--color always; \
	else \
		echo "pre-commit not configured for this project; add a .pre-commit-config.yaml file to configure it."; \
	fi

setup: setup-npm setup-poetry setup-pre-commit ## setup development environment

setup-npm: ## install node dependencies with npm
	@if [[ -f package.json ]]; then \
		npm ci; \
	fi

setup-poetry: ## setup python virtual environment
	@if [[ -f poetry.lock ]]; then \
		if [[ -d .venv ]]; then \
			poetry run python -m pip --version >/dev/null 2>&1 || rm -rf ./.venv/* ./.venv/.*; \
			poetry lock --check; \
			poetry install $(POETRY_OPTS) --sync; \
		else \
			poetry lock --check; \
			poetry install $(POETRY_OPTS) --sync; \
		fi \
	fi

setup-pre-commit: ## install pre-commit git hooks
	@if [[ -f .pre-commit-config.yaml ]]; then \
		poetry run pre-commit install; \
	fi

spellcheck: ## run cspell
	@echo "Running cSpell to checking spelling...";
	@if [[ -f ./.vscode/cspell.json ]]; then	\
		npm exec --no -- cspell lint . \
			--color \
			--config .vscode/cspell.json \
			--dot \
			--gitignore \
			--must-find-files \
			--no-progress \
			--relative \
			--show-context; \
	else \
		echo "cspell not configured for this project; add a .vscode/cspell.json file to configure it."; \
	fi

test-coverage: ## run unit tests and coverage on module
	@echo "projects that us poetry should define a 'test' target in a local Make file which should be used over this target."
	@echo "Starting test-coverage task for $(MODULENAME)";
	@docker compose up \
		--build \
		--force-recreate \
		--pull always \
		test-coverage;
	@echo "Finished test-coverage task for $(MODULENAME)"
	@echo ""

test-suite: ## deploy module infrastructure in AWS for integration test suite, run integration tests, destroy infra
	@echo "Starting test-suite task for $(MODULENAME)"
	@docker compose up \
		--build \
		--force-recreate \
		--pull always \
		test-suite;
	@echo "Finished test-suite task for $(MODULENAME)"
	@echo ""

test-suite-deploy: ## deploy module infrastructure to AWS for integration test suite
	@echo "Starting test-suite-deploy task for $(MODULENAME)"
	@docker compose up \
		--build \
		--force-recreate \
		--pull always \
		test-suite-deploy;
	@echo "Finished test-suite-deploy task for $(MODULENAME)"
	@echo ""

test-suite-destroy: ## destroy module infrastructure in AWS for integration test suite
	@echo "Starting test-suite-destroy task for $(MODULENAME)"
	@docker compose up \
		--build \
		--force-recreate \
		--pull always \
		test-suite-destroy;
	@echo "Finished test-suite-destroy task for $(MODULENAME)"
	@echo ""

test-suite-run: ## run the integration tests against deployed infrastructure in AWS
	@echo "Starting test-suite-run task for $(MODULENAME)"
	@docker compose up \
		--build \
		--force-recreate \
		--pull always \
		test-suite-run;
	@echo "Finished test-suite-run task for $(MODULENAME)"
	@echo ""

veracode: ## initiates veracode check on module
	@echo "Starting veracode task for $(MODULENAME)"
	@docker compose up \
		--build \
		--force-recreate \
		--pull always \
		veracode;
	@echo "Finished veracode task for $(MODULENAME)"
	@echo ""

# Custom Make Commands - Anything not originally from
# the local-setup.sh command which we removed for runway 3 updates

local-deploy: ## same as test-suite-deploy but does not pull docker image every time
	@echo "Starting test-suite-deploy task for $(MODULENAME)"
	@docker compose run \
		--rm \
		--remove-orphans \
		test-suite-deploy;
	@echo "Finished test-suite-deploy task for $(MODULENAME)"
	@echo "";

sync-files-to-local-deploy: ## updates local deploy with code from local for quick testing on aws
	@read -p "Enter Your xID:" xID; \
	poetry build; \
	aws s3 sync ./src/ \
	s3://decp-us-east-1-$${xID}-local-test1-agbd-analytics-etl/decp/commodity/agbd-analytics-etl/src/ \
	&& \
	aws s3 cp ./dist/src-0.0.1-py3-none-any.whl \
	s3://decp-us-east-1-$${xID}-local-test1-agbd-analytics-etl/decp/commodity/agbd-analytics-etl/src/

local-pytest-poetry-shell: ## runs pytest inside of poetry shell, the -s shows output even  w/ passing tests
	pytest -s;

local-pytest-outside-poetry-shell: ## runs pytest outside poetry shell in root dir
	poetry run pytest -s;

# to check ports on local: lsof -i -P -n | grep -E '4040|8888|18080|8998|4041'
# if you get an error for running port, kill process running it with 'kill -9 <process id>, take care to ensure correct ID.
run-glue-jupyter-lab: ## runs glue interactive in docker container with spark_ui, spark_history, jupyter, and livy_server
	@docker compose run \
		--service-ports \
		--rm \
		--remove-orphans \
		glue_jupyter_lab_agbd_analytics;

exec-jupyter-container: ## with jupyter lab docker running, execute in to docker
	@docker exec -it \
	$$(docker container ls  | grep 'glue_jupyter_lab_agbd_analytics' | awk '{print $$1}') \
	/bin/bash

run-unit-pytest-container: ## runs unit tests in glue docker
	@docker exec \
		$$(docker container ls  | grep 'glue_jupyter_lab_agbd_analytics' | awk '{print $$1}') \
		bash -c "python3 -m pytest ./test/unit_test/$${unittest:-test_upload_to_s3.py}"

# defaults to test_sample_code.py,
# to specify specific test define unittest bf make ex. -> 'unittest=* make run-pytest-container'
# pytest -rP -s ./test/integration_test/test_table_processors.py -k test_transformation_of_rcvry_evnt_air
run-int-pytest-container: ## runs integration tests in glue docker
	@docker exec \
		$$(docker container ls  | grep 'glue_jupyter_lab_agbd_analytics' | awk '{print $$1}') \
		bash -c "python3 -m pytest ./test/integration_test/$${unittest:-test_sample_code.py}"
