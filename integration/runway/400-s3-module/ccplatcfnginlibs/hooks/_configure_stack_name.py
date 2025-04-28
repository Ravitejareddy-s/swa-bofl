"""Configure stack name.

:Path: ``ccplatcfnginlibs.hooks.configure_stack_name``

.. deprecated:: 3.0.0

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from deprecated import deprecated

if TYPE_CHECKING:
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


@deprecated(
    reason="the config should not be mutated; "
    "can break some of CFNgin's built-in functionality"
)
def configure_stack_name(
    context: CfnginContext, *__args: Any, **__kwargs: Any
) -> bool:  # cov: ignore
    """Configure stack name by optionally adding a suffix.

    Args:
        context: CFNgin context object.

    Returns:
        True if successful.

    """
    stack_postfix = context.parameters.get("stack_postfix")
    if stack_postfix:
        LOGGER.debug("stack_postfix: %s", stack_postfix)
        for stack in context.config.stacks:
            # this is potentially unsafe and should not be done which is why this hook
            # is deprecated
            if not stack.stack_name:
                stack.stack_name = f"{stack.name}-{stack_postfix}"
            elif not stack.stack_name.endswith(stack_postfix):
                stack.stack_name = f"{stack.stack_name}-{stack_postfix}"
            LOGGER.debug("stack_name: %s", stack.stack_name)
    return True
