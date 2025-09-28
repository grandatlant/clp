#!/usr/bin/env -S python3 -O
# -*- coding = utf-8 -*-
"""clp.py
Combat Log Parsing Module.

Reference:
https://wowpedia.fandom.com/wiki/COMBAT_LOG_EVENT
"""

__copyright__ = 'Copyright (C) 2025 grandatlant'

__version__ = '0.1.1'

__all__ = [
    # Helper functions
    'parse_combat_log',
    'parse_combat_log_generator',
    'parse_combat_log_line',
    # Helper classes
    'ParsingError',
    'ParsingLookupError',
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
    'Unit',
    # Parsing classes
    'CombatLogEvent',
    'EventParamsParser',
]

import datetime
import enum
import itertools
import logging
import re
import shlex
from dataclasses import dataclass, field, asdict
from typing import (
    Final,
    ClassVar,
    Callable,
    Generator,
    Any,
    Optional,
    Union,
    Tuple,
    List,
    Dict,
)

# Type hints for EventParamsParser methods
FieldsDict = Dict[str, Callable[[str], Any]]
ParserDict = Dict[str, FieldsDict]
TwinParserDict = Dict[str, Tuple[FieldsDict, FieldsDict]]


log: Final[logging.Logger] = logging.getLogger(__name__)


# Helper casters for parsing


def is_not_nil(arg: str) -> bool:
    """True if (arg != 'nil'), False otherwise."""
    return arg != 'nil'


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
        member = cls.pseudo_member(value)
        log.warning(
            'StrEnumParser._missing_(%r, %r) '
            'called to generate pseudo member %r.',
            cls,
            value,
            member,
        )
        return member

    @classmethod
    def pseudo_member(cls, value):
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
        name = re.sub(r'\W+|^(?=\d)', '_', str(value)).upper()
        if not name.isidentifier():  # just double-check to be sure
            raise ValueError(
                'Value %r can not be transformed to a valid Enum member name.'
                % value
            )
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
        literal: Union[str, bytes, bytearray] = '0',
        base: int = 0,
    ):
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
    # and much more.
    # better use str instead this enum
    # or be happy with _missing_ produced


class PowerType(IntEnumParser):
    """Power Type parsing enum."""

    HEALTH = -2
    NONE = -1
    MANA = 0
    RAGE = 1
    FOCUS = 2
    ENERGY = 3
    COMBOPOINTS = 4  # or pet happiness, idk
    RUNES = 5
    RUNIC_POWER = 6


class UnitFlag(IntFlagParser):
    """Unit Flags parsing enum."""

    # Affiliation
    AFFILIATION_MINE = 0x00000001
    AFFILIATION_PARTY = 0x00000002
    AFFILIATION_RAID = 0x00000004
    AFFILIATION_OUTSIDER = 0x00000008
    # UNIT_AFFILIATION_MASK = 0x0000000F
    # Reaction
    REACTION_FRIENDLY = 0x00000010
    REACTION_NEUTRAL = 0x00000020
    REACTION_HOSTILE = 0x00000040
    REACTION_UNKNOWN_FLAG = 0x00000080  # Not in reference!
    # UNIT_REACTION_MASK = 0x000000F0
    # Control
    CONTROL_PLAYER = 0x00000100
    CONTROL_NPC = 0x00000200
    # UNIT_CONTROL_MASK = 0x00000300
    # Type
    TYPE_PLAYER = 0x00000400
    TYPE_NPC = 0x00000800
    TYPE_PET = 0x00001000
    TYPE_GUARDIAN = 0x00002000
    TYPE_OBJECT = 0x00004000
    TYPE_UNKNOWN_FLAG = 0x00008000  # Not in reference!
    # UNIT_TYPE_MASK = 0x0000FC00
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
    SPECIAL_UNKNOWN_FLAG_0x10000000 = 0x10000000  # Not in reference!
    SPECIAL_UNKNOWN_FLAG_0x20000000 = 0x20000000  # Not in reference!
    SPECIAL_UNKNOWN_FLAG_0x40000000 = 0x40000000  # Not in reference!
    NONE = 0x80000000
    # UNIT_SPECIAL_MASK = 0xFFFF0000


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
    SCHOOL_UNKNOWN_FLAG = 0x80  # Not in reference!
    # Double Schools Alias
    HOLYSTRIKE = HOLY | PHYSICAL
    FLAMESTRIKE = FIRE | PHYSICAL
    RADIANT = FIRE | HOLY
    HOLYFIRE = RADIANT
    STORMSTRIKE = NATURE | PHYSICAL
    HOLYSTORM = NATURE | HOLY
    VOLCANIC = NATURE | FIRE
    FROSTSTRIKE = FROST | PHYSICAL
    HOLYFROST = FROST | HOLY
    FROSTFIRE = FROST | FIRE
    FROSTSTORM = FROST | NATURE
    SHADOWSTRIKE = SHADOW | PHYSICAL
    TWILIGHT = SHADOW | HOLY
    SHADOWLIGHT = TWILIGHT
    SHADOWFLAME = SHADOW | FIRE
    PLAGUE = SHADOW | NATURE
    SHADOWSTORM = PLAGUE
    SHADOWFROST = SHADOW | FROST
    SPELLSTRIKE = ARCANE | PHYSICAL
    DIVINE = ARCANE | HOLY
    SPELLFIRE = ARCANE | FIRE
    ASTRAL = ARCANE | NATURE
    SPELLSTORM = ASTRAL
    SPELLFROST = ARCANE | FROST
    SPELLSHADOW = ARCANE | SHADOW
    # Multi Schools Alias
    ELEMENTAL = FROST | NATURE | FIRE
    CHROMATIC = SHADOW | FROST | NATURE | FIRE | HOLY
    COSMIC = ARCANE | SHADOW | NATURE | HOLY
    CHAOS = ARCANE | SHADOW | FROST | NATURE | FIRE
    MAGIC = ARCANE | SHADOW | FROST | NATURE | FIRE | HOLY


