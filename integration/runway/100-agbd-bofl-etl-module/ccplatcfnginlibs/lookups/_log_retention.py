"""Get log retention in days for an environment.

:Query Syntax: ``<environment>``

.. rubric:: Example
.. code-block:: yaml

    lookups:
      log_retention: ccplatcfnginlibs.lookups.LogRetentionLookup

    stacks:
      - name: example-stack
        variables:
          foo: ${log_retention ${environment}}
          bar: ${log_retention dev}

"""

from __future__ import annotations

from enum import IntEnum
from typing import Any, ClassVar

from runway.lookups.handlers.base import LookupHandler


class EnvironmetLogRetention(IntEnum):
    """Log retention in days by environment tier."""

    LAB = 1
    DEV = 5
    QA = 30
    PROD = 90


class LogRetentionLookup(LookupHandler[Any]):
    """Get log retention in days for an environment."""

    TYPE_NAME: ClassVar[str] = "log_retention"

    @classmethod
    def handle(
        cls,
        value: str,
        *__args: Any,
        **__kwargs: Any,
    ) -> int:
        """Get CloudWatch retention setting."""
        env, _args = cls.parse(value)
        return EnvironmetLogRetention[env.upper()].value
