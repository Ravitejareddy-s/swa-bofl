#!/usr/bin/env bash
#
# This script exists, because there's no good way to get the current target account into the configuration files otherwise.

set -e;
source "$(dirname "$0")/.shared.sh";  # load functions

# Expected Variables
completed_deployments=()

required_env=(
  DEPLOY_ENVIRONMENT  # name of an environment under ${ENVIRONMENT}
  ENVIRONMENT  # dev|qa|prod
  GIT_BRANCH  # used for namespace
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

echo "Current environment selected for deployment: ${DEPLOY_ENVIRONMENT}"
# Parse the environments.yml file and set the declared_environment in order to deploy with runway.
environments_file=./environments.yml
# Check if the environments.yml file exists else display error and exit.
if [[ -f "$environments_file" ]]; then
  deployments_array=()
  # Check for ENVIRONMENT variable for specified deploy job - based on top level key in environments.yml
  case $ENVIRONMENT in
    dev|qa|prod)
      base_environment=$ENVIRONMENT
      ;;

    *)
      log_error "Specified ENVIRONMENT \"${ENVIRONMENT}\" is invalid. Deployment YML should not be modified. Environment should be one of: dev, qa, prod."
      exit 1
      ;;
  esac
else
  log_error "No environments.yml file found! One must exist for deployment."
  log_error "Refer to https://confluence-tools.swacorp.com/pages/viewpage.action?pageId=889269320"
  exit 1
fi
# Setting deployment variables based on output of environments.yml format.
new_deployments_check=$(yq r environments.yml "${base_environment}.${DEPLOY_ENVIRONMENT}.deployments" | sed 's/^[^0-9]*//' | sed 's/null//')
default_deployments_check=$(yq r environments.yml deployments.* | sed 's/^[^0-9]*//' | sed 's/null//')

if [[ -n "${REGIONAL_DEPLOYMENT}" ]]; then
  echo "Using regional deployment environment variable: ${REGIONAL_DEPLOYMENT}"
  new_deployments_check="${REGIONAL_DEPLOYMENT}"
  default_deployments_check="${REGIONAL_DEPLOYMENT}"
fi

echo "Parsing environments.yml for new_deployments_check: ${new_deployments_check}"
echo "Parsing environments.yml for default_deployments_check: ${default_deployments_check}"

# Checking if both new_deployments_check and default_deployments_check are empty and then printing error info and exit.
if [[ ${new_deployments_check} == '' ]] && [[ ${default_deployments_check} == '' ]]; then
  log_error "The environments.yml file doesn't appear to contain any valid deployments for environment: ${DEPLOY_ENVIRONMENT}."
  log_error "Please refer to https://confluence-tools.swacorp.com/pages/viewpage.action?pageId=889269320"
  exit 1
# If new_deployments_check is empty (no specific deployments configured in environments.yml then set defaults.
elif [[ $new_deployments_check == '' ]]; then
  for line in ${default_deployments_check}; do
    if [[ ${line} != '' ]]; then
      deployments_array+=("${line}")
    fi
  done
  echo "No specific deployments found: ${DEPLOY_ENVIRONMENT} so using defaults: ${deployments_array[*]}"
else
  # If default_deployments_check is empty then echo update suggestion message.
  # Continue on and parse new_deployments_check.
  if [[ $default_deployments_check == '' ]]; then
    echo "No defaults list in environments.yml."
    echo "Consider updating to the new environments.yml format."
    echo "Refer to https://confluence-tools.swacorp.com/pages/viewpage.action?pageId=889269320"
  fi
  for line in ${new_deployments_check}; do
    if [[ ${line} != '' ]]; then
      deployments_array+=("${line}")
    fi
  done
  echo "Specific deployments found in: ${DEPLOY_ENVIRONMENT}: ${deployments_array[*]}"
fi

# Reverse order when destroying
# shellcheck disable=SC2199
if [[ "$@" == *"destroy"* ]]; then
  for (( idx=${#deployments_array[@]}-1 ; idx>=0 ; idx-- )) ; do
    reverse_deployments_array+=("${deployments_array[idx]}")
  done
  deployments_array=()
  deployments_array=("${reverse_deployments_array[@]}")
  echo "Specific deployments found in: ${DEPLOY_ENVIRONMENT} for destroying: ${deployments_array[*]}"
fi

set_python_version;
write_runway_variables_yml "${target_account_id}" "${GIT_BRANCH}";

# Start runway run based on each element of deployments_array.
for parsed_deployment in "${deployments_array[@]}"; do

  echo "Current selected deployment: ${parsed_deployment}"
  region=$(yq r runway.yml deployments -j | jq --arg DESIRED_DEPLOYMENT "$parsed_deployment" '.[] | select(.name==$DESIRED_DEPLOYMENT)' | jq .regions[0] | sed 's/"//g')
  export AWS_REGION=${region}

  for env_file in $(find . | grep "${DEPLOY_ENVIRONMENT}.env$" ); do
    sed -i '/^cfngin_bucket_name:/d' "${env_file}"
    sed -i '/^createDate:/d' "${env_file}"
    sed -i '/^namespace:/d' "${env_file}"
    sed -i '/^region:/d' "${env_file}"  # region isn't necessary; handled by runway
    sed -i '/^stacker_bucket_name:/d' "${env_file}"
    # shellcheck disable=SC1003
    sed -i '$a\' "${env_file}"  # ensure file ends with a newline
    {  # run multiple commands before redirecting the output to a file
      echo "cfngin_bucket_name: swa-devops-${target_account_id}-${region}"
      echo "createDate: remove me"
      echo "namespace: ${GIT_BRANCH}"
      echo "stacker_bucket_name: swa-devops-${target_account_id}-${region}"
    } >> "${env_file}"
  done

  # Serverless Bucket
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
      echo "namespace: ${GIT_BRANCH}"
      echo "region: ${region}"
      echo "serverless_bucket_name: swa-devops-${target_account_id}-${region}"
    } >> "${yml_file}"
  done

  for tfvars_file in $(find . | grep "${DEPLOY_ENVIRONMENT}.tfvars.json$" ); do
    update_tfvars_namespace "${GIT_BRANCH}" "${tfvars_file}";
    update_tfvars_region "${region}" "${tfvars_file}";
  done

  completed_deployments=("${completed_deployments[@]}" "$parsed_deployment")

  echo "Runway Version";
  runway --version;

  # Run CMD
  "$@" --tag "${parsed_deployment}"
  # shellcheck disable=SC2181
  [ $? -eq 0 ]  || exit 1

done

echo "Completed operations for: ";
echo "${completed_deployments[@]}" | tr ' ' '\n';