# Main external interface


class UnitGuid(str):
    """UnitGuid str subclass with ability
    to try to form int value (defaults to 0).
    """

    def __int__(self):
        """Return value: int(self, base=0)."""
        return int(str(self).strip(), base=0)

    def to_int(self) -> int:
        """Return value: int(self) or int(0)."""
        val = int(0)
        try:
            val = int(self)
        except ValueError as exc:
            log.exception(
                'UnitGuid.to_int(%r) failed with %r. int(0) returned.',
                self,
                exc,
            )
        return val


@dataclass
class Unit:
    """Describes Unit info."""

    guid: UnitGuid
    name: str
    flags: UnitFlag = UnitFlag.NONE

    def __post_init__(self):
        if not isinstance(self.guid, UnitGuid):
            self.guid = UnitGuid(str(self.guid))
        if not isinstance(self.flags, UnitFlag):
            if isinstance(self.flags, int):
                self.flags = UnitFlag(self.flags)
            else:
                self.flags = UnitFlag.from_literal(str(self.flags))

    def dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __str__(self):
        """Return value: self.name."""
        return self.name if isinstance(self.name, str) else str(self.name)

    def __int__(self):
        """Return value: int(self.flags)."""
        return int(self.flags)


@dataclass(order=True)
class CombatLogEvent:
    """Describes single Combat Log record."""

    timestamp: float
    name: str

    source: Optional[Unit] = None
    dest: Optional[Unit] = None

    params: List[str] = field(default_factory=list)

    @classmethod
    def from_log_line(cls, line: str):
        """Constructor for WoWCombatLog.txt parsing line by line."""
        # Example WoW 3.3.5 combat log line:
        # 4/21 20:19:34.123  SPELL_DAMAGE,Player-1-00000001,"Playername",0x511,Creature-0-0000-00000-00000-0000000000,"Training Dummy",0x10a48,12345,"Fireball",0x4,Training Dummy,0,0,1234,0,0,0,nil,nil,nil
        datetimestr, eventstr = line.strip().split('  ', 1)
        datetimestr, milliseconds = datetimestr.rsplit('.', 1)
        # TODO: Think about reading log file modification date to get year...
        yearstr = '1970'  # yes, just EPOCH year for smaller timestamp numbers
        datetimeobj = datetime.datetime.strptime(
            f'{yearstr} {datetimestr}',
            '%Y %m/%d %H:%M:%S',
        ) + datetime.timedelta(milliseconds=int(milliseconds))
        timestamp = datetimeobj.timestamp()
        # Event descriprion part
        # event_parts = eventstr.split(',')
        splitter = shlex.shlex(eventstr, posix=True)
        splitter.whitespace = ','
        splitter.whitespace_split = True
        event_parts = list(splitter)
        # Event name first
        name = event_parts[0].strip()
        if len(event_parts) < 7:  # no source-dest info.
            obj = cls(timestamp, name)
            log.warning(
                'CombatLogEvent.from_log_line(%r, %r): '
                'Unknown line format. Defaults returned: %r.',
                cls,
                line,
                obj,
            )
            return obj
        # Base event params (source-dest info)
        sourceID = event_parts[1].strip().strip('"')
        sourceName = event_parts[2].strip().strip('"')
        sourceFlags = event_parts[3].strip().strip('"')
        destID = event_parts[4].strip().strip('"')
        destName = event_parts[5].strip().strip('"')
        destFlags = event_parts[6].strip().strip('"')
        # Event-specific params
        params = [p.strip().strip('"') for p in event_parts[7:]]
        # Create complete CombatLogEvent
        return cls(
            timestamp,
            name,
            Unit(
                sourceID,
                sourceName,
                sourceFlags,
            ),
            Unit(
                destID,
                destName,
                destFlags,
            ),
            params,
        )

    def dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __str__(self):
        """Return value: self.name."""
        return self.name if isinstance(self.name, str) else str(self.name)

    def __float__(self):
        """Return value: self.timestamp."""
        return (
            self.timestamp
            if isinstance(self.timestamp, float)
            else float(self.timestamp)
        )

    def __int__(self):
        """Return value: int(self.timestamp)."""
        return int(self.timestamp)


