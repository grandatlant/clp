#!/usr/bin/env -S python3
# -*- coding = utf-8 -*-
r"""combatlogparse main module.

Reference:
https://wowpedia.fandom.com/wiki/COMBAT_LOG_EVENT
"""

__copyright__ = 'Copyright (C) 2025 grandatlant'


import os
import sys
import logging

from argparse import ArgumentParser, Namespace

from typing import (
    Final, Optional, Union, 
    List, Container,
)

import numpy as np
import pandas as pd

from clp import (__version__, parse_combat_log)
from envsetup import env

DEFAULT_COMBATLOG = env.DEFAULT_COMBATLOG
LOG_LEVEL = env.LOG_LEVEL

log: Final[logging.Logger] = logging.getLogger(__name__)
log.setLevel(logging.DEBUG if __debug__ else LOG_LEVEL)


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
        '-v', '--version',
        action = 'version',
        version = f'%(prog)s {__version__}',
    )
    parser.add_argument(
        'combatlog',
        nargs = '?',
        default = DEFAULT_COMBATLOG,
        help = f'''name of combatlog file to parse.
        Default "{DEFAULT_COMBATLOG}" is script-defined.''',
    )
    return parser.parse_args(args, namespace) # type: ignore


##  MAIN ENTRY POINT
def main(args: Optional[List[str]] = None) -> int:
    logging.basicConfig(
        level = logging.DEBUG if __debug__ else LOG_LEVEL,
        stream = sys.stdout,
        format = '%(levelname)s:%(name)s:%(message)s',
    )
    log.debug('%s.main(%s) start.', __name__, args)
    if args and args == sys.argv:
        args = args[1:]
    parsed: Namespace = parse_cli_args(args)
    log.debug('Parsed cli args: %s', parsed)
    df = None
    if parsed and parsed.combatlog:
        if os.path.exists(parsed.combatlog):
            if os.path.isfile(parsed.combatlog):
                df = pd.DataFrame(parse_combat_log(parsed.combatlog))
                #print(df)
                df.to_json(
                    '%s.json' % parsed.combatlog,
                    orient='records',
                    indent=4,
                )
    '''
    if df is not None:
        for group in df.groupby('event'):
            #print(group)
            group[1].to_json(
                '(%s).%s.json' % (group[0], parsed.combatlog),
                orient='records',
                indent=4,
            )
    '''
    log.debug('%s.main(%s) finish. return 0', __name__, args)
    return 0


if __name__ == '__main__':
    #assert sys.prefix != sys.base_prefix, 'Running outside venv!'
    if flag := getattr(sys, 'ps1', sys.flags.interactive):
        print('(interactive: %s)' % flag)
        from pprint import pprint as pp
        cldf = pd.DataFrame(parse_combat_log('WoWCombatLog.txt'))
        pp(dir(), compact=True, indent=4)
    else:
        sys.exit(main(sys.argv))
