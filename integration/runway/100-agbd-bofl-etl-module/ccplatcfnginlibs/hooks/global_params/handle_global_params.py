"""Hook to handle global parameters."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from deprecated import deprecated

if TYPE_CHECKING:
    from mypy_boto3_cloudformation.type_defs import OutputTypeDef
    from runway.context import CfnginContext


class HandleGlobalParamsDependencies(Protocol):
    """Handle global parameter dependencies."""

    def get_stack_outputs(self, stack_name: str) -> list[OutputTypeDef]:
        """Get stack outputs."""
        raise NotImplementedError

    def publish_ssm_param(
        self,
        full_name: str,
        value: str,
        region: str = "us-east-1",
        tags: dict[str, str] | None = None,
    ) -> None:
        """Publish SSM parameters."""
        raise NotImplementedError


@dataclass
class GlobalParamConfig:
    """Global parameter config."""

    stack_key: str
    output_match_keys: list[str]

    @classmethod
    def create(cls, config: dict[str, list[str]]) -> list[GlobalParamConfig]:
        """Create instances of type ``GlobalParamConfig``."""
        return [
            GlobalParamConfig(stack_key, output_match_keys)
            for stack_key, output_match_keys in config.items()
        ]


@dataclass
class HandleGlobalParamsParams:
    """Handle global parameters parameters."""

    cfn_stacks: list[str]
    supported_regions: list[str]
    tags: dict[str, str]
    namespace: str
    module_name: str

    @classmethod
    def create(
        cls,
        context: CfnginContext,
        regions: list[str],
        module_name: str,
        namespace: str,
    ) -> HandleGlobalParamsParams:
        """Create instance of ``HandleGlobalParamsParams`` class."""
        cfn_stacks = [
            f"{namespace}-{stack.stack_name or stack.name}"
            for stack in context.config.stacks
        ]
        return HandleGlobalParamsParams(
            cfn_stacks, regions, context.tags, namespace, module_name
        )


class Operation(enum.Enum):
    """Operations."""

    PUBLISH = 1


@deprecated(
    reason="each module should publish only the parameters it needs as part "
    "of a Stack or a custom hook"
)
def handle_global_params(
    deps: HandleGlobalParamsDependencies,
    configs: list[GlobalParamConfig],
    params: HandleGlobalParamsParams,
    operation: Operation,
) -> None:
    """Handle global parameters."""
    for config in configs:
        stack_matches = [
            name
            for name in params.cfn_stacks
            if config.stack_key.lower() in name.lower()
        ]
        if not stack_matches:
            continue

        stack_name = stack_matches[0]
        outputs = deps.get_stack_outputs(stack_name)
        output_matches = [
            output
            for output in outputs
            if any(
                key
                for key in config.output_match_keys
                if "OutputKey" in output and key.lower() in output["OutputKey"].lower()
            )
        ]
        if not output_matches:
            continue

        for match in output_matches:
            key, value = (match.get("OutputKey"), match.get("OutputValue"))
            param_name = (
                f"/ccplat/{params.namespace}/{params.module_name}/{stack_name}/{key}"
            )
            for region in params.supported_regions:
                if operation == Operation.PUBLISH and value:
                    deps.publish_ssm_param(param_name, value, region, params.tags)
                else:
                    raise ValueError("Invalid operation selected")
