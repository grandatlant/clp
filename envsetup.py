#!/usr/bin/env -S python3 -O
# -*- coding = utf-8 -*-
"""Environment setup module.
Exports 'DotEnv' pydantic model class and 'env' Final container, 
initialized from .env file found.
"""

__all__ = [
    'env',
    'DotEnv',
]

import pydantic
from dotenv import dotenv_values


class DotEnv(pydantic.BaseModel):
    """Container for .env file values."""
    DEFAULT_COMBATLOG: str = 'combatlog.txt'

    
## TODO: Replace dotenv.dotenv_values -> ConfigParser
env: DotEnv = DotEnv(**dotenv_values())


##  MAIN ENTRY POINT
def main(args=None):
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
