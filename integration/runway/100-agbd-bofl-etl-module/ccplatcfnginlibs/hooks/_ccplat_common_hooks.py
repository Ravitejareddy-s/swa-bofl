"""Execute a collection of hooks that are common to *most* CCPLAT modules.

:Path: ``ccplatcfnginlibs.hooks.CcplatCommonHooks``

This hook is an optional addition to CCPLAT modules.
It can be added to any stage to run the correct hooks for the stage.

.. rubric:: Example
.. code-block:: yaml

  pre_deploy:
    - path: ccplatcfnginlibs.hooks.CcplatCommonHooks
      args:
        validate_vpc: true  # default: false

  pre_destroy:
    - path: ccplatcfnginlibs.hooks.CcplatCommonHooks

  post_deploy:
    - path: ccplatcfnginlibs.hooks.CcplatCommonHooks

  post_destroy:
    - path: ccplatcfnginlibs.hooks.CcplatCommonHooks

"""

from __future__ import annotations

import logging
from functools import cached_property
from typing import TYPE_CHECKING, Any, Callable, ClassVar

from runway.cfngin.hooks.protocols import CfnginHookProtocol
from runway.utils import BaseModel

from ..utils import strip_leading_swa_notation, to_snake_case
from ._configure_stack_name import configure_stack_name
from ._create_custom_parameters import create_custom_parameters
from ._create_module_ssm_parameters import create_module_ssm_parameters
from ._delete_custom_parameters import delete_custom_parameters
from ._delete_module_ssm_parameters import delete_module_ssm_parameters
from ._ensure_apigateway_service_role import ensure_apigateway_service_role
from ._ensure_autoscaling_service_role import ensure_autoscaling_service_role
from ._validate_vpc_version import validate_vpc_version

if TYPE_CHECKING:
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


class CcplatCommonHooksArgs(BaseModel):
    """Args for the CcplatCommonHooks hook.

    Right now, this hook does not take any arguments directly so this class is empty.
    It needs to exist to satisfy the type checker.

    """

    enable_deprecated: bool = True
    """Enable running deprecated hooks.

    This can be disabled in newer modules where the the removal of deprecated hooks
    has already been accounted for.

    """


class CcplatCommonHooks(CfnginHookProtocol):
    """Execute a collection of hooks that are common to *most* CCPLAT stacks."""

    ARGS_PARSER = CcplatCommonHooksArgs

    POST_DEPLOY_HOOKS: ClassVar[list[Callable[..., Any]]] = []
    """Hooks run during the ``post_deploy`` stage."""

    POST_DEPLOY_HOOKS_DEPRECATED: ClassVar[list[Callable[..., Any]]] = [
        create_module_ssm_parameters,
        create_custom_parameters,
    ]
    """Deprecated hooks run during the ``post_deploy`` stage.

    These will be removed in the next major release.

    """

    POST_DESTROY_HOOKS: ClassVar[list[Callable[..., Any]]] = [
        delete_module_ssm_parameters,  # TODO (kyle): remove in v7.0.0, needed for cleanup in v6.0.0
        delete_custom_parameters,  # TODO (kyle): remove in v7.0.0, needed for cleanup in v6.0.0
    ]
    """Hooks run during the ``post_destroy`` stage."""

    PRE_DEPLOY_HOOKS: ClassVar[list[Callable[..., Any]]] = [
        validate_vpc_version,
        configure_stack_name,
        ensure_autoscaling_service_role,
        ensure_apigateway_service_role,
    ]
    """Hooks run during the ``pre_deploy`` stage."""

    PRE_DESTROY_HOOKS: ClassVar[list[Callable[..., Any]]] = [configure_stack_name]
    """Hooks run during the ``pre_destroy`` stage."""

    args: CcplatCommonHooksArgs = CcplatCommonHooksArgs()
    """Arguments passed to the hook and parsed into an object.

    Right now, this hook does not take any arguments directly.
    It needs to exist to satisfy the type checker.

    """

    def __init__(self, context: CfnginContext, **kwargs: Any) -> None:
        """Instantiate class.

        Args:
            context: CFNgin context object.
            **kwargs: Arbitrary keyword arguments.

        """
        self.args = self.ARGS_PARSER.model_validate(kwargs)
        self.ctx = context
        self._kwargs = kwargs

    @cached_property
    def kwargs(self) -> dict[str, Any]:
        """Return kwargs to pass to each hook."""
        kwargs = {
            to_snake_case(strip_leading_swa_notation(k)): v
            for k, v in self.ctx.parameters.items()
        }
        kwargs.update(self._kwargs)
        return kwargs

    @classmethod
    def log_hooks_to_run(cls, stage: str) -> None:
        """Log the hooks that will be run during the given stage.

        Args:
            stage: The stage to log the hooks for.

        """
        LOGGER.info(
            "executing CCPLAT common %s hooks: %s",
            stage,
            ", ".join(i.__name__ for i in getattr(cls, f"{stage.upper()}_HOOKS")),
        )

    def post_deploy(self) -> Any:
        """Run during the **post_deploy** stage."""
        return self.run("post_deploy")

    def post_destroy(self) -> Any:
        """Run during the **post_destroy** stage."""
        return self.run("post_destroy")

    def pre_deploy(self) -> Any:
        """Run during the **pre_deploy** stage."""
        return self.run("pre_deploy")

    def pre_destroy(self) -> Any:
        """Run during the **pre_destroy** stage."""
        return self.run("pre_destroy")

    def run(self, stage: str) -> bool:
        """Run the hooks for the given stage.

        Args:
            stage: The stage to run the hooks for.

        """
        self.log_hooks_to_run(stage)
        hooks: list[Callable[..., Any]] = getattr(self, f"{stage.upper()}_HOOKS")
        if self.args.enable_deprecated and hasattr(
            self, f"{stage.upper()}_HOOKS_DEPRECATED"
        ):
            hooks.extend(getattr(self, f"{stage.upper()}_HOOKS_DEPRECATED"))
        for hook in hooks:
            LOGGER.debug("running hook: %s", hook.__name__)
            if not hook(self.ctx, **self.kwargs):
                return False
        return True
