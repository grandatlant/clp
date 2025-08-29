# WoW 3.3.5 Combat Log Parsing & Format Reference Q&A

---

**User:**  
create a python script to load World of warcraft 3.3.5 combat log from file WoWCombatLog.txt to Pandas data frame for deep analyse

**Copilot:**  
```python name=wow_combatlog_loader.py
import pandas as pd
import re

def parse_combat_log_line(line):
    # Example WoW 3.3.5 combat log line:
    # 4/21 20:19:34.123  SPELL_DAMAGE,Player-1-00000001,"Playername",0x511,Creature-0-0000-00000-00000-0000000000,"Training Dummy",0x10a48,12345,"Fireball",0x4,Training Dummy,0,0,1234,0,0,0,nil,nil,nil
    # Date and message
    parts = line.strip().split('  ', 1)
    if len(parts) < 2:
        return None
    timestamp, event_rest = parts
    event_parts = event_rest.split(',')

    return {
        'timestamp': timestamp,
        'event': event_parts[0].strip(),
        'params': [x.strip().strip('"') for x in event_parts[1:]]
    }

def load_wow_combat_log(filename):
    records = []
    with open(filename, encoding='utf-8', errors='ignore') as f:
        for line in f:
            if not line.strip():
                continue
            parsed = parse_combat_log_line(line)
            if parsed:
                records.append(parsed)
    # Flatten params for DataFrame columns (optional: expand columns for specific events)
    df = pd.DataFrame(records)
    return df

# Example usage:
if __name__ == "__main__":
    df = load_wow_combat_log('WoWCombatLog.txt')
    print(df.head())
```

**Instructions:**
- Place this script in the same directory as your `WoWCombatLog.txt`.
- Run with `python wow_combatlog_loader.py`.
- The resulting DataFrame (`df`) will have columns: `timestamp`, `event`, and `params` (a list of string parameters for each event).
- For deeper analysis, you may want to further parse `params` based on the `event` type.

Let me know if you want to expand the columns for specific combat log events!

---

**User:**  
find me a complete reference to WoWCombatLog.txt file format with all types of events description and their parameters

**Copilot:**  

The World of Warcraft combat log (specifically for version 3.3.5, aka "Wrath of the Lich King") is not officially documented by Blizzard. However, the community has reverse-engineered and documented it extensively. The best references come from:

