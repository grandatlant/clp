#!/usr/bin/env -S python3
# -*- coding = utf-8 -*-
r"""combatlogparse main module.

Reference:
https://wowpedia.fandom.com/wiki/COMBAT_LOG_EVENT
"""

__copyright__ = 'Copyright (C) 2025 grandatlant'

__version__ = '0.0.3'

__all__ = [
    'log',
    'main',
    'parse_cli_args',
    'parse_combat_log',
    'parse_combat_log_line',
    'UnitGuid',
    'UnitFlag',
    'UnitInfo',
    'CombatLogEvent',
    'EventParser',
]

import os
import sys
import datetime
import enum
import logging

from itertools import chain
from dataclasses import dataclass, field, InitVar, asdict
from argparse import ArgumentParser, Namespace

from typing import (
    ClassVar, Callable,
    Any, Optional, Final, Union,
    List, Dict, ItemsView, Container,
)

#import numpy as np
import pandas as pd
#from matplotlib import pyplot as plt

from envsetup import env

log: Final[logging.Logger] = logging.getLogger(__name__)
log.setLevel(logging.DEBUG if __debug__ else env.LOG_LEVEL)


# Helper classes

class IntEnumParser(int, enum.Enum):
    """IntEnum base class for parsing purpose.
    Contains shared methods for int enum parsing.
    """
    @classmethod
    def from_literal(
        cls,
        literal: Union[str, bytes, bytearray] = '-1',
        base: int = 0,
    ) -> object:
        """Create enum member from int literal (usually hex)."""
        return cls(int(literal, base))


class IntFlagParser(enum.IntFlag):
    """IntFlag base class for parsing purpose.
    Contains shared methods for int flag parsing.
    """
    @classmethod
    def from_literal(
        cls,
        literal: Union[str, bytes, bytearray] = '0',
        base: int = 0,
    ) -> object:
        """Create flag member from int literal (usually hex)."""
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
    COMBOPOINTS = 4 # or pet happiness, idk
    RUNES = 5
    RUNIC_POWER = 6


class UnitFlag(IntFlagParser):
    """Unit flags parsing enum."""
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
    SPECIAL_UNKNOWN_FLAG_0x10000000 = 0x10000000 # Not in reference!
    SPECIAL_UNKNOWN_FLAG_0x20000000 = 0x20000000 # Not in reference!
    SPECIAL_UNKNOWN_FLAG_0x40000000 = 0x40000000 # Not in reference!
    NONE = 0x80000000
    #UNIT_SPECIAL_MASK = 0xFFFF0000


class SchoolFlag(IntFlagParser):
    """Spell School parsing enum."""
    # Clean Schools
    PHYSICAL = 0x01
    HOLY = 0x02
    FIRE = 0x04
    NATURE = 0x08
    FROST = 0x10
    SHADOW = 0x20
    ARCANE = 0x40
    SCHOOL_UNKNOWN_FLAG = 0x80 # Not in reference!
    # Double Schools
    # not today tho...


# Main external interface

class UnitGuid(str):
    """UnitGuid class with ability to try form int value (defaults to 0)."""
    def __int__(self):
        val = int(0)
        try:
            val = int(self, base=0)
        except ValueError as exc:
            log.warning('UnitGuid.__int__(%s) failed with %r.', self, exc)
        return val
    
    def to_int(self) -> int: return self.__int__()


