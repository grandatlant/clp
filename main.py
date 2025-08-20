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
    'parse_combat_log',
    'parse_combat_log_line',
]

import os
import sys
import time
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
log.setLevel(logging.DEBUG if __debug__ else env.LOG_LEVEL)


def parse_combat_log_line(
    line: str,
) -> Optional[Dict[str, Any]]:
    # Example WoW 3.3.5 combat log line:
    # 4/21 20:19:34.123  SPELL_DAMAGE,Player-1-00000001,"Playername",0x511,Creature-0-0000-00000-00000-0000000000,"Training Dummy",0x10a48,12345,"Fireball",0x4,Training Dummy,0,0,1234,0,0,0,nil,nil,nil
    # DateTime and EventInfo
    parts = line.strip().split('  ', 1)
    if len(parts) < 2:
        return None
    timestr, eventstr = parts
    time_parts = timestr.split('.')
    time_s = (
        #time.mktime(#make seconds from time_tuple
            time.strptime(time_parts[0], '%m/%d %H:%M:%S')
        #) + float('0.%s' % time_parts[1])#+fractions of seconds
    )
    event_parts = eventstr.split(',')
    event_name = event_parts[0].strip()
    event_source = [
        x.strip().strip('"')
        for x in event_parts[1:4]
    ]
    event_dest = [
        x.strip().strip('"')
        for x in event_parts[4:7]
    ]
    event_params = [
        x.strip().strip('"')
        for x in event_parts[7:]
    ]
    return {
        'timestr': timestr,
        'event': event_name,
        'source': event_source,
        'dest': event_dest,
        'params': event_params,
    }


def parse_combat_log(
    combatlog: str,
) -> List[Dict[str, Any]]:
    records = []
    with open(combatlog, encoding='utf-8', errors='ignore') as f:
        for line in f:
            if not line.strip():
                continue
            parsed = parse_combat_log_line(line)
            if parsed:
                records.append(parsed)
                #yield parsed
    return records


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
    return parser.parse_args(args, namespace) # type: ignore


##  MAIN ENTRY POINT
def main(args: Optional[List[str]] = None) -> int:
    logging.basicConfig(
        level = logging.DEBUG if __debug__ else env.LOG_LEVEL,
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
    if df is not None:
        for group in df.groupby('event'):
            print(group)
##            group[1].to_json(
##                '(%s).%s.json' % (group[0], parsed.combatlog),
##                orient='records',
##                indent=4,
##            )
    log.debug('%s.main(%s) finish. return 0', __name__, args)
    return 0


if __name__ == '__main__':
    #assert sys.prefix != sys.base_prefix, 'Running outside venv!'
    if flag := getattr(sys, 'ps1', sys.flags.interactive):
        print('(interactive: %s)' % flag)
        print(dir())
    else:
        sys.exit(main(sys.argv))