- [WoWWiki: COMBAT_LOG_EVENT](https://wowwiki-archive.fandom.com/wiki/COMBAT_LOG_EVENT)
- [WoWHead Forums](https://www.wowhead.com/forums)
- [GitHub projects related to WoW combat log parsing](https://github.com/search?q=wow+combat+log+parser)
- [Advanced Combat Tracker WoW Plugin Docs](https://advancedcombattracker.com/download.php)

Below is a **concise reference** for the WoW 3.3.5 combat log events and parameter structure:

---

## WoW 3.3.5 Combat Log File: Event Reference

### Format (Typical Line)

```
4/21 20:19:34.123  EVENT_NAME,sourceGUID,sourceName,sourceFlags,destGUID,destName,destFlags,[event-specific parameters...]
```

### General Event Types

- **SWING_DAMAGE**
- **SWING_MISSED**
- **RANGE_DAMAGE**
- **RANGE_MISSED**
- **SPELL_CAST_START**
- **SPELL_CAST_SUCCESS**
- **SPELL_CAST_FAILED**
- **SPELL_DAMAGE**
- **SPELL_MISSED**
- **SPELL_HEAL**
- **SPELL_ENERGIZE**
- **SPELL_DRAIN**
- **SPELL_LEECH**
- **SPELL_AURA_APPLIED**
- **SPELL_AURA_REMOVED**
- **SPELL_AURA_REFRESH**
- **SPELL_AURA_APPLIED_DOSE**
- **SPELL_AURA_REMOVED_DOSE**
- **SPELL_PERIODIC_DAMAGE**
- **SPELL_PERIODIC_HEAL**
- **SPELL_PERIODIC_ENERGIZE**
- **SPELL_PERIODIC_DRAIN**
- **SPELL_PERIODIC_LEECH**
- **SPELL_INTERRUPT**
- **SPELL_DISPEL**
- **SPELL_DISPEL_FAILED**
- **SPELL_STOLEN**
- **ENCHANT_APPLIED**
- **ENCHANT_REMOVED**
- **SPELL_SUMMON**
- **SPELL_CREATE**
- **SPELL_RESURRECT**
- **PARTY_KILL**
- **UNIT_DIED**
- **UNIT_DESTROYED**
- **ENVIRONMENTAL_DAMAGE**
- **DAMAGE_SHIELD**
- **DAMAGE_SHIELD_MISSED**
- **DAMAGE_SPLIT**
- **SPELL_INSTAKILL**
- **SPELL_EXTRA_ATTACKS**
- **SPELL_DURABILITY_DAMAGE**
- **SPELL_DURABILITY_DAMAGE_ALL**
- **SPELL_AURA_BROKEN**
- **SPELL_AURA_BROKEN_SPELL**

### Parameters

#### Common Prefix
For most events, the prefix (after timestamp) is:
```
EVENT_NAME,sourceGUID,sourceName,sourceFlags,destGUID,destName,destFlags
```
- **GUID**: Unique identifier for source/dest (player/creature/object)
- **Name**: Name of the unit (quoted if has spaces)
- **Flags**: Bitmask for unit type/affiliation/etc

#### Examples for Specific Events

**SWING_DAMAGE**  
```
SWING_DAMAGE,sourceGUID,sourceName,sourceFlags,destGUID,destName,destFlags,amount,overkill,school,resisted,blocked,absorbed,critical,glancing,crushing,isOffHand
```

**SPELL_DAMAGE**  
```
SPELL_DAMAGE,sourceGUID,sourceName,sourceFlags,destGUID,destName,destFlags,spellId,spellName,spellSchool,amount,overkill,school,resisted,blocked,absorbed,critical,glancing,crushing,isOffHand
```

**SPELL_HEAL**  
```
SPELL_HEAL,sourceGUID,sourceName,sourceFlags,destGUID,destName,destFlags,spellId,spellName,spellSchool,amount,overhealing,absorbed,critical
```

**SPELL_AURA_APPLIED**  
```
SPELL_AURA_APPLIED,sourceGUID,sourceName,sourceFlags,destGUID,destName,destFlags,spellId,spellName,spellSchool,auraType (BUFF/DEBUFF),amount
```

**ENVIRONMENTAL_DAMAGE**  
```
ENVIRONMENTAL_DAMAGE,sourceGUID,sourceName,sourceFlags,destGUID,destName,destFlags,environmentalType,amount,overkill,school,resisted,blocked,absorbed,critical,glancing,crushing,isOffHand
```

**UNIT_DIED**  
```
UNIT_DIED,sourceGUID,sourceName,sourceFlags,destGUID,destName,destFlags
```

### Links to Full References

- [WoWWiki: Combat Log](https://wowwiki-archive.fandom.com/wiki/Combat_log)
- [WoWWiki: COMBAT_LOG_EVENT](https://wowwiki-archive.fandom.com/wiki/COMBAT_LOG_EVENT)
- [COMBAT_LOG_EVENT_UNFILTERED Parameter Reference](https://wowpedia.fandom.com/wiki/COMBAT_LOG_EVENT#Parameters)

### Example Table of Parameters

| Event                | Extra Params (after destFlags)                                                                                                                                              |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| SWING_DAMAGE         | amount, overkill, school, resisted, blocked, absorbed, critical, glancing, crushing, isOffHand                                                                              |
| SPELL_DAMAGE         | spellId, spellName, spellSchool, amount, overkill, school, resisted, blocked, absorbed, critical, glancing, crushing, isOffHand                                             |
| SPELL_MISSED         | spellId, spellName, spellSchool, missType, amountMissed, isOffHand                                                                                                          |
| SPELL_AURA_APPLIED   | spellId, spellName, spellSchool, auraType (BUFF/DEBUFF), amount                                                                                                             |
| SPELL_HEAL           | spellId, spellName, spellSchool, amount, overhealing, absorbed, critical                                                                                                    |
| UNIT_DIED            | (no extra params)                                                                                                                                                           |
| ENVIRONMENTAL_DAMAGE | environmentalType, amount, overkill, school, resisted, blocked, absorbed, critical, glancing, crushing, isOffHand                                                          |

---

## Community Parser Reference

- [Details! Damage Meter (GitHub)](https://github.com/Tercioo/Details-Damage-Meter) — Includes up-to-date event tables for 3.3.5
- [WoWCombatLogParser.py Example](https://github.com/MaksymVlasov/wow-log-parser/blob/master/wowcombatlogparser.py)

---

### **For full, up-to-date, and detailed reference, consult:**
- [https://wowwiki-archive.fandom.com/wiki/COMBAT_LOG_EVENT](https://wowwiki-archive.fandom.com/wiki/COMBAT_LOG_EVENT)
- [https://wowpedia.fandom.com/wiki/COMBAT_LOG_EVENT#Parameters](https://wowpedia.fandom.com/wiki/COMBAT_LOG_EVENT#Parameters)

If you want a **machine-readable table** of all events/parameters, let me know!

---

**User:**  
save this conversation to downloadable markdown file for me

**Copilot:**  
*(This file!)*