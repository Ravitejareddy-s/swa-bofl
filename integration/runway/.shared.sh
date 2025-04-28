#!/usr/bin/env bash
#
# Functions shared across scripts in this directory.

function log_deprecated { printf "\e[33;1m[DEPRECATED] %s\e[0m\n" "$*"; }
function log_error { printf "\e[31;1m[ERROR] %s\e[0m\n" "$*"; }
function log_notice { printf "\e[35;1m[NOTICE] %s\e[0m\n" "$*"; }
function log_warning { printf "\e[33;1m[WARNING] %s\e[0m\n" "$*"; }

function set_python_version {
  if [[ -n "${PYTHON_VERSION}" ]]; then
    echo "python version ${PYTHON_VERSION} specified - trying to use it...";

    if command -v pyenv &> /dev/null; then
      if command -v "python${PYTHON_VERSION}" &> /dev/null; then
        full_version="$(pyenv latest "${PYTHON_VERSION}")";
        all_versions=$(< ~/.pyenv/version)
        filtered_versions=("${all_versions[@]/$full_version}")
        # shellcheck disable=SC2048,SC2086
        pyenv global "$full_version" ${filtered_versions[*]};
      else
        log_error "python version could not be set; python${PYTHON_VERSION} not installed";
        pyenv versions;
        exit 9;
      fi

    else
      log_error "python version could not be set; pyenv not installed";
    fi
  fi
}

function update_tfvars_namespace {
  # Update `namespace` in a tfvars file.
  local NAMESPACE="$1"  # namespace to be inserted
  local FILENAME="$2"  # name of the file to update
  local NEW_CONTENT  # will be used to store new file content temporarily


  NEW_CONTENT=$(jq --indent 4 ". |= . + {\"namespace\": \"$NAMESPACE\"}" "$FILENAME")
  echo "$NEW_CONTENT" > "$FILENAME"
}

function update_tfvars_region {
  # Update `region` in a tfvars file.
  local REGION="$1"  # region to be inserted
  local FILENAME="$2"  # name of the file to update
  local NEW_CONTENT  # will be used to store new file content temporarily


  NEW_CONTENT=$(jq --indent 4 ". |= . + {\"region\": \"$REGION\"}" "$FILENAME")
  echo "$NEW_CONTENT" > "$FILENAME"
}

function write_runway_variables_yml {
  # Write to a file that can be automatically loaded by runway for the "var" lookup.
  local ACCOUNT_ID="$1"  # target account ID
  local NAMESPACE="$2"

  local FILENAME="runway.variables.yml"

  # shellcheck disable=SC1003
  if [[ -f "${FILENAME}" ]]; then sed -i '$a\' "${FILENAME}"; fi  # ensure file ends with a newline
  {  # run multiple commands before redirecting the output to a file
    echo "account_id: ${ACCOUNT_ID}"
    echo "bucket_prefix: swa-devops-${ACCOUNT_ID}"
    echo "namespace: ${NAMESPACE}"
    echo "target_account_id: ${ACCOUNT_ID}"
  } >> ${FILENAME}
}
