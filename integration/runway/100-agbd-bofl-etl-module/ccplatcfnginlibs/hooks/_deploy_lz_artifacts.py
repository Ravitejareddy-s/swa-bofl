"""Hook used to deploy artifacts using the Landing Zone deployment engine.

:Path: ``ccplatcfnginlibs.hooks.deploy_lz_artifacts``

.. rubric:: Example
.. code-block:: yaml

    pre_deploy:
      - path: libs.hooks.lz_deploy_artifacts.hook
        required: true
        enabled: true
        args:
          s3_prefix: theprefix
          artifacts:
            - artifacts/artifact1.zip
            - artifacts/artifact2.zip
          environment: ${environment}
          timeout: 300

- artifacts: The path to one or more artifacts to be deployed.
- environment: The environment to deploy to.
- s3_prefix: The prefix used when uploading the artifact to the s3 bucket.
- timeout: (optional) The timeout (in seconds) before the the hook times out and the
           deployment is marked as failed. Default is 900 (15 minutes).

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..helpers.lz_deployer import deploy_artifacts

if TYPE_CHECKING:
    from runway.context import CfnginContext

DEFAULT_TIMEOUT = 900


def deploy_lz_artifacts(
    context: CfnginContext,
    *__args: Any,
    artifacts: list[str],
    environment: str,
    s3_prefix: str,
    timeout: int | str | None = None,
    **__kwargs: Any,
) -> bool:
    """CFNgin Hook that deploys artifact(s).

    Args:
        context: CFNgin context object.
        artifacts: List of paths to artifacts to upload.
        environment: The environment to deploy to.
        s3_prefix: Prefix for S3 objects.
        timeout: Time to wait when uploading artifacts.

    """
    if artifacts:
        deploy_artifacts(
            artifact_paths=artifacts,
            env=environment,
            region=context.env.aws_region,
            s3_prefix=s3_prefix,
            timeout=int(timeout or DEFAULT_TIMEOUT),
        )
        return True
    return False
