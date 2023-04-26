"""Basic helper functions"""

import os
from typing import Optional

from django.core.exceptions import ImproperlyConfigured


def get_env_variable(var_name, optional=False):
    """
    Retrieve an environment variable. Any failures will cause an exception
    to be thrown.
    """
    try:
        return os.environ[var_name]
    except KeyError as ex:
        if optional:
            return False
        raise ImproperlyConfigured(
            f"Error: You must set the {var_name} environment variable.",
        ) from ex


def to_bool(option: Optional[str]) -> bool:
    """
    Convert a string to a boolean.
    >>> to_bool("true")
    True
    >>> to_bool("false")
    False
    >>> to_bool("1")
    True
    >>> to_bool("0")
    False
    >>> to_bool("TRUE")
    True
    >>> to_bool(None)
    False
    """
    return option is not None and option.lower().strip() in ["true", "1"]
