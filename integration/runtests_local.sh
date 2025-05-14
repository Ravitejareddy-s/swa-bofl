#!/usr/bin/env bash
#
# By default, the test-suite will look to execute a `test1.py` test file, with a deployment specified in a `test1`
# environment directory.
# You can modify this behavior by setting one or both of the following environment variables:
# export TEST_ENV=test-environment-directory-name-to-deploy
# export TEST_TO_RUN=name-of-test-file
# Note: The directory specified by TEST_ENV must be within the environments directory in your module.
# Note: For TEST_TO_RUN, include only the file name, with no file extension/suffix included

set -e

echo "Starting runtests_local.sh"

# re-export env vars
export AWS_CONFIG_FILE="${AWS_CONFIG_FILE:-/aws/config}";
export AWS_PROFILE="${AWS_PROFILE:-${AWS_DEFAULT_PROFILE:-default}}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="${AWS_REGION:-us-east-1}"  # required by boto clients
export AWS_SDK_LOAD_CONFIG="1";
export AWS_SHARED_CREDENTIALS_FILE="${AWS_SHARED_CREDENTIALS_FILE:-/aws/credentials}";
export ENVIRONMENT="lab";

# setup local vars
TEST_DEPLOY="${TEST_DEPLOY:-true}";
TEST_RUN="${TEST_RUN:-true}";
TEST_DESTROY="${TEST_DESTROY:-true}";
TEST_ENV="${TEST_ENV:-test1}";

REQUIRED_ENV_VARS=(
  AWS_CONFIG_FILE
  MODULENAME
  GIT_BRANCH
)

for i in "${REQUIRED_ENV_VARS[@]}"; do
  if [[ ${!i} == "" ]]; then
    echo "Missing Env Var $i";
    exit 9;
  fi
done

BASE_NAMESPACE=$( echo "${GIT_BRANCH/\//-}" | xargs | tr "[:upper:]" "[:lower:]" );
export NAMESPACE="${BASE_NAMESPACE}-${TEST_ENV}";

echo "AWS_REGION: ${AWS_REGION}";
echo "GIT_BRANCH: ${GIT_BRANCH}";
echo "MODULENAME: ${MODULENAME}";
echo "NAMESPACE: ${NAMESPACE}";

if [[ -n "${PYTHON_VERSION}" ]]; then
  echo "python version ${PYTHON_VERSION} specified - trying to use it...";

  if command -v pyenv &> /dev/null; then
    if command -v "python${PYTHON_VERSION}" &> /dev/null; then
      full_version="$(pyenv latest ${PYTHON_VERSION})";
      echo "python version ${full_version} found - trying to use it";
      all_versions=$(< ~/.pyenv/version)
      filtered_versions=("${all_versions[@]/$full_version}")
      pyenv global $full_version ${filtered_versions[*]};

    else
      echo "python version could not be set; python${PYTHON_VERSION} not installed";
      pyenv versions;
      exit 1;
    fi
  else
    echo "python version could not be set; pyenv not installed";
  fi
fi

export NVM_DIR="$HOME/.nvm"
# shellcheck disable=SC1091
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
if [[ -n "${NODE_VERSION}" ]]; then
  echo "setting node version: ${NODE_VERSION} through NODE_VERSION environment variable...";
  nvm use "${NODE_VERSION}";
elif [[ -f ./.nvmrc ]]; then
  echo "setting node version from .nvmrc file in project...";
  nvm use;
else
  echo "using default node version...";
  nvm use default;
fi
npm --version >/dev/null 2>&1;


# Use Met to build infra container for this test run
echo "Creating local directory with module source in integration folder";
if [[ -d 'local' ]]; then rm -rf local; fi
mkdir -p /work/integration/local;
rsync -av --exclude-from='/usr/share/rsync_exclude' --no-perms --no-owner --no-group /work/ "local/${MODULENAME}";


# Change networking_tier_namespace value
echo "Looking for files to update namespace";
REPLACE_NAMESPACE=${TO_BE_REPLACED_NS:-other-${BASE_NAMESPACE}}
if [[ -d "pre-deployments" ]] && [[ -z "${SKIP_PRE_DEPLOY}" ]]; then
  for file in $(grep -Rl "to-be-replaced" ./environment); do
    sed -i.bak "s/to-be-replaced/${REPLACE_NAMESPACE}/" "$file";
    rm "${file}.bak";
    echo "Updated ${file} to use networking_tier_namespace ${REPLACE_NAMESPACE}";
    cat "$file";
  done
