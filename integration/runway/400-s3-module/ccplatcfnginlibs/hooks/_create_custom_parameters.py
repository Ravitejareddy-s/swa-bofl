"""Create SSM Parameters from ``customParameters`` in module config.

:Path: ``ccplatcfnginlibs.hooks.create_custom_parameters``

.. rubric:: Example
.. code-block:: yaml

  post_deploy:
    - path: ccplatcfnginlibs.hooks.create_custom_parameters
      args:
        module_config_path: ${module_config}
        module_name: ${module_name}

"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from runway.lookups.handlers.cfn import CfnLookup

if TYPE_CHECKING:
    from _typeshed import StrPath
    from runway.cfngin.providers.aws.default import Provider
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


def create_custom_parameters(
    context: CfnginContext,
    *__args: Any,
    module_config_path: StrPath | None = None,
    module_name: str | None = None,
    provider: Provider,
    **__kwargs: Any,
) -> bool:
    """Create SSM Parameters from ``customParameters`` in module config.

    Args:
        context: Runway context object.
        module_config_path: Path to module config.
        module_name: Name of module.
        provider: Runway provider object.

    """
    if not module_name:
        LOGGER.warning(
            "skipped creating custom SSM parameters; module_name not provided"
        )
        return True

    if not module_config_path:
        LOGGER.warning(
            "skipped creating custom SSM parameters; module_config_path not provided"
        )
        return True

    module_config_path = Path(module_config_path)
    if not module_config_path.is_file():
        LOGGER.warning(
            "skipped creating custom SSM parameters; module config file not found"
        )
        return True

    module_config = yaml.safe_load(module_config_path.read_bytes())

    if "customParameters" not in module_config or not module_config["customParameters"]:
        return True

    client = context.get_session().client("ssm")
    kms_key_id = CfnLookup.handle("EC-KmsKey.KmsKeyID", context, provider=provider)
    for name, value in module_config["customParameters"].items():
        fqn = f"/ccplat/{context.namespace}/{module_name}/customParams/{name}"
        client.put_parameter(
            Description=(
                "TRUNCATED Custom Parameter"
                if len(value) > 4096
                else "Custom Parameter"
            ),
            KeyId=kms_key_id,
            Name=fqn,
            Overwrite=True,
            Type="SecureString",
            Value=value[:4095],
        )
        client.add_tags_to_resource(
            ResourceType="Parameter",
            ResourceId=fqn,
            Tags=[{"Key": k, "Value": v} for k, v in context.tags.items()],
        )
    return True