@dataclass
class EventParamsParser:
    """Class for parsing CombatLogEvent for analyse."""

    # Input data
    event: Union[CombatLogEvent, str]
    params: List[str] = field(default_factory=list)
    # Output data
    parsed: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.event, CombatLogEvent):
            self.params = self.event.params.copy()

    # TemplateParser: ClassVar[FieldsDict] = {
    #    'param1Name': constructor_from_str,
    #    'param2Name': callable_caster_from_str_to_parsed_value,
    # }

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
        'amountMissed': int,  # optional
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
        #'EVENT_PREFIX': FieldsDict,  # {} - no params for this prefix
        'SWING': {},
        'RANGE': SpellParser,
        'SPELL': SpellParser,
        'SPELL_PERIODIC': SpellParser,
        'SPELL_BUILDING': SpellParser,
        'ENVIRONMENTAL': EnvParser,
    }
    suffix_parsers: ClassVar[ParserDict] = {
        #'_EVENT_SUFFIX': FieldsDict,  # {} - no params for this suffix
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

    @classmethod
    def get_all_fields(cls) -> FieldsDict:
        # TODO: Replace result with collections.ChainMap
        result = {}
        for fieldsdict in itertools.chain(
            cls.prefix_parsers.values(),
            cls.suffix_parsers.values(),
        ):
            result.update(fieldsdict)
        for sp_pref, sp_suff in cls.special_parsers.values():
            result.update(sp_pref)
            result.update(sp_suff)
        return result

    def parse(self, params: Optional[List[str]] = None) -> Dict[str, Any]:
        """Parse event params to dict according to event name.
        This call sets "self.parsed['params']"
        with list of params left unparsed.
        Return value: self.parsed.
        """
        if isinstance(self.event, CombatLogEvent):
            event = self.event.name
            self.parsed.update(self.event.dict())
        else:
            event = str(self.event)
            self.parsed.setdefault('name', event)
        params = self.params if params is None else params
        # Search for prefix-suffix pair with longest prefix
        prefix_fields, suffix_fields = None, None
        prefix_match = []
        for k in self.prefix_parsers.keys():
            if event.startswith(k):
                prefix_match.append(k)
        if prefix_match:
            prefix = max(prefix_match, key=len)
            prefix_fields = self.prefix_parsers.get(prefix, None)
            suffix = event[len(prefix) :]
            suffix_fields = self.suffix_parsers.get(suffix, None)
        else:  # No prefix found. Search special events
            for k, psrs in self.special_parsers.items():
                if event == k:
                    prefix_fields, suffix_fields = psrs
                    break
        if prefix_fields is None or suffix_fields is None:
            err = f'No parser for event {event}.'
            raise ParsingLookupError(err)
        # Start parsing params
        parsed_count = 0
        parsers = itertools.chain(prefix_fields.items(), suffix_fields.items())
        for (name, caster), param in zip(parsers, params):
            if name in self.parsed:
                err = f'Duplicate: {event} param "{name}" already parsed.'
                raise ParsingError(err)
            self.parsed[name] = caster(param)
            parsed_count += 1
        # Check if some params left unparsed
        params_left = params[parsed_count:]
        if params_left:
            self.parsed['params'] = params_left
            log.warning(
                'EventParamsParser.parse(%r, %r) call '
                'left params %r unparsed '
                'for event %r.',
                self,
                params,
                params_left,
                event,
            )
        else:  # all params parsed in full, remove it from result
            self.parsed.pop('params', None)
        return self.parsed


# Helper functions


def parse_combat_log_line(
    line: str,
) -> Dict[str, Any]:
    """Parse combatlog file line to dict."""
    parsed = dict()
    try:
        parsed = EventParamsParser(CombatLogEvent.from_log_line(line)).parse()
    except ParsingError as exc:
        log.exception(
            'Error occured while parsing combatlog line %r: %r',
            line,
            exc,
        )
    return parsed


def parse_combat_log_generator(
    combatlog: str,
) -> Generator[Dict[str, Any], None, None]:
    """Generator for parsed combatlog events."""
    with open(combatlog, encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.strip():
                if parsed := parse_combat_log_line(line):
                    yield parsed


def parse_combat_log(
    combatlog: str,
) -> List[Dict[str, Any]]:
    """Parse combatlog file to list of dicts."""
    return list(parse_combat_log_generator(combatlog))


def main(args=None):
    return 0


if __name__ == '__main__':
    main()
