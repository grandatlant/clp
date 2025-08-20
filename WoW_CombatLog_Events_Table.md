# WoW Combat Log Events: Table of Events, Descriptions, and Parameters

*Note: This list is based on community knowledge and the [Details! Damage Meter](https://github.com/Tercioo/Details-Damage-Meter) addon structure. Because of GitHub's code search limitations, this table may not include every possible event. For a complete and always up-to-date reference, see [WoWWiki: COMBAT_LOG_EVENT](https://wowwiki-archive.fandom.com/wiki/COMBAT_LOG_EVENT) and [Details! repo](https://github.com/Tercioo/Details-Damage-Meter/search?q=combat+log+event).*

| Event Name                  | Description                                                      | Event Parameters (after common prefix)                                                                                                                                              |
|-----------------------------|------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| SWING_DAMAGE                | Melee auto-attack hit that deals damage.                         | amount, overkill, school, resisted, blocked, absorbed, critical, glancing, crushing, isOffHand                                              |
| SWING_MISSED                | Melee auto-attack that missed (dodge, miss, parry, etc.).        | missType, isOffHand, amountMissed                                                                                                            |
| RANGE_DAMAGE                | Ranged attack hit (e.g., Hunter shot) that deals damage.         | spellId, spellName, spellSchool, amount, overkill, school, resisted, blocked, absorbed, critical, glancing, crushing, isOffHand             |
| RANGE_MISSED                | Ranged attack that missed.                                       | spellId, spellName, spellSchool, missType, isOffHand, amountMissed                                                                           |
| SPELL_DAMAGE                | Spell hit that deals damage.                                     | spellId, spellName, spellSchool, amount, overkill, school, resisted, blocked, absorbed, critical, glancing, crushing, isOffHand             |
| SPELL_MISSED                | Spell did not land (miss, resist, immune, etc.).                 | spellId, spellName, spellSchool, missType, isOffHand, amountMissed                                                                           |
| SPELL_HEAL                  | Spell that heals a target.                                       | spellId, spellName, spellSchool, amount, overhealing, absorbed, critical                                                                     |
| SPELL_ENERGIZE              | Spell or ability grants mana/energy/rage.                        | spellId, spellName, spellSchool, amount, powerType, extraAmount                                                                              |
| SPELL_DRAIN                 | Spell drains resource from target (e.g., mana drain).            | spellId, spellName, spellSchool, amount, powerType, extraAmount                                                                              |
| SPELL_LEECH                 | Spell leeches resource from target.                              | spellId, spellName, spellSchool, amount, powerType, extraAmount, powerGain                                                                   |
| SPELL_AURA_APPLIED          | Aura (buff/debuff) is applied to target.                         | spellId, spellName, spellSchool, auraType (BUFF/DEBUFF), amount                                                                              |
| SPELL_AURA_REMOVED          | Aura (buff/debuff) is removed from target.                       | spellId, spellName, spellSchool, auraType (BUFF/DEBUFF), amount                                                                              |
| SPELL_AURA_REFRESH          | Aura (buff/debuff) is refreshed on target.                       | spellId, spellName, spellSchool, auraType (BUFF/DEBUFF), amount                                                                              |
| SPELL_AURA_APPLIED_DOSE     | Stackable aura gain (applies additional dose/stack).             | spellId, spellName, spellSchool, auraType (BUFF/DEBUFF), amount                                                                              |
| SPELL_AURA_REMOVED_DOSE     | Stackable aura lose (reduces dose/stack).                        | spellId, spellName, spellSchool, auraType (BUFF/DEBUFF), amount                                                                              |
| SPELL_PERIODIC_DAMAGE       | Damage over time tick.                                           | spellId, spellName, spellSchool, amount, overkill, school, resisted, blocked, absorbed, critical                                             |
| SPELL_PERIODIC_HEAL         | Heal over time tick.                                             | spellId, spellName, spellSchool, amount, overhealing, absorbed, critical                                                                     |
| SPELL_PERIODIC_ENERGIZE     | Resource over time tick (mana/energy/rage).                      | spellId, spellName, spellSchool, amount, powerType, extraAmount                                                                              |
| SPELL_PERIODIC_DRAIN        | Resource drain over time tick.                                   | spellId, spellName, spellSchool, amount, powerType, extraAmount                                                                              |
| SPELL_PERIODIC_LEECH        | Resource leech over time tick.                                   | spellId, spellName, spellSchool, amount, powerType, extraAmount, powerGain                                                                   |
| SPELL_INTERRUPT             | Spell cast is interrupted.                                       | spellId, spellName, spellSchool, extraSpellId, extraSpellName, extraSchool                                                                   |
| SPELL_DISPEL                | Buff or debuff is dispelled.                                     | spellId, spellName, spellSchool, extraSpellId, extraSpellName, extraSchool, auraType                                                        |
| SPELL_DISPEL_FAILED         | Dispel attempt failed.                                           | spellId, spellName, spellSchool, extraSpellId, extraSpellName, extraSchool, auraType                                                        |
| SPELL_STOLEN                | Buff/debuff is stolen by a spell.                                | spellId, spellName, spellSchool, extraSpellId, extraSpellName, extraSchool, auraType                                                        |
| ENCHANT_APPLIED             | Weapon/gear enchantment applied.                                 | itemId, itemName, enchantId, enchantName                                                                                                     |
| ENCHANT_REMOVED             | Weapon/gear enchantment removed.                                 | itemId, itemName, enchantId, enchantName                                                                                                     |
| SPELL_SUMMON                | Summons a creature/object.                                       | spellId, spellName, spellSchool, creatureGUID, creatureName, creatureType                                                                    |
| SPELL_CREATE                | Creates an object (e.g., a healthstone).                         | spellId, spellName, spellSchool, objectGUID, objectName, objectType                                                                          |
| SPELL_RESURRECT             | Resurrects a player or NPC.                                      | spellId, spellName, spellSchool, resurrectedGUID, resurrectedName                                                                            |
| PARTY_KILL                  | Source kills the target.                                         | (none)                                                                                                                                       |
| UNIT_DIED                   | Target unit has died.                                            | (none)                                                                                                                                       |
| UNIT_DESTROYED              | Target unit/object is destroyed.                                 | (none)                                                                                                                                       |
| ENVIRONMENTAL_DAMAGE        | Damage from environment (falling, fire, drowning, etc.).         | environmentalType, amount, overkill, school, resisted, blocked, absorbed, critical, glancing, crushing, isOffHand                            |
| DAMAGE_SHIELD               | Damage dealt by a damage shield.                                 | spellId, spellName, spellSchool, amount, overkill, school, resisted, blocked, absorbed, critical, glancing, crushing, isOffHand              |
| DAMAGE_SHIELD_MISSED        | Damage shield failed to hit.                                     | spellId, spellName, spellSchool, missType, isOffHand, amountMissed                                                                           |
| DAMAGE_SPLIT                | Damage split among several targets.                              | spellId, spellName, spellSchool, amount, absorbed                                                                                            |
| SPELL_INSTAKILL             | Spell causes instant death.                                      | spellId, spellName, spellSchool, instantKillType                                                                                             |
| SPELL_EXTRA_ATTACKS         | Grants extra attacks.                                            | spellId, spellName, spellSchool, amount                                                                                                      |
| SPELL_DURABILITY_DAMAGE     | Spell causes item durability loss.                               | spellId, spellName, spellSchool, itemId, itemName                                                                                            |
| SPELL_DURABILITY_DAMAGE_ALL | Spell causes all items to lose durability.                       | spellId, spellName, spellSchool                                                                                                              |
| SPELL_AURA_BROKEN           | Aura broken due to damage or effect.                             | spellId, spellName, spellSchool, extraSpellId, extraSpellName, extraSchool, auraType                                                        |
| SPELL_AURA_BROKEN_SPELL     | Aura broken by a specific spell.                                 | spellId, spellName, spellSchool, extraSpellId, extraSpellName, extraSchool, auraType                                                        |

## Common Prefix Parameters for All Events

All events start with:
- **timestamp** (not an argument, but in the log)
- **event** (the event type, e.g., SPELL_DAMAGE)
- **sourceGUID** (unique id for the source)
- **sourceName** (name of the source)
- **sourceFlags** (bitmask for the source)
- **destGUID** (unique id for the dest)
- **destName** (name of the dest)
- **destFlags** (bitmask for the dest)

## References
- [Details! Damage Meter: combat log logic](https://github.com/Tercioo/Details-Damage-Meter/search?q=combat+log+event)
- [WoWWiki: COMBAT_LOG_EVENT](https://wowwiki-archive.fandom.com/wiki/COMBAT_LOG_EVENT)
- [WoW Combat Log Event Parameters (community)](https://wowpedia.fandom.com/wiki/COMBAT_LOG_EVENT#Parameters)

---

*For more events and parameter details, search ["combat log event"](https://github.com/Tercioo/Details-Damage-Meter/search?q=combat+log+event) in the Details! GitHub repository.*