#!/usr/bin/env -S python3
# -*- coding = utf-8 -*-
r"""combatlogparse main module.

Reference:
https://wowpedia.fandom.com/wiki/COMBAT_LOG_EVENT
"""

__copyright__ = 'Copyright (C) 2025 grandatlant'

__version__ = '0.0.4'

__all__ = [
    # Shared objects
    'log',
    'env',
    # Functions
    'main',
    'parse_cli_args',
    'parse_combat_log',
    'parse_combat_log_line',
    # Helper classes
    'ParsingError',
    # str enums
    'StrEnumParser',
    'EnvironmentalType',
    'MissType',
    'AuraType',
    'FailedType',
    # int enums
    'IntEnumParser',
    'PowerType',
    # int flags
    'IntFlagParser',
    'SchoolFlag',
    'UnitFlag',
    # data containers
    'UnitGuid',
    'UnitInfo',
    # Parsing classes
    'CombatLogEvent',
    'EventParamsParser',
]

import os
import sys
import datetime
import re
import enum
import logging

from itertools import chain
from dataclasses import dataclass, field, InitVar, asdict
from argparse import ArgumentParser, Namespace

from typing import (
    Final, ClassVar, Callable,
    Any, Optional, Union,
    Tuple, List, Dict,
    ItemsView, Container,
)

import numpy as np
import pandas as pd

from envsetup import env

log: Final[logging.Logger] = logging.getLogger(__name__)
log.setLevel(logging.DEBUG if __debug__ else env.LOG_LEVEL)


# Helper casters for parsing

def is_not_nil(arg: str) -> bool:
    """True if (arg != 'nil'), False otherwise."""
    return (arg != 'nil')


# Helper classes

class ParsingError(Exception):
    """Exception type for internal use."""


class ParsingLookupError(ParsingError, LookupError):
    """ParsingError with LookupError base."""


class StrEnumParser(str, enum.Enum):
    """StrEnum base class for parsing purpose.
    Contains shared methods for str enum parsing.
    """
    @classmethod
    def _missing_(cls, value):
        """A classmethod for looking up values not found in cls."""
        log.warning('StrEnumParser %r missing value %r.', cls, value)
        return cls._create_pseudo_member_(value)

    @classmethod
    def _create_pseudo_member_(cls, value):
        """Create a new parsed member."""
        value = str(value)
        pseudo = cls._value2member_map_.get(value, None)
        if pseudo is None:
            # construct a singleton enum pseudo-member
            pseudo = str.__new__(cls, value)
            pseudo._name_ = cls.value_to_name(value)
            pseudo._value_ = value
            # use setdefault in case another thread already created value
            pseudo = cls._value2member_map_.setdefault(value, pseudo)
        return pseudo

    @staticmethod
    def value_to_name(value):
        """Replace all invalid identifier chars in str(value) with '_'
        and upper() transform to use it as Enum member name.
        """
        name = re.sub(r'\W+|^(?=\d)','_', str(value)).upper()
        if not name.isidentifier():
            raise ValueError('Value %r can not be transformed to '
                             'a valid Enum member name.' % value)
        return name


