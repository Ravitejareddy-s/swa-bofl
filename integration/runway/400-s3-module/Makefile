GITLAB_CI := $(if $(GITLAB_CI),yes,no)
REPORTS := $(if $(REPORTS),yes,$(GITLAB_CI))
SHELL := /bin/bash

ifeq ($(REPORTS), yes)
	PYTEST_REPORT_OPTS = --cov-report html --cov-report xml --junitxml reports/report.xml
endif

.PHONY: help
help: ## show this message
	@awk \
		'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' \
		$(MAKEFILE_LIST)
	@if [[ -f general-resources.mk ]]; then \
		$(MAKE) --no-print-directory -f .general-resources.mk help; \
	fi

lint: ## run all linters
	@$(MAKE) --no-print-directory -f .general-resources.mk lint;

.PHONY: setup
setup: FORCE setup-local ## setup development environment
	@$(MAKE) --no-print-directory -f .general-resources.mk setup-npm setup-poetry setup-pre-commit;

setup-local: FORCE ## setup local environment by downloading general-resources
	@rm -rf .general-resources general-resources && mkdir -p .general-resources
	@curl -k -L --silent \
		'https://nexus-tools.swacorp.com/service/rest/v1/search/assets/download?sort=version&repository=releases&group=com.swacorp.ccplat.swa-common.ccp&name=general-resources&maven.extension=zip&version=%3C3.0.0' \
		--output ./.general-resources/general-resources.zip
	@unzip -q -o ./.general-resources/general-resources.zip -d ./.general-resources;
	@mv ./.general-resources/resources/module-setup.sh ./
	@bash module-setup.sh
	@rm module-setup.sh
	@rm -rf .general-resources

.PHONY: test
test: ## run integration and unit tests
	@echo "No tests to run."

# does not try to forward in pipelines or if the target is in the current Makefile.
# this is **very** delicate and should be modified with caution.
%: FORCE
	@if [[ ! -f .general-resources.mk ]]; then \
		echo ".general-resources.mk not found; run 'make setup' to create it."; \
	else \
		ALL_TARGETS="$$(grep '^[^#[:space:]].*:' Makefile)"; \
		if [[ "$@" != "Makefile" && $(GITLAB_CI) == "no" && "$${ALL_TARGETS}" != *"$@:"* ]]; then \
			$(MAKE) --no-print-directory -f .general-resources.mk $@; \
		fi; \
	fi

# alternative to using .PHONY; useful for dynamically generated targets
FORCE: ;