@dataclass
class UnitInfo():
    """Describes Unit info in a single Combat Log record."""
    guid_str: InitVar[str] = ''
    guid: UnitGuid = field(init=False, default_factory=UnitGuid)
    name: str = ''
    flags_str: InitVar[str] = '0'
    flags: UnitFlag = field(init=False, default_factory=UnitFlag.from_literal)
    
    def __post_init__(
        self,
        guid_str: str,
        flags_str: str,
    ) -> None:
        self.guid = UnitGuid(guid_str)
        self.flags = UnitFlag.from_literal(flags_str)
        
    def dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class CombatLogEvent():
    """Describes single Combat Log record."""
    timestamp: float
    name: str
    source: UnitInfo = field(default_factory=UnitInfo)
    dest: UnitInfo = field(default_factory=UnitInfo)
    params: List[str] = field(default_factory=list)
    
    @classmethod
    def from_log_line(cls, line: str) -> object:
        """Constructor for WoWCombatLog.txt parsing line by line."""
        # Example WoW 3.3.5 combat log line:
        # 4/21 20:19:34.123  SPELL_DAMAGE,Player-1-00000001,"Playername",0x511,Creature-0-0000-00000-00000-0000000000,"Training Dummy",0x10a48,12345,"Fireball",0x4,Training Dummy,0,0,1234,0,0,0,nil,nil,nil
        datetimestr, eventstr = line.strip().split('  ', 1)
        datetimestr, milliseconds = datetimestr.rsplit('.', 1)
        ##TODO: Think about reading log file modification date to get year...
        yearstr = '1970' # yes, just EPOCH year for smaller numbers
        datetimeobj = datetime.datetime.strptime(
            f'{yearstr} {datetimestr}',
            '%Y %m/%d %H:%M:%S',
        ) + datetime.timedelta(milliseconds=int(milliseconds))
        timestamp = datetimeobj.timestamp()
        # Event descriprion part
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
        return cls(
            timestamp,
            event_name,
            UnitInfo(*event_source),
            UnitInfo(*event_dest),
            event_params,
        )
    
    def dict(self) -> Dict[str, Any]: return asdict(self)


def is_not_nil(arg: str):
    return (arg != 'nil')


