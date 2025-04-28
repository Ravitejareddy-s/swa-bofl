"""Delete all SSM parameters published by the``publish_ssm_parameters`` hook.

:Path: ``ccplatcfnginlibs.hooks.delete_module_ssm_parameters``

.. deprecated:: 3.0.0

.. rubric:: Example
.. code-block:: yaml

  pre_destroy:  # or post_destroy
    - path: ccplatcfnginlibs.hooks.delete_module_ssm_parameters
      args:
        global_module: true  # default: false
        module_name: ${module_name}
        stack_postfix: ${default stack_postfix::None}

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from deprecated import deprecated

from ..constants import SUPPORTED_AWS_REGIONS

if TYPE_CHECKING:
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


@deprecated(
    reason="SSM Parameters should be created as part of a stack; "
    "Stack outputs should be referenced directly instead of using SSM Parameters"
)
def delete_module_ssm_parameters(
    context: CfnginContext,
    *__args: Any,
    global_module: bool = False,
    module_name: str | None = None,
    stack_postfix: str | None = None,
    **__kwargs: Any,
) -> bool:
    """Delete all SSM parameters published by the``publish_ssm_parameters`` hook.

    Args:
        context: CFNgin context object.
        global_module: Whether or not this is a global module.
        module_name: Name of the module.
        stack_postfix: Postfix to append to the stack name.

    """
    if not module_name:
        LOGGER.warning("skipped deleting SSM parameters; module_name not provided")
        return True

    if stack_postfix:
        module_name = f"{module_name}/{stack_postfix}"

    session = context.get_session()

    region_list = SUPPORTED_AWS_REGIONS if global_module else [context.env.aws_region]

    for region in region_list:
        client = session.client("ssm", region_name=region)
        parameters = [
            i["Name"]
            for i in [
                param
                for page in client.get_paginator("get_parameters_by_path").paginate(
                    Path=f"/ccplat/{context.namespace}/{module_name}",
                    Recursive=True,
                    WithDecryption=True,
                )
                for param in page["Parameters"]
            ]
            if "Name" in i
        ]
        for chunk in [
            parameters[i * 10 : (i + 1) * 10]
            for i in range((len(parameters) + 10 - 1) // 10)
        ]:
            client.delete_parameters(Names=chunk)
    return True
