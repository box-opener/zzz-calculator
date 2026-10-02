# Implementation notes and open questions

This file records non-authoritative implementation limits. It does not change
the terminology, calculation, or implementation specifications, and it does
not decide game semantics.

## Hoshimi Miyabi (`character:1091`)

### Nanoka source version

The old fixed Nanoka path `3.2.4+18409985` now returns 404 for both Miyabi and
an already-pinned character. Nanoka's public manifest currently lists the
released `3.2` dataset and the newer `3.3.4+19304006` dataset; the page's live
version is `3.2`. Miyabi's packaged raw record therefore uses the real,
retrievable URL `https://static.nanoka.cc/zzz/3.2/zh/character/1091.json`, with
`source_version` recorded as `3.2`. Existing raw records and the shared pinned
version constant remain unchanged.

### Skill parameter relationships not stated by the source text

Nanoka groups multiple different source curves under the same parameter name
for three moves. The reviewed mapping retains every source skill ID and value.
The selected entry is blocked with its candidates until their relationship is
resolved; these diagnostics are attached to the entry, so unrelated moves and
supporting-character requests continue to calculate.

- `强化特殊技：飞雪` has two `斩击伤害倍率` curves (`1091009`, `1091010`) and
  two `追击伤害倍率` curves (`1091011`, `1091012`). Its text distinguishes the
  first and second press, but does not say whether each pair is multiple hits,
  a complete move value, or mutually exclusive versions.
- `连携技：春临` has `伤害倍率` curves `1091015`, `1091016`, and `1091017`.
  The first two values are equal, and the source text gives no hit count or
  aggregation rule.

### Cinema 6 automatic slash

The raw text says:

> 在<color=#FFFFFF>[霜月架势]</color>期间，星见雅将获得<color=#FFFFFF>[极意]</color>效果，使<color=#FFFFFF>[普通攻击：霜月]</color>造成的伤害提升<color=#2BAD00>30%</color>；获得<color=#FFFFFF>[极意]</color>效果后，消耗<color=#FFFFFF>[落霜]</color>时，星见雅会根据当前蓄力段数，自动拔刀向前方发动强力斩击；在<color=#FFFFFF>[落霜]</color>耗尽前，拔刀斩击不会打断<color=#FFFFFF>[霜月架势]</color>下的蓄力进度；在一次<color=#FFFFFF>[霜月架势]</color>期间，最多连续发动3次拔刀斩击。

The current raw record has no C6 slash multiplier. The text does not establish
whether the slash reuses the selected Frostmoon charge multiplier or has a
separate multiplier, nor does it explicitly assign the slash a MoveId or damage
tags. The implementation keeps a stage-specific derived event and a 0–3
repeat input, but an emitted slash is blocked as ambiguous until its multiplier
and identity are reviewed. The template's absent MoveId and empty tags are
provisional isolation values, not a confirmed game identity. The explicit 30%
Frostmoon damage modifier remains active on the actual Frostmoon move. A repeat
count of zero creates no slash event and does not block the main move.

### Static state inputs

The following are exposed as current-state scenario conditions. The calculator
does not replay their creation, expiry, cooldown, or order:

- whether the enemy currently has Icefire and whether Frostburn Break's
  10-second trigger interval is available;
- whether the enemy currently has Frostscorch;
- whether the Cinema 1 team buildup-efficiency effect gained after a full
  Frostmoon hit removes Frostscorch is currently active;
- whether the current Frostmoon is the one after a team Disorder trigger;
- whether the Ultimate's 12-second Ice damage bonus is currently active.

Miyabi's Icefire buildup efficiency is retained as
`min(current crit rate, 80%)` on `ANOMALY_BUILDUP_EFFICIENCY` and reads the
formal settlement panel after panel effects. It appears in the execution trace.
The browser's static anomaly assumption still treats one gauge as 100% complete,
so buildup efficiency and buildup-value increases do not multiply final damage.

## Packaged base-panel scope