@dataclass
class EventParser():
    """Class for parsing CombatLogEvent for analyse."""
    event: Union[CombatLogEvent, str]
    params: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.event, CombatLogEvent):
            self.params = self.event.params.copy()
            
    # Prefix parsers
    @staticmethod
    def SpellParser():
        return {
            'spellId': str,
            'spellName': str,
            'spellSchool': SchoolFlag.from_literal,
        }
    @staticmethod
    def EnvParser():
        return {
            'environmentalType': str,
        }
    
    # Suffix parsers
    @staticmethod
    def DamageParser():
        return {
            'amount': int,
            'overkill': int,
            'school': SchoolFlag.from_literal,
            'resisted': int,
            'blocked': int,
            'absorbed': int,
            'critical': is_not_nil,
            'glancing': is_not_nil,
            'crushing': is_not_nil,
            'isOffHand': is_not_nil,
        }
    @staticmethod
    def MissParser():
        return {
            'missType': str,
            'isOffHand': str,
            'amountMissed': int,
        }
    @staticmethod
    def HealParser():
        return {
            'amount': int,
            'overhealing': int,
            'absorbed': int,
            'critical': is_not_nil,
        }
    @staticmethod
    def EnergizeParser():
        return {
            'amount': int,
            'powerType': PowerType.from_literal,
        }
    @staticmethod
    def DrainParser():
        return {
            'amount': int,
            'powerType': PowerType.from_literal,
            'extraAmount': int,
        }
    @staticmethod
    def SpellBlockParser():
        return {
            'extraSpellID': str,
            'extraSpellName': str,
            'extraSchool': SchoolFlag.from_literal,
            'auraType': str,
        }
    @staticmethod
    def ExtraAttackParser():
        return {
            'amount': int,
        }
    @staticmethod
    def AuraParser():
        return {
            'auraType': str,
            'amount': int,
            'auraExtra1': str,# Not sure this column 
            'auraExtra2': str,# Not sure this column 
        }
    @staticmethod
    def AuraDoseParser():
        return {
            'auraType': str,
            'powerType': PowerType.from_literal,
        }
    @staticmethod
    def AuraBrokenParser():
        return {
            'extraSpellID': str,
            'extraSpellName': str,
            'extraSchool': SchoolFlag.from_literal,
            'auraType': str,
        }
    @staticmethod
    def CastFailedParser():
        return {
            'failedType': str,
        }
    
    # Special parsers
    @staticmethod
    def EnchantParser():
        return {
            'spellName': str,
            'itemID': str,
            'itemName': str,
        }
    
    # Combo-parsers
    @property
    def ev_prefix(self):
        return {
            'SWING': {},
            'RANGE': self.SpellParser(),
            'SPELL': self.SpellParser(),
            'SPELL_PERIODIC': self.SpellParser(),
            'SPELL_BUILDING': self.SpellParser(),
            'ENVIRONMENTAL': self.EnvParser(),
        }
    @property
    def ev_suffix(self):
        return {
            '_DAMAGE': self.DamageParser(),
            '_MISSED': self.MissParser(),
            '_HEAL': self.HealParser(),
            '_HEAL_ABSORBED': {},
            '_ABSORBED': {},
            '_ENERGIZE': self.EnergizeParser(),
            '_DRAIN': self.DrainParser(),
            '_LEECH': self.DrainParser(),
            '_INTERRUPT': self.SpellBlockParser(),
            '_DISPEL': self.SpellBlockParser(),
            '_DISPEL_FAILED': self.SpellBlockParser(),
            '_STOLEN': self.SpellBlockParser(),
            '_EXTRA_ATTACKS': self.ExtraAttackParser(),
            '_AURA_APPLIED': self.AuraParser(),
            '_AURA_REMOVED': self.AuraParser(),
            '_AURA_APPLIED_DOSE': self.AuraDoseParser(),
            '_AURA_REMOVED_DOSE': self.AuraDoseParser(),
            '_AURA_REFRESH': self.AuraDoseParser(),
            '_AURA_BROKEN': self.AuraParser(),
            '_AURA_BROKEN_SPELL': self.AuraBrokenParser(),
            '_CAST_START': {},
            '_CAST_SUCCESS': {},
            '_CAST_FAILED': self.CastFailedParser(),
            '_INSTAKILL': {},
            '_DURABILITY_DAMAGE': {},
            '_DURABILITY_DAMAGE_ALL': {},
            '_CREATE': {},
            '_SUMMON': {},
            '_RESURRECT': {},
        }
    @property
    def sp_event(self):
        return {
            'DAMAGE_SPLIT': (self.SpellParser(), self.DamageParser()),
            'DAMAGE_SHIELD': (self.SpellParser(), self.DamageParser()),
            'DAMAGE_SHIELD_MISSED': (self.SpellParser(), self.MissParser()),
            'ENCHANT_APPLIED': (self.EnchantParser(), {}),
            'ENCHANT_REMOVED': (self.EnchantParser(), {}),
            'PARTY_KILL': ({}, {}),
            'UNIT_DIED': ({}, {}),
            'UNIT_DESTROYED': ({}, {}),
            'UNIT_DISSIPATES': ({}, {}),
        }
    
    def parse_params(self) -> dict:
        d = dict()
        if isinstance(self.event, CombatLogEvent):
            event = self.event.name
            d.update(self.event.dict())
        else:
            event = str(self.event)
        # Search for longest prefix
        prefix_fields, suffix_fields = {}, {}
        prefix_match = []
        for k in self.ev_prefix.keys():
            if event.startswith(k):
                prefix_match.append(k)
        if prefix_match:
            prefix = max(prefix_match, key=len)
            prefix_fields = self.ev_prefix.get(prefix)
            suffix = event[len(prefix):]
            suffix_fields = self.ev_suffix.get(suffix, {})
        else:
            # No prefix found. Search special events
            for (k, psrs) in self.sp_event.items():
                if event == k:
                    (prefix_fields, suffix_fields) = psrs
                    break
        # Start popping params one by one in order saved in fields
        for name, psr in chain(prefix_fields.items(), suffix_fields.items()):
            if name in d:
                raise KeyError(f'Duplicate parse attempt for field {name}.')
            d[name] = psr(self.pop_param())
        # Check if some params left
        d['params'] = self.params
        if self.params:
            log.warning(
                'EventParser.parse_params(%s) left params %s unparsed.',
                self,
                self.params,
            )
        return d

    def pop_param(self):
        val = ''
        try:
            val = self.params.pop(0)
        except IndexError as exc:
            log.warning('EventParser.pop_param(%s) failed with %r.', self, exc)
        return val


# Helper functions

def parse_combat_log_line(
    line: str,
) -> Dict[str, Any]:
    #return CombatLogEvent.from_log_line(line).dict()
    return EventParser(CombatLogEvent.from_log_line(line)).parse_params()


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
        '-v', '--version',
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
