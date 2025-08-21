#!/usr/bin/env -S python3
# -*- coding = utf-8 -*-
r"""combatlogparse main module.

Reference:
https://wowpedia.fandom.com/wiki/COMBAT_LOG_EVENT
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
import enum
import logging

from argparse import ArgumentParser, Namespace
from typing import (
    Any, Optional, Final, Union,
    List, Dict, Container,
)

#import numpy as np
import pandas as pd
#from matplotlib import pyplot as plt

from envsetup import env

log: Final[logging.Logger] = logging.getLogger(__name__)
log.setLevel(logging.DEBUG if __debug__ else env.LOG_LEVEL)

# Helper classes

class _AttrHolder:
    """Attribute holder base class with human-readable repr."""
    __slots__ = '__dict__',
    def __repr__(self):
        type_name = type(self).__name__
        arg_strings = []
        star_args = {}
        for arg in self._get_args_():
            arg_strings.append(repr(arg))
        for name, value in self._get_kwargs_():
            if name.isidentifier():
                arg_strings.append('%s=%r' % (name, value))
            else:
                star_args[name] = value
        if star_args:
            arg_strings.append('**%s' % repr(star_args))
        return '%s(%s)' % (type_name, ', '.join(arg_strings))
    def _get_args_(self):
        return []
    def _get_kwargs_(self):
        return sorted(self.__dict__.items())


class StrEnumParser(str, enum.Enum):
    """StrEnum base class for parsing purpose."""


class IntEnumParser(int, enum.Enum):
    """IntEnum base class for parsing purpose.
    Contains shared methods for int enum parsing.
    """
    @classmethod
    def from_literal(
        cls,
        literal: Union[str, bytes, bytearray],
        base: int = 0,
    ):
        """Create enum member from int literal (usually hex)."""
        return cls(int(literal, base))


class IntFlagParser(enum.IntFlag):
    """IntFlag base class for parsing purpose.
    Contains shared methods for int flag parsing.
    """
    @classmethod
    def from_literal(
        cls,
        literal: Union[str, bytes, bytearray],
        base: int = 0,
    ):
        """Create enum member from int literal (usually hex)."""
        return cls(int(literal, base))

# Concrete Enum classes used for log parsing.

class PowerType(IntEnumParser):
    """Power type parsing enum."""
    HEALTH = -2
    NONE = -1
    MANA = 0
    RAGE = 1
    FOCUS = 2
    ENERGY = 3
    COMBOPOINTS = 4
    RUNES = 5
    RUNIC_POWER = 6


class UnitFlag(IntFlagParser):
    # Affiliation
    AFFILIATION_MINE = 0x00000001
    AFFILIATION_PARTY = 0x00000002
    AFFILIATION_RAID = 0x00000004
    AFFILIATION_OUTSIDER = 0x00000008
    #UNIT_AFFILIATION_MASK = 0x0000000F
    # Reaction
    REACTION_FRIENDLY = 0x00000010
    REACTION_NEUTRAL = 0x00000020
    REACTION_HOSTILE = 0x00000040
    REACTION_UNKNOWN_FLAG = 0x00000080 # Not in reference!
    #UNIT_REACTION_MASK = 0x000000F0
    # Control
    CONTROL_PLAYER = 0x00000100
    CONTROL_NPC = 0x00000200
    #UNIT_CONTROL_MASK = 0x00000300
    # Type
    TYPE_PLAYER = 0x00000400
    TYPE_NPC = 0x00000800
    TYPE_PET = 0x00001000
    TYPE_GUARDIAN = 0x00002000
    TYPE_OBJECT = 0x00004000
    TYPE_UNKNOWN_FLAG = 0x00008000 # Not in reference!
    #UNIT_TYPE_MASK = 0x0000FC00
    # Special cases (non-exclusive)
    TARGET = 0x00010000
    FOCUS = 0x00020000
    MAINTANK = 0x00040000
    MAINASSIST = 0x00080000
    RAIDTARGET1 = 0x00100000
    RAIDTARGET2 = 0x00200000
    RAIDTARGET3 = 0x00400000
    RAIDTARGET4 = 0x00800000
    RAIDTARGET5 = 0x01000000
    RAIDTARGET6 = 0x02000000
    RAIDTARGET7 = 0x04000000
    RAIDTARGET8 = 0x08000000
    RAIDTARGET_OTHER = 0x10000000 # Not in reference!
    NONE = 0x80000000
    #UNIT_SPECIAL_MASK = 0xFFFF0000


class SchoolFlag(IntFlagParser):
    # Clean Schools
    PHYSICAL = 0x01
    HOLY = 0x02
    FIRE = 0x04
    NATURE = 0x08
    FROST = 0x10
    SHADOW = 0x20
    ARCANE = 0x40
    # Double Schools
    # not today tho...


class EventPrefix(StrEnumParser):
    SWING = 'SWING'
    RANGE = 'RANGE'
    SPELL = 'SPELL'
    SPELL_PERIODIC = 'SPELL_PERIODIC'
    SPELL_BUILDING = 'SPELL_BUILDING'
    ENVIRONMENTAL = 'ENVIRONMENTAL'


class EventSuffix(StrEnumParser):
    _DAMAGE = '_DAMAGE'
    _MISSED = '_MISSED'
    _HEAL = '_HEAL'
    _HEAL_ABSORBED = '_HEAL_ABSORBED'
    _ABSORBED = '_ABSORBED'
    _ENERGIZE = '_ENERGIZE'
    _DRAIN = '_DRAIN'
    _LEECH = '_LEECH'
    _INTERRUPT = '_INTERRUPT'
    _DISPEL = '_DISPEL'
    _DISPEL_FAILED = '_DISPEL_FAILED'
    _STOLEN = '_STOLEN'
    _EXTRA_ATTACKS = '_EXTRA_ATTACKS'
    _AURA_APPLIED = '_AURA_APPLIED'
    _AURA_REMOVED = '_AURA_REMOVED'
    _AURA_APPLIED_DOSE = '_AURA_APPLIED_DOSE'
    _AURA_REMOVED_DOSE = '_AURA_REMOVED_DOSE'
    _AURA_REFRESH = '_AURA_REFRESH'
    _AURA_BROKEN = '_AURA_BROKEN'
    _AURA_BROKEN_SPELL = '_AURA_BROKEN_SPELL'
    _CAST_START = '_CAST_START'
    _CAST_SUCCESS = '_CAST_SUCCESS'
    _CAST_FAILED = '_CAST_FAILED'
    _INSTAKILL = '_INSTAKILL'
    _DURABILITY_DAMAGE = '_DURABILITY_DAMAGE'
    _DURABILITY_DAMAGE_ALL = '_DURABILITY_DAMAGE_ALL'
    _CREATE = '_CREATE'
    _SUMMON = '_SUMMON'
    _RESURRECT = '_RESURRECT'


class SpecialEvent(StrEnumParser):
    # Combined Events
    DAMAGE_SPLIT = EventPrefix.SPELL + EventSuffix._DAMAGE#: (SpellParser(), DamageParser()),
    DAMAGE_SHIELD = EventPrefix.SPELL + EventSuffix._DAMAGE#: (SpellParser(), DamageParser()),
    DAMAGE_SHIELD_MISSED = EventPrefix.SPELL + EventSuffix._MISSED#: (SpellParser(), MissParser()),
    # Special Parameters
    ENCHANT_APPLIED = 'ENCHANT_APPLIED'#: (EnchantParser(), VoidSuffixParser()),
    ENCHANT_REMOVED = 'ENCHANT_REMOVED'#: (EnchantParser(), VoidSuffixParser()),
    PARTY_KILL = 'PARTY_KILL'#: (VoidParser(), VoidSuffixParser()),
    UNIT_DIED = 'UNIT_DIED'#: (VoidParser(), VoidSuffixParser()),
    UNIT_DESTROYED = 'UNIT_DESTROYED'#: (VoidParser(), VoidSuffixParser()),
    UNIT_DISSIPATES = 'UNIT_DISSIPATES'


class CombatLogEvent(_AttrHolder):
    """."""
    def __new__(cls, *args, **kwargs):
        """Default constructor."""
        obj = super().__new__(*args, **kwargs)
        return obj

    


# Helper functions

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
        print(dir())
    else:
        sys.exit(main(sys.argv))
