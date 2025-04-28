#!/usr/bin/env bash
#
# This script exists, because there's no good way to get the current target account into the configuration files otherwise.

set -ex;
source "$(dirname "$0")/.shared.sh";  # load functions

# Expected Variables
required_env=(
  AWS_REGION
  DEPLOY_ENVIRONMENT  # name of an environment
  GIT_BRANCH  # used for namespace
)

if [[ -z "${AWS_REGION}" ]]; then
  AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
fi

for i in "${required_env[@]}"; do
  if [[ ${!i} == "" ]]; then
    log_error "Missing Env Var $i"
    exit 1
  fi
done

if [ -z "$DESIRED_DEPLOYMENT" ]; then
  DESIRED_DEPLOYMENT=00-main
fi

# Make sure AWS credentials are valid
# Get Account Id
target_account_id=$(aws sts get-caller-identity --output text --query 'Account')

if [[ ${target_account_id} == "" ]]; then
  log_error "Missing Aws Credentials"
  exit 1
fi


# NAMESPACE is branch_name converted to lowercase, and '/' to '-'
NAMESPACE=$(echo "${GIT_BRANCH}" | tr 'A-Z/' 'a-z-')

set_python_version;
write_runway_variables_yml "${target_account_id}" "${NAMESPACE}";

for env_file in $(find . | grep "${DEPLOY_ENVIRONMENT}.env$" ); do
  sed -i '/^cfngin_bucket_name:/d' "${env_file}"
  sed -i '/^createDate:/d' "${env_file}"
  sed -i '/^namespace:/d' "${env_file}"
  sed -i '/^region:/d' "${env_file}"  # region isn't necessary; handled by runway
  sed -i '/^stacker_bucket_name:/d' "${env_file}"
  # shellcheck disable=SC1003
  sed -i '$a\' "${env_file}"  # ensure file ends with a newline
  {  # run multiple commands before redirecting the output to a file
    echo "cfngin_bucket_name: swa-devops-${target_account_id}-${AWS_REGION}"
    echo "createDate: remove me"
    echo "namespace: ${NAMESPACE}"
    echo "stacker_bucket_name: swa-devops-${target_account_id}-${AWS_REGION}"
  } >> "${env_file}"
done

for yml_file in $(find . | grep "config-${DEPLOY_ENVIRONMENT}.yml$" ); do
  # removing old values
  sed -i '/^createDate:/d' "${yml_file}"
  sed -i '/^namespace:/d' "${yml_file}"
  sed -i '/^region:/d' "${yml_file}"
  sed -i '/^serverless_bucket_name:/d' "${yml_file}"
  # shellcheck disable=SC1003
  sed -i '$a\' "${yml_file}"  # ensure file ends with a newline
  {  # run multiple commands before redirecting the output to a file
    echo "createDate: remove me"
    echo "namespace: ${NAMESPACE}"
    echo "region: ${AWS_REGION}"
    echo "serverless_bucket_name: swa-devops-${target_account_id}-${AWS_REGION}"
  } >> "${yml_file}"
done

for tfvars_file in $(find . | grep "${DEPLOY_ENVIRONMENT}.tfvars.json$" ); do
  update_tfvars_namespace "${NAMESPACE}" "${tfvars_file}"
  update_tfvars_region "${AWS_REGION}" "${tfvars_file}"
done

# Update runway.yml for correct region targeting
if [ "$AWS_REGION" != "us-east-1" ]; then
  sed -i "s/us-east-1/${AWS_REGION}/" runway.yml
fi

echo "Runway Version";
runway --version;

# Run CMD
exec "$@" --tag "${DESIRED_DEPLOYMENT}"
