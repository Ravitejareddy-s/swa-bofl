"""Create all parameters passed into CFNgin to SSM.

:Path: ``ccplatcfnginlibs.hooks.create_module_ssm_parameters``

.. deprecated:: 3.0.0

.. rubric:: Example
.. code-block:: yaml

  post_deploy:
    - path: ccplatcfnginlibs.hooks.create_module_ssm_parameters
      args:
        global_module: true  # default: false
        global_params:
          stack1:
            - output1
            - output2
          stack2:
            - output1
            - output2
        module_name: ${module_name}
        module_config_path: ${module_config}
        stack_postfix: ${default stack_postfix::None}

"""

from __future__ import annotations

import logging
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any

from deprecated import deprecated
from runway.core.providers.aws.type_defs import TagTypeDef

from ..constants import SUPPORTED_AWS_REGIONS
from .global_params.handle_global_params import (
    GlobalParamConfig,
    HandleGlobalParamsDependencies,
    HandleGlobalParamsParams,
    Operation,
    handle_global_params,
)

if TYPE_CHECKING:
    import boto3
    from _typeshed import StrPath
    from mypy_boto3_cloudformation.type_defs import OutputTypeDef
    from mypy_boto3_ssm.client import SSMClient
    from runway.cfngin.providers.aws.default import Provider
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


@deprecated(
    reason="each module should publish only the parameters it needs as part "
    "of a Stack or a custom hook"
)
class Dependencies(HandleGlobalParamsDependencies):
    """Dependencies."""

    def __init__(self, context: CfnginContext, provider: Provider) -> None:
        """Instantiate class."""
        self.ctx = context
        self.provider = provider

    @cached_property
    def session(self) -> boto3.Session:
        """Return cached boto3 session."""
        return self.ctx.get_session()

    def get_stack_outputs(self, stack_name: str) -> list[OutputTypeDef]:
        """Get CloudFormation Stack Outputs."""
        return self.provider.get_stack(stack_name).get("Outputs", [])

    def publish_ssm_param(
        self,
        full_name: str,
        value: str,
        region: str = "us-east-1",
        tags: dict[str, str] | None = None,
    ) -> None:
        """Publish SSM parameter."""
        return put_parameter(
            self.session.client("ssm", region_name=region), full_name, value, tags=tags
        )


@deprecated(
    reason="SSM Parameters should be created as part of a stack; "
    "Stack outputs should be referenced directly instead of using SSM Parameters"
)
def create_module_ssm_parameters(  # noqa: C901
    context: CfnginContext,
    *__args: Any,
    global_module: bool = False,
    global_params: dict[str, list[str]] | None = None,
    module_name: str | None = None,
    module_config_path: StrPath | None = None,
    provider: Provider,
    stack_postfix: str | None = None,
    **__kwargs: Any,
) -> bool:
    """Create all parameters passed into CFNgin to SSM.

    Args:
        context: CFNgin context object.
        global_module: Whether or not this is a global module.
        global_params: Global parameters to publish.
        module_name: Name of the module.
        module_config_path: Path to the module's config file.
        provider: CFNgin provider object.
        stack_postfix: Postfix to append to the stack name.

    """
    if not module_name:
        LOGGER.warning("skipped creating SSM parameters; module_name not provided")
        return True

    if stack_postfix:
        module_name = f"{module_name}/{stack_postfix}"

    session = context.get_session()
    client = session.client("ssm")
    tags = [TagTypeDef(Key=k, Value=v) for k, v in context.tags.items()]

    for param, value in context.parameters.items():
        if param != "module_config":
            put_parameter(
                client,
                f"/ccplat/{context.namespace}/{module_name}/params/{param}",
                value,
                tags=tags,
            )

    if module_config_path:
        module_config_path = Path(module_config_path)
        if module_config_path.is_file():
            module_config_string = (
                module_config_path.read_text().replace("{{", "").replace("}}", "")
            )
            put_parameter(
                client,
                f"/ccplat/{context.namespace}/{module_name}/params/module_config",
                module_config_string,
                tags=tags,
            )

    region_list = SUPPORTED_AWS_REGIONS if global_module else [context.env.aws_region]
    for stack in [stack for stack in context.stacks if stack.enabled]:
        for region in region_list:
            if len(region_list) > 1:
                region_client = session.client("ssm", region_name=region)
                stack_name = f"{stack.name}-{region}"
            else:
                region_client = client
                stack_name = stack.name
            for output_key, output_value in stack.outputs.items():
                put_parameter(
                    region_client,
                    f"/ccplat/{context.namespace}/{module_name}/{stack_name}/{output_key}",
                    output_value,
                    tags=tags,
                )

    if global_params:
        handle_global_params(
            Dependencies(context, provider),
            GlobalParamConfig.create(global_params),
            HandleGlobalParamsParams.create(
                context, SUPPORTED_AWS_REGIONS, module_name, context.namespace
            ),
            Operation.PUBLISH,
        )
    return True


def put_parameter(
    client: SSMClient,
    fqn: str,
    value: Any,
    *,
    description: str = "CFNgin parameter",
    tags: dict[str, str] | list[TagTypeDef] | None = None,
) -> None:
    """Put SSM parameter.

    Args:
        client: SSM client.
        fqn: Fully qualified name of the parameter.
        value: Value of the parameter.
        description: Description of the parameter. If ``value`` is truncated,
            ``TRUNCATED`` will be appended to the description.
        tags: Tags to add to the parameter.

    """
    client.put_parameter(
        Description=f"TRUNCATED {description}" if len(value) > 4096 else description,
        Name=fqn,
        Overwrite=True,
        Type="String",
        Value=str(value)[:4095],
    )
    if tags:
        client.add_tags_to_resource(
            ResourceId=fqn,
            ResourceType="Parameter",
            Tags=(
                [TagTypeDef(Key=k, Value=v) for k, v in tags.items()]
                if isinstance(tags, dict)
                else tags
            ),
        )