`character_base_stats` currently accepts character level only and uses the
level-60 (`extra_level[6]`) stat record for the reviewed equipment-build slice.
For Miyabi this gives attack `880.6952`, anomaly mastery `116`, and anomaly
proficiency `238` (148 base + 90 from source property `31201`). The API has no
separate ascension/core-stat selector, so selecting a lower core passive level
does not alter this level-60 base panel. Manual-panel mode remains available
for user-supplied stats.

## Yixuan (`character:1371`)

### Nanoka source version and packaged panel

The Yixuan detail record is packaged from the currently retrievable live `3.2`
source at `https://static.nanoka.cc/zzz/3.2/zh/character/1371.json`, with that
version and URL recorded in the raw file. The older pinned path
`3.2.4+18409985` returned 404 during source validation; no existing character
record or shared version constant was rewritten. The raw record identifies
base element 以太 and special element 玄墨. Its level-60 `extra_level[6]`
contains `11101` HP `+420`; the common Nanoka panel normalization includes this
property and yields HP `8373.8621`, attack `872.5748`, crit rate `0.194`,
anomaly mastery `92`, and anomaly proficiency `90` before equipment.

The build API still takes character level but no separate core/ascension-level
input. Equipment builds therefore use the packaged level-60, `extra_level[6]`
panel even when the selected core level is lower. Manual-panel mode remains
available for user-supplied values.

Yixuan's source says each point of her maximum HP adds 0.1 penetration force.
The shared calculation specification already defines the general formula as
`0.25 × current attack + 0.10 × current max HP`; the compiler uses the existing
typed `PenetrationDamageEvent` and this shared formula without adding a second
HP term. The independent Xuanmo anomaly is calculated through the static
`AnomalyRecord` path, not through penetration force.

### Lightning event identity

The Additional Ability and Cinema 1 text state force multipliers of 225% and
50%, respectively, and identify Yixuan as the force owner/dealer. Neither
passage assigns the lightning event an elemental attribute, `MoveId`,
`SkillGroup`, or damage tags. When the explicit Perfect Support switch-out or
Cinema 1 hit condition is selected, the event creation is therefore blocked
with an `AMBIGUOUS_SEMANTICS` diagnostic that retains the known multiplier and
the unresolved identity choices. No lightning damage value is guessed.

The existing static request model can exercise Cinema 1 from a Direct or
Penetration damage event, including Yixuan's own Penetration event. It does not
simulate the six-second cooldown. The Additional Ability's switched-out actor
is supplied as a separate current-state selection; the current support-entry
trigger contract identifies the incoming actor, not the outgoing Yixuan.

### Static anomaly and resource states

Yixuan's raw core text identifies an independent 玄墨 anomaly gauge. The
calculator exposes 玄墨侵蚀 as a separate `AttributeAnomalyDamageEvent` using
the static full-gauge assumption: 10 seconds, 20 ticks at 62.5% each. Its
紊乱 event uses the maximum-duration formula `450% + 20 × 62.5% = 1700%` and
inherits the Xuanmo anomaly record. These events use the Ether base resistance
and the anomaly/disorder calculators; Penetration, Core damage, Cinema 4, and
Cinema 6 modifiers are filtered out of these settlements.

The calculator accepts current-state choices for 凝神, 聚墨/符法千重-破,
静心 stack count, the Perfect Support switch-out, and the C6 free Ultimate.
It does not replay state acquisition, duration expiry, stack consumption,
cooldowns, flash energy, 术法值, or the extra 3 seconds of stun duration. The
Extra Ability's 10-second flash recovery and Yixuan's other flash/resource
changes are also outside the current damage calculation contract. When the
Extra Ability is eligible and 凝神 is selected, its 40% crit-damage bonus is a
settlement-panel effect owned by Yixuan; it does not change teammates' panels.
Attribute anomaly and Disorder events use no-crit rules, so this ordinary crit
panel value does not alter their damage.

## Lucia (`character:1451`)

### Nanoka source and packaged panel

The raw character record is retained at `core/data/characters/lucia.json` from
`https://static.nanoka.cc/zzz/3.2/zh/character/1451.json`, with the live `3.2`
version and exact source URL embedded in the file. Its rarity field is `4`,
which the local character catalog maps to S rank. The level-60 packaged panel
includes the raw `extra_level[6].extra["30501"]` energy-recovery bonus and
normalizes to HP `8477.1696`, attack `758.2048`, anomaly mastery `96`, anomaly
proficiency `95`, and energy recovery `1.56` before equipment.

