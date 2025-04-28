"""Utilities."""

import re

TO_SNAKE_CASE_PATTERNS = [
    re.compile(r"(.)([A-Z][a-z]+)"),
    re.compile(r"([a-z0-9])([A-Z])"),
]
"""Compiled patterns for ``to_snake_case`` for improved performance."""


def format_name(name: str) -> str:
    """Format name.

    Please update the macros in
    https://gitlab-tools.swacorp.com/swa-common/ccp/macros/-/blob/master/macros/macros.jinja
    whenever an update is made to the macro functions in this file.

    Args:
        name: Name to format.

    Returns:
        Formatted name.

    """
    for special_char in [
        "\\",
        "`",
        "*",
        "_",
        "{",
        "}",
        "[",
        "]",
        "(",
        ")",
        ">",
        "#",
        "+",
        "-",
        ".",
        "!",
        "$",
        "'",
        "/",
        "^",
        "@",
        " ",
    ]:
        if special_char in name:
            name = name.replace(special_char, "")
    return name.capitalize()[:91]


def strip_leading_swa_notation(word: str) -> str:
    """Strip leading notation added to SWA variables from a string.

    ..rubric:: Example

    - "oSomething" => "Something".
    - "pSomething" => "Something".
    - "vSomething" => "Something".

    """
    return re.sub(r"^(o|p|v)(?=[A-Z])(.*)", r"\2", word)


def to_snake_case(word: str) -> str:
    """Convert a string to snake case."""
    word.replace("__", "_")
    for pattern in TO_SNAKE_CASE_PATTERNS:
        word = pattern.sub(r"\1_\2", word)
    return word.lower()
