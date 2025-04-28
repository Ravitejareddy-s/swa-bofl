#This script is used in the script section of gitlab integration test job for tearing down testing resources

set -e

GIT_BRANCH_PROVIDED=0
ORIGINAL_GIT_BRANCH=''
if [ "$GIT_BRANCH" ]; then
  GIT_BRANCH_PROVIDED=1
  ORIGINAL_GIT_BRANCH=${GIT_BRANCH}
fi

SHORT_GIT_BRANCH=''
if [ "$CI_PIPELINE_SOURCE" == "merge_request_event" ]; then
  SHORT_GIT_BRANCH="mr-${CI_MERGE_REQUEST_IID}"
else
  SHORT_GIT_BRANCH=$(echo ${CI_COMMIT_REF_SLUG} | sed "s/feature-//g")
fi

SHORT_COMMIT_SHA=${CI_COMMIT_SHORT_SHA:0:6}

if [ -z "$DEPLOY_ENVIRONMENT" ]; then
  export DEPLOY_ENVIRONMENT=${TEST_NAME}
fi

if [ "$GIT_BRANCH_PROVIDED" -eq 0 ]; then
    export GIT_BRANCH=$SHORT_GIT_BRANCH-$SHORT_COMMIT_SHA-${TEST_NAME}
  else
    export GIT_BRANCH=$ORIGINAL_GIT_BRANCH
  fi

cd ${CI_PROJECT_DIR}/integration/runway
echo "Runway Destroy"
./entrypoint.sh runway destroy

if [ -d "${CI_PROJECT_DIR}/integration/pre-deployments/environment/local/${TEST_NAME}" ]; then
  echo "Destroying pre deployments for ${TEST_NAME}"
  if [ "$GIT_BRANCH_PROVIDED" -eq 0 ]; then
    export GIT_BRANCH=other-$SHORT_GIT_BRANCH-$SHORT_COMMIT_SHA-${TEST_NAME}
  else
    export GIT_BRANCH=other-$ORIGINAL_GIT_BRANCH
  fi
  cd ${CI_PROJECT_DIR}/integration/pre-deployments/runway

  echo "Runway Destroy"
  ./entrypoint.sh runway destroy
fi

if [ -f ${CI_PROJECT_DIR}/integration/post_hooks.py ]; then
  echo "Executing Python Post Hooks"
  python3 ${CI_PROJECT_DIR}/integration/post_hooks.py
elif [ -f ${CI_PROJECT_DIR}/integration/post_hooks.sh ]; then
  echo "Executing Shell Post Hooks"
  sh ${CI_PROJECT_DIR}/integration/post_hooks.sh
fi