The shared equipment-build API still has no ascension/core-stat selector, so
these level-60 figures use `extra_level[6]` even when a lower core level is
selected. Manual-panel mode can represent a different panel.

### Current and initial maximum HP

The EX Chorus source encodes the final-hit addition as
`{CAL:0.34 + 0.03 × effective special-skill level,100,2}%`; the `100` is the
CAL display scale, so the settlement multiplier is `0.34 + 0.03 × effective
special-skill level` (0.70 at level 12), with no additional division by 100.
It is a separate Direct event using Lucia's current maximum-HP panel and is
created once for the final hit of each reviewed Chorus move. The child keeps
its parent's MoveId, skill group, and tags so C2/C6 Chorus effects apply to it.
Ultimate rush collision children retain the Ultimate MoveId but are excluded;
only the stop-time finisher gets one HP component. Whim variants get none. The
team 5% max-HP effect during Spring Ether Curtain is a current panel modifier,
so it changes this added damage.

Break Dark instead reads Lucia's initial maximum HP. The source formula is
represented as `12 + initial HP × (5 + 0.2 × effective special-skill level) /
200`, capped at `612 + 24 × effective special-skill level` total added
penetration force. The 12 flat force is separate from the HP-scaled term; the
Spring Curtain current-HP increase does not raise the input to this formula.
The source does not say to floor the result, so the implementation does not.

Cinema 6 reads initial maximum HP for its 2% attack increase, applied to
Lucia's own panel. Its +30% crit damage applies only to Lucia Chorus Direct
events, while the Extra Ability's +30% crit damage is a team panel buff during
Break Dark and requires another Rupture or Stun teammate. Cinema 6 guaranteed
crit is an independently enabled event effect for Chorus moves while any Ether
Curtain is selected; it is not a permanent property of the raw event template.

The static damage rules also carry non-blocking diagnostics for resources that
do not alter the current settlement: Cinema 1's 5% Decibel-gain and Echo-stack
refresh, Cinema 4's 100 Decibels (with its 15-second trigger interval), the EX
Special raw energy-cost field with no numeric value, and the Ultimate's
Starlight-area HP recovery. Their resource, healing, and timing effects are not
calculated. These diagnostics leave the known damage values usable.

### Dream follow-up and Ultimate rush collisions

The Core source identifies an automatic follow-up as Chorus, but Nanoka exposes
three same-named `追加攻击伤害倍率` curves under skill IDs `1451007`, `1451010`,
and `1451015` without saying which generated move identity, skill group, or
damage tags they inherit. A Direct or Penetration hit from the current operator
can therefore retain the known partial result and a blocking identity
diagnostic with all three current-level multiplier candidates. A hit dealt by
Lucia herself does not trigger this follow-up. The calculation does not model
the 8-second lockout or dream-resource consumption.

Ultimate source curve `1451024` gives each rush collision multiplier, but the
3-second hold duration does not determine how many collisions occur. The
calculator exposes an integer selected hit count with no inferred upper bound;
without a count only the known finisher remains calculated and the selected
Ultimate path is partial. A count of zero adds no collision event. Positive
counts create repeated events with the Ultimate's MoveId and tags; the EX
Chorus max-HP addition remains limited to its one final hit.

### Static state assumptions and anomaly

Dream, Dream Song, Break Dark, Spring Curtain, any Ether Curtain, follow-up
readiness, and Ultimate collision count are current-state inputs. The static
calculator does not replay time, cooldowns, curtain extension, dream-resource
consumption, or the 8-second follow-up lockout. Lucia's Ether corruption is a
separate static anomaly result: 20 ticks at 62.5% each over the 10-second
assumption; max-duration Disorder uses `450% + 20 × 62.5% = 1700%`. These use
the Ether anomaly/disorder calculators with no standard crit or penetration
force contribution.

## Dialyn (`character:1481`)

### Nanoka source and packaged panel