class IntEnumParser(int, enum.Enum):
    """IntEnum base class for parsing purpose.
    Contains shared methods for int enum parsing.
    """
    @classmethod
    def from_literal(
        cls,
        # defaults '-1' as we think '0' is valid enum member for indexing
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

class EnvironmentalType(StrEnumParser):
    """Environmental Type parsing enum."""
    DROWNING = 'DROWNING'
    FALLING = 'FALLING'
    FATIGUE = 'FATIGUE'
    FIRE = 'FIRE'
    LAVA = 'LAVA'
    SLIME = 'SLIME'


class MissType(StrEnumParser):
    """Miss Type parsing enum."""
    MISS = 'MISS'
    DODGE = 'DODGE'
    PARRY = 'PARRY'
    IMMUNE = 'IMMUNE'
    ABSORB = 'ABSORB'
    BLOCK = 'BLOCK'
    DEFLECT = 'DEFLECT'
    EVADE = 'EVADE'
    REFLECT = 'REFLECT'
    RESIST = 'RESIST'


class AuraType(StrEnumParser):
    """Aura Type parsing enum."""
    BUFF = 'BUFF'
    DEBUFF = 'DEBUFF'


class FailedType(StrEnumParser):
    """Failed Type parsing enum."""
    INTERRUPTED = 'Interrupted'
    NOT_RECOVERED = 'Not yet recovered'
    NO_TARGET = 'No target'
    INVALID_TARGET = 'Invalid target'
    ITEM_NOT_READY = 'Item is not ready yet'
    ACTION_IN_PROGRESS = 'Another action is in progress'
    OUT_OF_RANGE = 'Out of range'
    # and much much more
    # better use str instead this enum
    # or be happy with _create_pseudo_member_ produced


class PowerType(IntEnumParser):
    """Power Type parsing enum."""
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
    """Unit Flags parsing enum."""
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
    """UnitGuid str subclass with ability
    to try to form int value (defaults to 0).
    """
    def __int__(self):
        val = int(0)
        try:
            val = int(self, base=0)
        except ValueError as exc:
            log.exception(
                'UnitGuid.__int__(%s) failed with %r.',
                self,
                exc,
            )
        return val
    
    def to_int(self) -> int:
        return self.__int__()


@dataclass
class UnitInfo():
    """Describes Unit info in a single Combat Log record."""
    guid_str: InitVar[str] = ''
    guid: UnitGuid = field(init=False)
    name: str = ''
    flags_str: InitVar[str] = '0'
    flags: UnitFlag = field(init=False)
    
    def __post_init__(
        self,
        guid_str: str,
        flags_str: str,
    ) -> None:
        self.guid = UnitGuid(guid_str)
        self.flags = UnitFlag.from_literal(flags_str)
        
    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CombatLogEvent():
    """Describes single Combat Log record."""
    timestamp: float
    name: str
    
    #source: UnitInfo = field(default_factory=UnitInfo)
    sourceID_str: InitVar[str] = ''
    sourceID: UnitGuid = field(init=False)
    sourceName: str = ''
    sourceFlags_str: InitVar[str] = '0'
    sourceFlags: UnitFlag = field(init=False)
    
    #dest: UnitInfo = field(default_factory=UnitInfo)
    destID_str: InitVar[str] = ''
    destID: UnitGuid = field(init=False)
    destName: str = ''
    destFlags_str: InitVar[str] = '0'
    destFlags: UnitFlag = field(init=False)
    
    params: List[str] = field(default_factory=list)

    def __post_init__(
        self,
        sourceID_str,
        sourceFlags_str,
        destID_str,
        destFlags_str,
    ) -> None:
        self.sourceID = UnitGuid(sourceID_str)
        self.sourceFlags = UnitFlag.from_literal(sourceFlags_str)
        self.destID = UnitGuid(destID_str)
        self.destFlags = UnitFlag.from_literal(destFlags_str)
        
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
            #UnitInfo(*event_source),
            *event_source,
            #UnitInfo(*event_dest),
            *event_dest,
            event_params,
        )
    
    def dict(self) -> Dict[str, Any]:
        return asdict(self)


# Type hints for EventParamsParser methods
FieldsDict = Dict[str, Callable[[str], Any]]
ParserDict = Dict[str, FieldsDict]
TwinParserDict = Dict[str, Tuple[FieldsDict, FieldsDict]]

