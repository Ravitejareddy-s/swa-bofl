"""Delete SSM Parameters from ``customParameters`` in module config.

:Path: ``ccplatcfnginlibs.hooks.delete_custom_parameters``

.. rubric:: Example
.. code-block:: yaml

  pre_destroy:  # or post_destroy
    - path: ccplatcfnginlibs.hooks.delete_custom_parameters
      args:
        module_config_path: ${module_config}
        module_name: ${module_name}

"""

from __future__ import annotations

import logging
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from _typeshed import StrPath
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


def delete_custom_parameters(
    context: CfnginContext,
    *__args: Any,
    module_config_path: StrPath | None = None,
    module_name: str | None = None,
    **__kwargs: Any,
) -> bool:
    """Delete SSM Parameters from ``customParameters`` in module config.

    Args:
        context: CFNgin context object.
        module_config_path: Path to module config file.
        module_name: Name of the module.

    """
    if not module_name:
        LOGGER.warning(
            "skipped deleting custom SSM parameters; module_name not provided"
        )
        return True

    if not module_config_path:
        LOGGER.warning(
            "skipped deleting custom SSM parameters; module_config_path not provided"
        )
        return True

    module_config_path = Path(module_config_path)
    if not module_config_path.is_file():
        LOGGER.warning(
            "skipped deleting custom SSM parameters; module config file not found"
        )
        return True

    module_config = yaml.safe_load(Path(module_config_path).read_bytes())

    if "customParameters" not in module_config or not module_config["customParameters"]:
        return True

    client = context.get_session().client("ssm")
    for name in module_config["customParameters"]:
        with suppress(ClientError):
            client.delete_parameter(
                Name=f"/ccplat/{context.namespace}/{module_name}/customParams/{name}"
            )
    return True
