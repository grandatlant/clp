#!/usr/bin/env -S python3 -O
# -*- coding: utf-8 -*-
"""Environment setup module.
Exports 'DotEnv' data class and 'env' Final[DotEnv] container,
initialized from .env file found.
"""

__all__ = [
    'env',
    'DotEnv',
]

from threading import RLock
from dataclasses import dataclass
from typing import (
    Any,
    Final,
    Optional,
    Union,
    ClassVar,
)

from dotenv import dotenv_values


@dataclass
class DotEnv:
    """Container for .env file values."""

    DEFAULT_COMBATLOG: str = 'WoWCombatLog.txt'
    LOG_LEVEL: Union[str, int] = 'WARNING'

    default: ClassVar[Optional[Any]] = None

    def __post_init__(self):
        # per-instance data update lock, in case of emergency
        self._lock = RLock()

    def __getattr__(self, name):
        return vars(self).get(name.upper(), self.default)

    def __contains__(self, key):
        return key in vars(self)

    def setdefault(self, name: str = 'default', value: Any = None) -> Any:
        """Like a builtin dict.setdefault method,
        Insert instance attr 'name' with a 'value'
        if attr 'name' is not yet in instance vars.
        Return the value for 'name' instance attr
        if it is in the instance vars, else default.
        Return value: value.
        """
        # getattr() not work here, __getattr__ is error-safe
        with self._lock:
            if name not in vars(self):
                setattr(self, name, value)
            return getattr(self, name, value)


## TODO: Replace dotenv.dotenv_values -> ConfigParser or toml
env: Final[DotEnv] = DotEnv(**dotenv_values())
