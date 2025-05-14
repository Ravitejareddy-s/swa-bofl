#!/bin/bash
#
# Preflight checks

set -ex;
source "$(dirname "$0")/.shared.sh";  # load functions

# Expected Variables
required_env=(
  GIT_BRANCH
)

for i in "${required_env[@]}"; do
  if [[ ${!i} == "" ]]; then
    log_error "Missing Env Var $i"
    exit 1
  fi
done

# Make sure AWS credentials are valid
# Get Account Id
target_account_id=$(aws sts get-caller-identity --output text --query 'Account')

if [[ ${target_account_id} == "" ]]; then
  log_error "Missing Aws Credentials"
  exit 1
fi

set_python_version;
write_runway_variables_yml "${target_account_id}" "${GIT_BRANCH}";

# shellcheck disable=SC2013
for deploy_env in $(cat /work/runway/test_targets.txt); do
  env_name=$(echo "${deploy_env}" | sed 's/-.*//g')
  region=$(echo "${deploy_env}" | sed 's/^.*-//g')
  for env_file in $(find . | grep "${env_name}-${region}.env$" ); do
    sed -i '/^cfngin_bucket_name:/d' "${env_file}"
    sed -i '/^namespace:/d' "${env_file}"
    sed -i '/^region:/d' "${env_file}"  # region isn't necessary; handled by runway
    sed -i '/^stacker_bucket_name:/d' "${env_file}"
    # shellcheck disable=SC1003
    sed -i '$a\' "${env_file}"  # ensure file ends with a newline
    {  # run multiple commands before redirecting the output to a file
      echo "cfngin_bucket_name: swa-devops-${target_account_id}-${region}"
      echo "namespace: ${GIT_BRANCH}"
      echo "stacker_bucket_name: swa-devops-${target_account_id}-${region}"
    } >> "${env_file}"
  done
  # Preflight check all the potential target environments.
  DEPLOY_ENVIRONMENT=${deploy_env} runway preflight
done