@dataclass
class EventParamsParser():
    """Class for parsing CombatLogEvent for analyse."""
    event: Union[CombatLogEvent, str]
    params: List[str] = field(default_factory=list)
    parsed: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.event, CombatLogEvent):
            self.params = self.event.params.copy()

    #TemplateParser: ClassVar[FieldsDict] = {
    #    'param1Name': constructor_from_str,
    #    'param2Name': callable_caster_from_str_to_parsed_value,
    #}
    
    # Prefix parsers
    SpellParser: ClassVar[FieldsDict] = {
        'spellId': int,
        'spellName': str,
        'spellSchool': SchoolFlag.from_literal,
    }
    EnvParser: ClassVar[FieldsDict] = {
        'environmentalType': EnvironmentalType,
    }
    
    # Suffix parsers
    DamageParser: ClassVar[FieldsDict] = {
        'amount': int,
        'overkill': int,
        'school': SchoolFlag.from_literal,
        'resisted': int,
        'blocked': int,
        'absorbed': int,
        'critical': is_not_nil,
        'glancing': is_not_nil,
        'crushing': is_not_nil,
    }
    MissParser: ClassVar[FieldsDict] = {
        'missType': MissType,
        'amountMissed': int, # TODO: optional param
    }
    HealParser: ClassVar[FieldsDict] = {
        'amount': int,
        'overhealing': int,
        'absorbed': int,
        'critical': is_not_nil,
    }
    EnergizeParser: ClassVar[FieldsDict] = {
        'amount': int,
        'powerType': PowerType.from_literal,
    }
    DrainParser: ClassVar[FieldsDict] = {
        'amount': int,
        'powerType': PowerType.from_literal,
        'extraAmount': int,
    }
    SpellBlockParser: ClassVar[FieldsDict] = {
        'extraSpellID': int,
        'extraSpellName': str,
        'extraSchool': SchoolFlag.from_literal,
        'auraType': AuraType,
    }
    ExtraAttackParser: ClassVar[FieldsDict] = {
        'amount': int,
    }
    AuraParser: ClassVar[FieldsDict] = {
        'auraType': AuraType,
    }
    AuraDoseParser: ClassVar[FieldsDict] = {
        'auraType': AuraType,
        'amount': int,
    }
    CastFailedParser: ClassVar[FieldsDict] = {
        'failedType': FailedType,
    }
    
    # Special parsers
    EnchantParser: ClassVar[FieldsDict] = {
        'spellName': str,
        'itemID': int,
        'itemName': str,
    }
    
    # Combo-parsers
    prefix_parsers: ClassVar[ParserDict] = {
        #'EVENT_PREFIX': FieldsDict, # {} - no params for this prefix
        'SWING': {},
        'RANGE': SpellParser,
        'SPELL': SpellParser,
        'SPELL_PERIODIC': SpellParser,
        'SPELL_BUILDING': SpellParser,
        'ENVIRONMENTAL': EnvParser,
    }
    suffix_parsers: ClassVar[ParserDict] = {
        #'_EVENT_SUFFIX': FieldsDict, # {} - no params for this suffix
        '_DAMAGE': DamageParser,
        '_MISSED': MissParser,
        '_HEAL': HealParser,
        '_HEAL_ABSORBED': {},
        '_ABSORBED': {},
        '_ENERGIZE': EnergizeParser,
        '_DRAIN': DrainParser,
        '_LEECH': DrainParser,
        '_INTERRUPT': SpellBlockParser,
        '_DISPEL': SpellBlockParser,
        '_DISPEL_FAILED': SpellBlockParser,
        '_STOLEN': SpellBlockParser,
        '_EXTRA_ATTACKS': ExtraAttackParser,
        '_AURA_APPLIED': AuraParser,
        '_AURA_REMOVED': AuraParser,
        '_AURA_APPLIED_DOSE': AuraDoseParser,
        '_AURA_REMOVED_DOSE': AuraDoseParser,
        '_AURA_REFRESH': AuraParser,
        '_AURA_BROKEN': AuraParser,
        '_AURA_BROKEN_SPELL': SpellBlockParser,
        '_CAST_START': {},
        '_CAST_SUCCESS': {},
        '_CAST_FAILED': CastFailedParser,
        '_INSTAKILL': {},
        '_DURABILITY_DAMAGE': {},
        '_DURABILITY_DAMAGE_ALL': {},
        '_CREATE': {},
        '_SUMMON': {},
        '_RESURRECT': {},
    }
    special_parsers: ClassVar[TwinParserDict] = {
        #'SPECIAL_EVENT_NAME': (FieldsDict_Prefix, FieldsDict_Suffix),
        'DAMAGE_SPLIT': (SpellParser, DamageParser),
        'DAMAGE_SHIELD': (SpellParser, DamageParser),
        'DAMAGE_SHIELD_MISSED': (SpellParser, MissParser),
        'ENCHANT_APPLIED': (EnchantParser, {}),
        'ENCHANT_REMOVED': (EnchantParser, {}),
        'PARTY_KILL': ({}, {}),
        'UNIT_DIED': ({}, {}),
        'UNIT_DESTROYED': ({}, {}),
        'UNIT_DISSIPATES': ({}, {}),
    }
    
    def parse(self) -> Dict[str, Any]:
        """Parse event params to dict.
        This call removes parsed "params" from "self" object one by one
        and sets "self.parsed['params']" with list of params left unparsed.
        Return value: self.parsed.
        """
        if isinstance(self.event, CombatLogEvent):
            event = self.event.name
            self.parsed.update(self.event.dict())
        else:
            event = str(self.event)
        # Search for longest prefix
        prefix_fields, suffix_fields = None, None
        prefix_match = []
        for k in self.prefix_parsers.keys():
            if event.startswith(k):
                prefix_match.append(k)
        if prefix_match:
            prefix = max(prefix_match, key=len)
            prefix_fields = self.prefix_parsers.get(prefix, None)
            suffix = event[len(prefix):]
            suffix_fields = self.suffix_parsers.get(suffix, None)
        else: # No prefix found. Search special events
            for k, psrs in self.special_parsers.items():
                if event == k:
                    prefix_fields, suffix_fields = psrs
                    break
        if prefix_fields is None or suffix_fields is None:
            raise ParsingLookupError(f'Parser absent for unknown event {event}.')
        # Start popping params one by one in order saved in fields dicts
        for name, caster in chain(prefix_fields.items(), suffix_fields.items()):
            if name in self.parsed:
                raise ParsingError(
                    'Duplicate parse attempt for '
                    f'{event} event param {name}: {caster}.'
                )
            # TODO: Implement Optional caster logic
            # e.g. 'if isinstance(caster, dict): #optional parser'
            # TODO: Replace hack '0' for int with caster default value
            self.parsed[name] = caster(self.pop_param('0'))
        # Check if some params left unparsed
        if self.params:
            self.parsed['params'] = self.params
            log.warning(
                'EventParamsParser.parse(%s) left params %s unparsed.',
                self,
                self.params,
            )
        else:
            # All params parsed, remove it if exists
            self.parsed.pop('params', None)
        return self.parsed

    def pop_param(self, default: str = '') -> str:
        """Remove and return first param (with index 0) from "self.params".
        "default" returned if no items left (IndexError catched).
        Return value: self.params.pop(0) or default
        """
        val = default
        try:
            val = self.params.pop(0)
        except IndexError as exc:
            #log.exception(
            #    'EventParamsParser.pop_param(%s) failed with %r.',
            #    self,
            #    exc,
            #)
            pass
        return val


# Helper functions

def parse_combat_log_line(
    line: str,
) -> Dict[str, Any]:
    """Parse combatlog file line to dict."""
    parsed = None
    try:
        parsed = EventParamsParser(CombatLogEvent.from_log_line(line)).parse()
    except ParsingError as exc:
        log.exception(
            'Error occured while parsing line "%s": %r',
            line,
            exc,
        )
    return parsed


def parse_combat_log(
    combatlog: str,
) -> List[Dict[str, Any]]:
    """Parse combatlog file to list of dicts."""
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
        from pprint import pprint as pp
        cldf = pd.DataFrame(parse_combat_log('WoWCombatLog.txt'))
        pp(dir(), compact=True, indent=4)
    else:
        sys.exit(main(sys.argv))
