"""Hook helpers."""

from __future__ import annotations

import importlib
import logging
import sys
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from runway.context import CfnginContext

LOGGER = logging.getLogger(__name__)


def execute_hooks(
    hook_list: list[str], context: CfnginContext, *__args: Any, **kwargs: Any
) -> bool:
    """Execute a list of hooks.

    Args:
        hook_list: List of hooks to execute.
        context: CFNgin context object.
        **kwargs: Arbitrary keyword arguments.

    """
    successful = True
    for hook_path in hook_list:
        LOGGER.info("Executing hook %s", hook_path)
        try:
            method = load_method_from_path(hook_path)
            successful = method(context=context, **kwargs)
            if not successful:
                LOGGER.error("Hook %s returned a False response", hook_path)
        except Exception:
            LOGGER.exception("Error occurred while calling hook %s", hook_path)
            successful = False
        if not successful:
            break

    return successful


def load_method_from_path(hook_path: str) -> Callable[..., Any]:
    """Load method from path.

    Args:
        hook_path: Path to the method to load.

    Returns:
        Method loaded from path.

    """
    module_path, object_name = hook_path.rsplit(".", 1)
    importlib.import_module(module_path)
    return getattr(sys.modules[module_path], object_name)