The raw record is retained in `core/data/characters/dialyn.json` from
`https://static.nanoka.cc/zzz/3.2/zh/character/1481.json`, with the live `3.2`
version and URL recorded in the file. The index confirms name 琉音, code Dialyn,
source rarity field `4` (displayed as S by this project's catalog), Break specialty,
Physical base element, and `IconRole54`. Its reviewed level-60 panel is HP
`8250.5871`, attack `758.2048`, defense `612.6038`, impact `110`, crit rate
`0.194`, crit damage `0.50`, anomaly mastery `94`, anomaly proficiency `93`, and
energy recovery `1.20` before equipment.

Core impact reads Dialyn's **initial** crit rate: `min(max(initial crit rate -
0.50, 0) × 100 × core coefficient, 100)`, where the per-one-percent
coefficient rises from `1.4` at Core 1 to `2.0` at Core 7. For example,
initial crit `0.80` at Core 7 adds `60` impact. Later settlement crit changes do
not change this value.

### Good Review and malicious complaint

Good Review is exposed as a current-state input. Its damage bonus, Cinema 1
resistance ignore, and Cinema 4 self attack bonus are available only when the
Additional Ability is team-eligible (another Attack or Rupture teammate is
present). Cinema 4's attack bonus is `+500` to Dialyn's own settlement panel;
Good Review's team damage bonus is `+40%`; Cinema 1 ignores `15%` of all
attribute resistance.

Malicious Complaint is another current-state input. When it is active and the
enemy is stunned, the Core stun vulnerability bonus is `15%` through `30%` over
Core levels 1–7, with an additional `20%` from Cinema 2. Cinema 2 separately
adds `15%` normal damage bonus against a complained-about enemy for every team
member, regardless of which character or damage type produced the hit. The
calculator does not extend stun duration or replay complaint expiry.

### Previous teammate and Guessing Game identities

The Additional Ability source gives an extra `320%` of an Attack teammate's
attack or `400%` of a Rupture teammate's penetration force for the three
Rock/Scissors/Paper EX hits. It identifies the source as Dialyn's “previous
teammate,” but the request contains only the primary and supporting character
IDs, with no ordered active-party history or typed previous-teammate reference.
It also does not fully identify the generated hit's damage dealer, element, or
crit owner. Only this added hit is blocked on a selected Stone, Scissors, or
Paper EX calculation; the known EX damage and other buffs remain available.
The unresolved diagnostic preserves both source formulas.

The raw Guessing Game entry gives unique, numbered stage curves `1481005`–
`1481008`, while its prose says there are up to two stages after Stone or
Scissors. Each numbered curve is a separately selectable damage entry, with
its exact source label and value. The source does not assign which two numbered
curves belong to each preceding move or how the two pairs aggregate. The
implementation does not infer those pairings or combine their values.

### Cinema 6 AfterSound and static resource states

Cinema 6 states that a teammate who entered through Dialyn's forced-Ultimate
Core effect receives AfterSound; that teammate's hits can trigger one extra
Physical hit by Dialyn. The calculator requires a typed Support Entry actor
fact for the selected hit and matches the actual damage dealer against that
actor. It never infers the holder from `current_operator`. The raw gives no
named MoveId for that independent hit, so its event keeps `move_id=None`; its
confirmed `SPECIAL_ATTACK` group and EX Special damage tag
remain explicit. The derived event uses Dialyn as dealer, current attack and
crit owner, and an explicitly selected `0`–`12` hit count. The `1`-second
interval is not simulated. Count zero adds no event; without a count, only the
selected C6 hit path is partial.

Good Review, Malicious Complaint, AfterSound ownership/hit, and the two
Guessing Game numbered states are current-state inputs. The calculator does not
replay Good Review point generation or its 15-second duration/extension,
Rock→Scissors→Paper EX transitions and their 8-second windows, complaint
accumulation/expiry, review-triggered chain windows, C1 review accumulation,
C4's opening `20` energy or `180`-second limit, or Cinema 4's `100` decibels.
These non-damage resource and timing gaps are surfaced as non-blocking rule
diagnostics. Defensive Assist source entries contain daze multipliers but no
damage multiplier and are not fabricated as damage events.

### Static Physical Assault and Disorder

The two additional selectable entries are the shared static Physical Assault
and Physical Disorder paths. Assault uses multiplier `7.13`; the calculator
creates its anomaly record under the single-character, full-gauge static
assumption and applies `NoCritRule`. Disorder uses the same typed physical
anomaly record, with a `4.5` base multiplier plus `0.075` per selected remaining second (0–10,
default 10), also with `NoCritRule`.

Core's initial-crit-to-impact bonus is applied to Dialyn's settlement panel
before the static anomaly record is assembled, so the record retains the
resulting impact strength. Cinema 2's all-unit `+15%` is received as a matched
`DAMAGE_NORMAL_BONUS` during record generation and is incorporated once in the
anomaly effect-strength normal region. The Anomaly and Disorder calculators
then use that historical strength without applying a second generic bonus.
For Attack `1000`, anomaly proficiency `100`, level `60`, and Physical bonus
`0.30`, the C2 bonus changes the record's normal region from `1.30` to `1.45`
and effect strength from `2600` to `2900`.

### Vivian (薇薇安, character:1331)

Vivian's raw record is the live Nanoka 3.2 file at
`https://static.nanoka.cc/zzz/3.2/zh/character/1331.json`. The earlier pinned
3.2.4+18409985 character path returned 404; this implementation retains the
retrievable source URL/version on the raw record without changing any existing
character source version.

