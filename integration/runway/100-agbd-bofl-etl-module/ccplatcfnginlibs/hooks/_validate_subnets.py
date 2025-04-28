"""Validate subnets.

:Path: ``ccplatcfnginlibs.hooks.validate_subnets``

.. rubric:: Example
.. code-block:: yaml

  pre_deploy:
    - path: ccplatcfnginlibs.hooks.validate_subnets
      args:
        allowed_subnets:
          - foo
        subnets:
          - foo
        max_subnets: 1

"""

from __future__ import annotations

from typing import Any


def validate_subnets(
    *__args: Any,
    allowed_subnets: list[str],
    subnets: list[str] | str,
    max_subnets: int | None = None,
    **__kwargs: Any,
) -> bool:
    """Validate subnets.

    Args:
        allowed_subnets: allowable subnets.
        subnets: subnets used.
        max_subnets: maximum number of subnets used.

    """
    subnets_set = set(subnets if isinstance(subnets, list) else subnets.split(","))
    if max_subnets and len(subnets_set) > max_subnets:
        raise ValueError(
            f"The subnets provided which are '{subnets_set}' must be only '{max_subnets}' "
            f"of '{allowed_subnets}'"
        )
    if not allowed_subnets or not subnets_set:
        raise ValueError(
            f"Missing required args allowed_subnets : '{allowed_subnets}' and "
            f"subnets : '{subnets_set}'"
        )
    if not set(allowed_subnets).issuperset(subnets_set):
        raise ValueError(
            f"The subnets which are '{subnets_set}' must be a subset of '{allowed_subnets}'"
        )
    return True