fi

echo "Running met to generate deployment configuration";
met /work/integration;

# Gather the tests. They should have corresponding environment definitions in integration/environment
echo "Starting test suite execution";
echo "Deploy test suite - ${TEST_DEPLOY}";
echo "Run test suite - ${TEST_RUN}";
echo "Destroy test suite - ${TEST_DESTROY}";

TEST_NAME="${TEST_TO_RUN:-$TEST_ENV}";

echo "Running test $TEST_NAME";
echo "Using environment named $TEST_ENV";

# Install requirements needed for pre & post hooks
if [[ -f /work/integration/requirements.txt ]]; then
  pip install -r /work/integration/requirements.txt;
fi

if [[ $TEST_DEPLOY == "true" ]]; then
  # Run Pre-hooks
  if [ -f /work/integration/pre_hooks.py ]; then
    python3 /work/integration/pre_hooks.py;
  elif [ -f /work/integration/pre_hooks.sh ]; then
    bash /work/integration/pre_hooks.sh;
  fi
fi

# Run Pre-deployments
if [[ -d "/work/integration/pre-deployments/environment/local/${TEST_ENV}" ]] && [[ -z "${SKIP_PRE_DEPLOY}" ]]; then
  echo "Found pre-deployments for ${TEST_ENV}";
  pushd /work/integration/pre-deployments;
  met "${PWD}";

  pushd /work/integration/pre-deployments/runway;
  export DEPLOY_ENVIRONMENT="${TEST_ENV}";
  export GIT_BRANCH="other-${NAMESPACE}";
  ./entrypoint.sh runway deploy --deploy-environment "${TEST_ENV}" --ci;
  popd;
  popd;
fi

# Set up environment
if [[ $TEST_DEPLOY == "true" ]]; then
  pushd /work/integration/runway;
  export DEPLOY_ENVIRONMENT="${TEST_ENV}";
  export GIT_BRANCH="${NAMESPACE}";
  ./entrypoint.sh runway deploy --deploy-environment "${TEST_ENV}" --ci;
  popd;
fi

# Run test
if [[ $TEST_RUN == "true" ]]; then
  pushd /work;
  export DEPLOY_ENVIRONMENT="${TEST_ENV}";
  export GIT_BRANCH="${NAMESPACE}";
  if [[ -f poetry.lock ]]; then
    poetry lock --check;
    poetry install --sync;
    poetry run pytest "/work/integration/${TEST_NAME}.py";
  else
    pytest "/work/integration/${TEST_NAME}.py";
  fi
  popd
fi

# Tear down environment
if [[ $TEST_DESTROY == "true" ]]; then
  pushd /work/integration/runway;
  export DEPLOY_ENVIRONMENT="${TEST_ENV}";
  export GIT_BRANCH="${NAMESPACE}";
  ./entrypoint.sh runway destroy --deploy-environment "${TEST_ENV}" --ci;
  popd;
fi

# Run Post-deployments
if [ -d "/work/integration/pre-deployments/environment/local/${TEST_ENV}" ]; then
  echo "Found pre-deployments for ${TEST_ENV}";
  echo "Destroying...";

  # Teardown pre-deploy environment
  if [[ $TEST_DESTROY == "true" ]]; then
    pushd /work/integration/pre-deployments/runway;
    export DEPLOY_ENVIRONMENT="${TEST_ENV}";
    export GIT_BRANCH="other-${NAMESPACE}";
    ./entrypoint.sh runway deploy --deploy-environment "${TEST_ENV}" --ci;
    popd;
  fi
fi

if [[ $TEST_DESTROY == "true" ]]; then
  # Run Post-hooks
  if [ -f /work/integration/post_hooks.py ]; then
    python3 /work/integration/post_hooks.py;
  elif [ -f /work/integration/post_hooks.sh ]; then
    bash /work/integration/post_hooks.sh;
  fi
fi

# Change networking_tier_namespace value back
echo "Reverting files with updated namespace"
if [[ -d "/work/integration/pre-deployments" ]] && [[ -z "${SKIP_PRE_DEPLOY}" ]]; then
  for file in $(grep -Rl "${REPLACE_NAMESPACE}" ./environment); do
    sed -i.bak "s/${REPLACE_NAMESPACE}/to-be-replaced/" "${file}";
    rm "${file}.bak";
    echo "Reverted ${file}";
    cat "${file}";
  done
fi