The static Ether Corrosion entry uses the specification's complete 10-second
record: 20 ticks at `0.625` each. The separate static Disorder entry uses the
matching full-duration `17.0` multiplier. The Extra Ability's team Corrosion
and Corrosion-settled Disorder bonuses are independent of whether Vivian has a
Protective Feather available for the follow-up hit.

The source marks Feather Flurry, Feather Blade Counter, Silver Aria, and Quick
Assist: Feather Guard as both Physical and Ether damage, but supplies one
combined curve for each hit and no per-element shares. Those entries retain
their exact raw parameter identity and curve text, but a selected hit returns
an ambiguity diagnostic instead of assigning the entire multiplier to one
element. Other single-element moves remain calculable.

Cinema 6 only specifies the maximum Anomaly Mutation ratio: five spent
Protective Feathers make it five times the base ratio. The mapping for one to
four feathers is absent. The maximum case is calculable; selecting the
intermediate-count condition blocks only that mutation event with an explicit
diagnostic. Other known Cinema 6 effects continue to apply.

Prophecy deals 55% ATK Ether damage every 0.55 seconds while the target remains
anomalous. The calculator requires an explicit integer tick count and does not
derive a count from duration. Feather gains/consumption, stance changes, the
0.5-second extra-ability throttle, and Prophecy end timing are not replayed;
the relevant current states are exposed as explicit inputs.

Anomaly Mutation is emitted as a typed Discharge event sourced from the exact
typed historical Attribute Anomaly record. That record supplies its own
effect strength, element, stored anomaly bonus, and damage owner; Vivian's
current anomaly proficiency supplies only the Discharge multiplier. Cinema 2's
1.30 proficiency gain and 15% resistance ignore are separate enabled rules and
match only these Discharge events. This uses the dedicated
`DISCHARGE_PROFICIENCY_MULTIPLIER` node and leaves the existing
`ANOMALY_MUTATION_COEFFICIENT` meaning unchanged.

The direct Feathering Blossoms entry does not carry the target's existing
anomaly-record identity in the current calculation request. If the selected
direct Blossom is marked as hitting an anomalous target, the hit remains
calculated and the mutation child reports `MISSING_DATA`; the compiler does
not recalculate the target anomaly from Vivian's panel. Selecting a typed
Attribute Anomaly event as the source allows the mutation to use that exact
record.

Cinema 4's 12% ATK buff lasts for 12 seconds after either named Basic hit, so a
separate current-buff condition controls Vivian's formal self panel. It is not
coupled to Prophecy. Cinema 6's 40% Ether bonus is applied through the ordinary
normal-damage input when a Vivian-owned Ether/Xuanmo anomaly or Disorder source
record is generated. The Disorder calculator uses that historical strength
without a second normal-bonus region. The bonus is not copied to the independent
Discharge bonus region, and explicit historical records or another character's
source record are not rewritten.
