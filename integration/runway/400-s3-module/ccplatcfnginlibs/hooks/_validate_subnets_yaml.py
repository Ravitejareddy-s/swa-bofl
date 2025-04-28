"""Validate subnets found in a yaml file.

:Path: ``ccplatcfnginlibs.hooks.validate_subnets_yaml``

"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def validate_subnets_yaml(*__args: Any, **kwargs: Any) -> bool:
    """Validate subnets.

    Keyword Args:
        allowed_subnets (Optional[List[str]]): allowable subnets.
        yaml_file (str): yaml file containing information about subnets used.
        object (str): the object containing the subnets.
        key (str): the name of the key which points to the value of the subnets.
        max_subnets (Optional[int]): maximum number of subnets used.
        **kwargs: Arbitrary keyword arguments.

    """
    if "yaml_file" not in kwargs:
        raise ValueError("Missing required arg 'yaml_file'")
    if "object" not in kwargs:
        raise ValueError("Missing required arg 'object'")
    if "key" not in kwargs:
        raise ValueError("Missing required arg 'key'")

    allowed_subnets: set[str] = set(kwargs.get("allowed_subnets", []))
    subnets = yaml.safe_load(Path(kwargs["yaml_file"]).read_bytes())[kwargs["object"]][
        kwargs["key"]
    ].split(",")
    max_subnets = int(kwargs.get("max_subnets", 0))
    if max_subnets and len(subnets) > max_subnets:
        raise ValueError(
            f"The subnets provided which are '{subnets}' must be only '{max_subnets}' "
            f"of '{allowed_subnets}'",
        )

    if not allowed_subnets or not subnets:
        raise ValueError(
            f"Missing required args allowed_subnets: '{allowed_subnets}' and "
            f"subnets : '{subnets}'",
        )

    if not allowed_subnets.issuperset(subnets):
        raise ValueError(
            f"The subnets which are '{subnets}' must be a subset of '{allowed_subnets}'"
        )
    return True
