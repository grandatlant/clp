#!/usr/bin/env -S python3
# -*- coding = utf-8 -*-
"""combatlogparse main module.
"""

__copyright__ = 'Copyright (C) 2025 grandatlant'

__version__ = '0.0.1'

__all__ = [
    'log',
    'main',
    'parse_cli_args',
]

import sys
import logging
from argparse import ArgumentParser, Namespace
from typing import (
    Any, Optional, Final, Union,
    List, Dict, Container,
)

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from envsetup import env

log: Final[logging.Logger] = logging.getLogger(__name__)


def parse_cli_args(
    args: Optional[List[str]] = None,
    namespace: Optional[Union[Namespace, Container]] = None,
) -> Namespace:
    """Parse provided cli arguments."""
    parser: ArgumentParser = ArgumentParser(
        description = __doc__,
        epilog = __copyright__,
        #allow_abbrev = False,
    )
    parser.add_argument(
        '-v',
        '--version',
        action = 'version',
        version = f'%(prog)s {__version__}',
    )
    parser.add_argument(
        'combatlog',
        nargs = '?',
        default = env.DEFAULT_COMBATLOG,
        help = f'''name of combatlog file to parse.
        Default "{env.DEFAULT_COMBATLOG}" is script-defined.''',
    )
    return parser.parse_args(args, namespace)


##  MAIN ENTRY POINT
def main(args: Optional[List[str]] = None) -> int:
    logging.basicConfig(
        level = logging.DEBUG if __debug__ else logging.INFO,
        stream = sys.stdout,
        format = '%(levelname)s:%(name)s:%(message)s',
    )
    log.debug('%s.main(%s) start.', __name__, args)
    if args and args == sys.argv:
        args = args[1:]
    parsed: Namespace = parse_cli_args(args)
    log.debug('Parsed args: %s', parsed)
    if parsed.combatlog:
        pass
    log.debug('%s.main(%s) finish. return 0', __name__, args)
    return 0


if __name__ == '__main__':
    #assert sys.prefix != sys.base_prefix, 'Running outside venv!'
    sys.exit(main(sys.argv))
