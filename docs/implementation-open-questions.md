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

## Zhao (照, `character:1341`)

### Nanoka source and level-60 HP layers

The lossless raw record is the live Nanoka 3.2 source at
`https://static.nanoka.cc/zzz/3.2/zh/character/1341.json`. It identifies Zhao
as an Ice Defense character. At level 60, the white HP value is `9117.4144`;
raw `extra_level[6].extra[11102]` contributes another 18% in the same
out-of-combat percentage layer as equipment. With a 30% HP Drive Disc main
stat, the real build is `9117.4144 × (1 + 0.18 + 0.30) = 13493.773312` before
flat HP. The preview provenance retains white HP, the raw 18%, and the disc
percentage as separate sources. A bare panel therefore resolves to
`10758.548992` HP after the character's 18% contribution.

### Skill curves, charge damage, and stat sources

The Fifth Basic and Ultimate source parameters explicitly combine source IDs
`1341005 + 1341006` and `1341014 + 1341023`; both component curves are kept in
the move text and their same-level values are added. C3 and C5 raise the
effective Basic, Dodge, Special, Chain, and Assist skill levels by two each;
Ultimate is not raised by them. Dash Attack has one source curve for combined
Physical and Ice damage but no per-element split, so only that selected entry
is blocked as ambiguous.

The Core Crit Rate conversion reads Zhao's **initial** Max HP at 0.8% per 1000
HP at Core 1, increasing to 1.4% at Core 7. Cinema 6 multiplies that converted
gain by 1.25 only when its rule is enabled. Spring Curtain's team `+5%` Max HP
uses a separately selected current state; its 50-second team Attack increase
has its own current-state input. The former can increase current Max HP used by
charge damage without changing the initial-HP source used for Crit Rate or the
Additional Ability.

The Additional Ability is eligible with another Attack, Anomaly, or Support
character. Its current-state input means that Zhao herself is under any Ether
Curtain. The team damage bonus starts at `+10%`; Zhao's initial HP above 15,000
adds `+1%` per 400 HP, capped at `+40%` total. Cinema 1's team resistance
ignore and Cinema 2's owner `+20%`/other-character `+15%` Attack buffs require
their own current-state inputs. The Cinema 2 panel effect targets every active
teammate except Zhao and uses each recipient's own initial Attack.

Cinema 4's `+40%` Crit Damage is limited to Final Judgment, Chain, and Ultimate
damage, including the HP component attached to each of those same moves; it
does not apply to Support Follow-Up. The three named Final Judgment, Chain, and
Support Follow-Up finishers can each receive an HP damage component based on
current Max HP: `(0.12 + 0.01 × effective Basic level) × selected whole
seconds`, from zero through five. The component keeps its parent's real MoveId,
skill group, tags, Zhao dealer and Crit owner, Ice element, and Standard Crit
rule; creation provenance distinguishes it from the move's ATK component.
Cinema 6 multiplies only that component by `1.40` when its rule is enabled. At
effective Basic level 16, the per-second ratio is `0.28`, or `0.392` with that
Cinema 6 rule. Charge accumulation and consumption timing are not simulated.

### Static Ice anomaly and non-damage state limits

The separate static Ice entries assume one complete anomaly gauge and use
`NoCritRule`: Shatter uses `500%`; Disorder uses the default `450% + floor(t) × 7.5%`,
where the user-selected remaining duration is an integer from zero through ten
seconds and defaults to ten. Anomaly strength uses the current reviewed panel
and ordinary damage bonus once when the historical static record is created.

The calculator exposes current Frostbite, Curtain, C1, and C2 states rather
than replaying their accumulation, opening, expiry, 3-second hit throttle, or
180-second limit. Healing ticks, current-HP costs, Decibels, automatic Quick
Assist ordering, and preserved-charge timeline effects remain non-damage
resource gaps with non-blocking diagnostics.

## Qingyi (青衣, `character:1251`)

### Nanoka source and level-60 panel

The complete Qingyi record is the live Nanoka 3.2 source at
`https://static.nanoka.cc/zzz/3.2/zh/character/1251.json`. It identifies an
Electric Stun character in faction 7. The reviewed level-60 panel includes the
raw `extra_level[6]` Attack `+75` and Impact `+18`, yielding HP `8250.5871`,
Attack `758.2048`, Impact `136`, Anomaly Mastery `94`, and Anomaly Proficiency
`93` before equipment.

### Current Impact conversion, Subjugation, and the chain hit

The Additional Ability is eligible when another Attack character is on the
team or another teammate has the same Nanoka faction ID. If eligible, Qingyi's
current Impact above 120 adds `+6` Attack per point, capped at `+600`. This is a
formal self Panel effect sourced from the current settlement Impact after
equipment and other panel effects. For example, the base Impact `136` adds
`+96` Attack; the supported W-Engine Soul Lock case moves current Impact to
`163.2`, which adds `+259.2` Attack while the equipment-built base Attack stays
`1471.2048`.

The Core effect and Cinema 2 both read one selected current Subjugation count
from 0 to 20. At Core 1 each layer adds `2%` target Stun Vulnerability; this
grows to `4%` at Core 7. Cinema 2 raises that per-layer value to 135% of its
original value when enabled. The standard Calculator applies Stun Vulnerability
only while the enemy is stunned. Chain damage separately adds `3%` normal
damage bonus per current Subjugation layer, whether or not the enemy is stunned.
The calculator does not replay finisher stack application, each dash's extra
layer, Perfect Dodge layers, the Normal/Elite doubling rule, or stack reset
when stun ends. The selected count represents the current enemy status.

The Additional Ability's `+20%` Basic Daze and Cinema 2's conditional `+15%`
Daze at max Subjugation are not included in damage totals because the current
`calculate_payload` path returns damage only and does not instantiate Daze
outcomes. Raw Prop 1002 Daze curves, including the three Defensive Assist curves
that have no damage parameter, remain in the lossless raw record; the
implementation creates no false Direct events for them.

### C1, Flashover, Cinema 6, and static anomalies

Cinema 1's current-target status applies `15%` Enemy Defense Reduction to all
teammate damage and a separate `+20%` event Crit Rate to Qingyi Direct hits
against that target. Flashover's excess voltage over 75% is a selected integer
from zero to 25 percentage points. Each adds `+1%` in the move's normal damage
bonus region to the Moon Turn components; it does not multiply the source skill
curve. The separate `+0.5%` Daze coefficient is outside the damage output.

Cinema 6's `+100%` Crit Damage is event-stat scoped to Qingyi's Moon Turn move;
it does not change her formal Crit Damage panel. The all-attribute `-20%`
resistance effect is represented as a current target status with no damage
event filter, so any teammate's later damage can benefit. The calculator does
not infer either status from the selected attack or model its 15-second expiry.

Static Electric anomaly uses the specification's full 10-second Shock record:
10 ticks at `125%` each, all under `NoCritRule`. Electric Disorder uses the
default `450%` base plus `floor(t) × 125%`, where selected remaining time is an
integer from zero through ten seconds and defaults to ten. These route through
the shared typed AnomalyRecord, Attribute Anomaly, and Disorder templates;
Core stun vulnerability and Cinema 6 resistance reduction are applied by the
same generic calculator path.

### Curves whose hit relation remains unresolved

The Basic: 一煞 prose says that its sequence causes both Physical and Electric
damage but the raw record gives one damage curve per displayed stage without
per-element shares. The implementation retains each source curve and blocks
only the selected Basic stage with an explicit ambiguity diagnostic. It also
keeps source `1251002`, labeled “一段伤害倍率（派生）”, separate; the prose does
not establish which action or hit it replaces or adds.

Moon Turn gives distinct rush `1251008` and finisher `1251009` curves, and its
prose says there are five rush attacks. The source does not identify whether
`1251008` is a per-rush ratio or the aggregate five-rush ratio. The rush curve
and isolated final-hit curve are preserved as separate entries; selecting the
full sequence is blocked with both plausible total ratios shown. No count is
multiplied into the curve by assumption.

The EX Special base parameter explicitly adds curves `1251011`, `1251021`,
and `1251022`; that source sum is calculated at the effective Special level.
Holding the button can consume additional energy to increase turn-in attacks,
but the text does not map that extension to a repeat count and another curve.
Selecting the extra-turn state keeps the known base event and reports
`MISSING_DATA` for only that extension branch.

Cinema 3 and 5 each add two levels to Basic, Dodge, Assist, Special, and Chain;
Ultimate receives neither bonus. The compilers apply these to the raw curves
before event construction, up to effective level 16. The calculator does not
replay Flashover charge, entry restoration, interruption level, shields,
support-point consumption, energy refreshes, or battle durations; those limits
have non-blocking diagnostics where they affect the selected rule.


## W-Engine live 3.2 first queue batch (non-authoritative implementation notes)

Source order is the insertion order of Nanoka's live 3.2 W-Engine index. The first
ten previously uncovered rows are `12001`–`12005`, then `12007`–`12011`; the
existing `12006` entry stays in place and is not duplicated.

`「月相」-朔` (`12003`) preserves R1–R5's one-shot Energy restore on its raw talent
source and an effectless, source-linked RuleItem. The current `calculate_payload`
contract has no current Energy resource result. Its selected RuleItem reports a
non-blocking `UNSUPPORTED_CALCULATOR` diagnostic quoting the selected refinement;
it is not converted to Energy Regeneration and does not change the damage result.
The static equipment preview likewise reports the limitation.

`「湍流」-铳型` (`12007`) and `「湍流」-矢型` (`12008`) put their reviewed
R1–R5 values in the typed Daze outgoing modifier lane. The damage request does not
emit Daze results, so the selected RuleItems retain non-blocking diagnostics and
do not alter damage totals. This describes the result-contract boundary, not a
missing numeric source value.

Several passives specify a duration and/or cooldown. This static request does not
replay event timing; their active period is represented by a user-selectable
current-state condition. `「残响」-Ⅰ型` and `「残响」-Ⅱ型` additionally say that
same-name passives do not stack. Copies with matching resolved values apply once
across the active team. When copies with different refinements are simultaneously
enabled and active, no source priority is stated; the application skips all
members of that non-stacking panel group and emits a blocking local ambiguity
diagnostic instead of selecting the first or largest value. This does not block
single-copy use or same-refinement duplicates.


## W-Engine live 3.2 second queue batch (non-authoritative implementation notes)

The second ten uncovered index rows are `12012`–`12016` and `13001`–`13005`.
R1–R5 numeric values are extracted independently from each raw talent description.
`12016`'s source `base_property.name` is `基础防御力` with value 19. The live
index's level-60 value is normalized as white Defense 282 (the index's generic
`atk` key is not treated as Attack for this row); its 32% secondary Defense
contribution then aggregates in the same percent layer. The domain has a typed
Vanguard role but no registered Vanguard character, so the compiler preserves
this build/effect mapping without claiming an actual `calculate_payload` path.

`12012` says `队伍中任意角色对敌人施加属性异常效果时，装备者回复5.5点能量` at
R5. Its penetration-rate Build contribution and source-linked resource rule are
retained, but the current request has no Energy resource result; the selected
RuleItem reports a non-blocking diagnostic and applies no substitute stat.

`12014` says `受到敌方攻击时，攻击者造成的伤害降低10%，持续12秒` at R5. This
is an enemy outgoing-damage effect. The current request calculates player damage
only, so it keeps the source RuleItem and a non-blocking diagnostic; it does not
map the effect onto player outgoing damage or an enemy defensive modifier.

`13002` says team Dodge Counter, EX Special, Assist Attack, and Chain Attack each
grant distinct Decibel amounts, and the wearer recovers Energy; it also says the
four cooldowns are independent and same-name passives do not stack. Those resource
results remain in the raw/refinement mapping with a non-blocking diagnostic
because neither Decibel nor Energy has a result contract here.

Current stacks and active-state buffs are explicit inputs where their numeric
results are known: `13001` uses 0–3 charges on the wearer's Ultimate; `13003` uses
0–10 current attack stacks; `13005` uses 0–8 current Impact tiers. Event ordering,
Energy history, and per-stack expiration times are not replayed. `12013`, `12015`,
`12016`, and `13004` likewise expose the current buff-active state rather than
simulating hits, swaps, or durations.


All live W-Engine advanced properties use the max-star source growth factor
`1 + stars[5].rand_rate / 10000`. Percent-formatted values are then divided by
10000 to become ratios; flat-formatted values retain the grown flat number. This
corrects the previously shipped `12011` flat Anomaly Proficiency from 24 to 60
and models `13003` as 75, while keeping raw source values and star-growth fields
unchanged. A regression derives the expected normalized result for every live
3.2 fixture, covering both percent and flat formats. Thus `12011` with base AP
100 and an active R5 +40 buff resolves to AP 200; `13003`'s max-level static AP
contribution is 75 before its energy-stack attack buff.


## W-Engine live 3.2 third queue batch (non-authoritative implementation notes)

The next ten rows in Nanoka index order are `13006`–`13015`. Their live detail
payloads and each R1–R5 description are preserved in the raw fixtures. The
max-star static values use each fixture's raw `stars[5].rand_rate` growth, including
flat values; the R1–R5 passive values are parsed independently from each talent.

`13006`'s source conditions its outgoing Daze bonus on target HP being at least 50%
and adds the same amount at 75%. Both thresholds are explicit current target states;
the request keeps each modifier in the Daze lane. Since damage requests do not
calculate Daze, the selected rules carry a non-blocking result limitation.

`13007`'s always-on maximum HP bonus and its 12-second Impact increase after being
hit are separate effects. The latter uses an explicit “after hit Impact buff active”
state; it is not gated by a shield. `13008`'s Anomaly Proficiency stacks are also a
current count from 0 to 4. The request does not replay individual stack expiry or
cleanup timing.

For `13009`, the source says `当场上存在处于属性异常状态下的敌人时，装备者的攻击力提升…，对目标造成的伤害额外提升…`.
The field condition independently activates the owner's Attack panel bonus. When
the current damage target is anomalous, the target damage bonus is unambiguous. If
another enemy is anomalous but the current target is normal, the source does not
resolve whether “对目标” means only an anomalous target or any target while the
field condition holds. That precise state produces a branch-local blocking
`AMBIGUOUS_TEXT` diagnostic; unrelated moves and the Attack panel remain available.

`13011` says `受到敌方攻击时，装备者的能量获得效率提升…；装备者换回后场时，该增益效果将传递给当前操作中的角色`.
The current request has no incoming damage or resource result and does not provide a
typed recipient for the swap transfer. Its original descriptions and R1–R5 values
remain attached to a source-only rule with a non-blocking limitation; it does not
create Energy Regeneration or alter player outgoing damage.

`13012` uses separate current states for the post-EX Crit Damage panel buff and a
below-half-HP target at the time of the EX hit. `13015` likewise uses one current
state for its EX/Chain Attack buff and a second state for the extra amount earned
when the target was anomalous at trigger time; it does not infer the latter from
the target's later settlement state. `13014` applies its current 0–3 stacks only to
the owner's Penetration Force lane.


## W-Engine live 3.2 sixth batch: result-lane limitations

This batch adds `14003`, `14105`, `14107`, `14109`, `14110`, `14114`, `14116`,
`14117`, `14118`, and `14122` from the exact live Nanoka catalog order. No new
game-text identity or multiplier ambiguity was found. The limitations below are
calculator result lanes that the current request does not produce; each keeps its
source rule and a non-blocking diagnostic while the known panel or damage effects
remain active.

`14003` says `每层充能效果使招式造成的失衡值提升`. Its EX Special Daze modifier
is typed and matched, but the damage request has no Daze result. The explicit
0–6 charge selection represents the current pre-cast count; accrual, consumption,
and elapsed-time history are not replayed.

`14107` says `装备者施加的护盾值提升` and also grants team Daze after a teammate
triggers `破招` or `极限闪避`. Shield strength has no result in the current request
and Daze has no result lane, so these known modifiers stay in their respective
typed paths with a non-blocking diagnostic. The current team damage buff continues
to calculate from its selected active state.

`14114` raises Basic-attack damage and Daze per active stack. Its ordinary damage
effect is applied to Basic-tagged events; the Daze modifier remains typed but has
no result lane. The active 0–5 count is explicit; same-move trigger caps and
eight-second stack expiry are not replayed.

For `14117`, the source grants AP when a damage stack is gained while the stack
count is at least five. The current AP increase therefore has its own
`anomaly-proficiency-buff-active` state, separate from the current damage-stack
count, so a previously triggered AP buff can remain active after the count falls.
This records the known trigger relation without replaying its stack-generation
rate, doubled backline generation, internal cooldown, or six-second timer.

`14122`'s Disorder damage effect checks the wearer's formal current AP at the
375-point inclusive threshold and requires that the wearer be the typed Disorder
triggerer. Its Electric buildup effect is capability-gated; the current registry
has no Electric-capable Anomaly owner, so no actor is invented to exercise that
branch. The source's 15-second AP buff is represented as an explicit current state.


## W-Engine live 3.2 seventh batch: capability and result boundaries

This batch covers `14125`, `14126`, `14129`, `14130`, `14132`, `14133`, `14134`,
`14137`, `14138`, and `14139` from the live index. Each complete detail JSON and
each refinement's original text are retained. The R1–R5 values use the corresponding
refinement, not a copied R1 value.

`14125`'s team damage effect is unique. A separate active state represents a
qualifying Tea Power stack gain at 15 or more; the current stack count does not
recompute whether its ten-second team state has expired. Same-refinement copies
apply once. When duplicate holders have different refinement values, the shared
non-stacking guard blocks that local event effect with an ambiguity diagnostic
instead of choosing an instance.

`14129`, `14130`, and `14132` retain their always-on Crit Damage/Crit Rate panels
when the owner lacks the event capability required to trigger their timed state.
Their activation requires Ice damage, Fire Follow-up Attack damage, and Fire
Chain/Ultimate damage respectively. The current Attack roster has no such Ice or
Fire trigger source, so those specific RuleItems are ineligible rather than
checkbox-enabled on an incompatible owner. `14138` likewise keeps its Crit Damage
and stack panel while its full-stack Electric branch is ineligible for the
registered Attack owner.

`14133` separates the general wearer Anomaly Buildup Efficiency effect from the
Ether-hit AP stacks, which are eligible only when the owner can produce Ether
damage. `14134`'s source advanced property is HP% (`rand_property.name` is `生命值`),
while its points-per-second Energy increase remains a flat current Energy
Regeneration contribution. Its team Crit Damage state requires the registered
`zhao-ether-curtain` mechanism; the permanent team Attack/HP panel effect is
independent of that state.

`14139`'s Daze modifier remains typed on EX Special, Chain, and Ultimate events,
but the request has no Daze result; a non-blocking diagnostic preserves that
limitation. Its unique team damage stacks are separate current state after an
eligible Fire Chain/Ultimate trigger. The registered Stun roster has no Fire-capable
owner, so that team-buff RuleItem is ineligible and does not invent a Fire event.


## W-Engine live 3.2 fourth queue batch (non-authoritative implementation notes)

The next ten uncovered index rows are `13016`–`13021`, `13101`, `13106`, `13108`,
and `13111`. Each fixture keeps its complete live detail JSON and each R1–R5 source
description; static advanced properties use the max-star growth present in that
same raw detail.

`13016` says `队伍中角色生命值大于等于50%，受到的伤害降低…，受到的[秽息浸染]值降低…，该效果全队唯一`.
Both reductions remain on an effectless source RuleItem with a non-blocking
diagnostic because the request cannot calculate received enemy damage or Malaise
Infection accumulation. It does not choose a team HP recipient or synthesize an
incoming result.

`13017` and `13021` are Vanguard engines, a role with no registered character
calculation path. Their source/index level-60 white values are Defense 356, so the
fixtures store typed white Defense rather than reusing the catalog's generic `atk`
field as Attack. The compiler retains `13017`'s Defense and its EX Special active
Defense state, and `13021`'s current-crit-rate-over-100% damage formula, for direct
domain/build validation without inventing a Vanguard roster member.

`13018`'s anomaly-target damage bonus is calculated from an explicit current-target
Anomaly state. Its Disorder-triggered Energy restore stays in a source-linked,
non-blocking RuleItem because Energy has no result contract. `13019` takes one
current 0–3 stack selection: each stack applies its ordinary damage bonus and the
Crit Rate panel effect is tied to that same RuleStackCondition at exactly three.
Its 20-second duration and 0.5-second trigger interval are not simulated. `13020`
uses a current Assist Attack buff state for its wearer Daze and ordinary damage
bonuses; the Daze modifier is traced while its missing result remains non-blocking.

`13101`'s Electric damage increase is implemented in the element damage bonus lane.
Its Dodge Counter/Assist Attack Energy Recovery Efficiency buff is a current-state
source rule with a non-blocking resource-result diagnostic. `13106` applies its
flat Energy Regeneration panel amount only when its owner is not the request's
current operator, matching the active-team structure. It does not accept a
condition toggle that can label an on-field wearer as being in the backline. Its
0–15 Physical damage stacks remain an independent explicit current count. `13108`
records the greater-than-six-
meter Basic/Dash hit as the trigger for an active current-target buff; the stored
Physical damage bonus is applied to subsequent Physical damage events from that
wearer without retesting settlement distance or requiring the later event itself
to be Basic/Dash. `13111` scopes the active effect to the owner's Basic/Dash Electric
damage tags. The registered Attack-role roster has no Electric-capable owner, so
the compiler marks the effect ineligible for those owners instead of fabricating an
Electric character; its 15-second internal cooldown is not replayed.


## W-Engine live 3.2 fifth queue batch (non-authoritative implementation notes)

The next ten uncovered catalog rows are `13112`, `13113`, `13115`, `13127`, `13128`,
`13135`, `13142`, `13144`, `14001`, and `14002`. `13103` remains the already
supported row between batches, so this batch follows the actual insertion order.

`13112` says `受到敌方攻击后，下一次攻击命中敌人时，额外造成装备者960%防御力的伤害，且必定触发暴击` at R5. The incoming-damage reduction remains a source RuleItem because no incoming result exists. If the explicit “this attack triggers the ready proc” condition is selected and the wearer is the actual damage dealer, a typed EventCreation branch emits a blocking `AMBIGUOUS_IDENTITY` diagnostic: the guaranteed crit and DEF coefficient are known, while the added hit's element, damage type, MoveId/skill identity, and crit-stat owner are not. No trigger-move identity is fabricated, and the ordinary attack remains known.

`13113` has an Ice damage bonus and a separate EX-triggered, current 0–4 TEAM Attack stack. The Ice effect is capability-gated; the current registered Support owners do not gain it unless their typed capabilities include Ice. The group uses a stable same-name non-stacking key across owners. `13115` likewise applies an explicit 0–4 aggregate TEAM Attack stack with a one-layer-per-friendly-unit source cap and a stable non-stacking group. The active stack count and contributors are not replayed from attacks; no untracked Bangboo or fourth teammate is synthesized. Its one-shot Energy result remains a non-blocking source-rule diagnostic.

`13127` separates shield-gated flat Energy Regeneration from the unconditional EX Special/Assist Attack anomaly-buildup efficiency bonus. `13128` exposes its three random effects as independent current-state rules—Attack, Anomaly Proficiency, and buildup efficiency—because the source explicitly allows multiple outcomes to coexist; no random result or 0.3-second cooldown is replayed. `13135` treats Follow-up Attack as the trigger only; its later Physical damage and Daze effects are not restricted to the current move being Follow-up. Its Daze result is outside the current damage output and has a non-blocking diagnostic. `13142` scopes damage bonus to EX Special and Ultimate tags; Energy recovery remains source-only.

`13144` has a Fire damage bonus and a separate owner HP-loss current-state Crit Rate panel buff. The Fire branch is capability-gated; the registered Rupture owner does not have Fire damage capability. `14001` keeps the permanent Attack panel bonus. Its 200%-ATK extra damage on a critical hit is a separate local unresolved-child branch when the explicit current proc fact is selected, because the source does not identify the extra hit's element, damage type, MoveId/skill identity, or crit-stat owner; its refinement-specific cooldown is not simulated. `14002`'s current target-specific all-team Crit Rate increase is an event-stat modifier for standard-crit Direct/Penetration events, so it does not alter formal team Crit Rate snapshots or No-Crit Anomaly/Disorder results. Its same-name stacking group is stable across equipment owners; differing active refinements block that target-scope effect instead of choosing a copy.

## W-Engine live 3.2 final batch

### 14151 霓虹妄想: scope of the uniqueness phrase

The R1 text ends: `拥有2层效果时，装备者的异常精通额外提升<color=#2BAD00>60</color>点，该效果全队唯一。` The uniqueness phrase could apply to the immediately preceding full-stack Anomaly Proficiency bonus or to the stack effect as a whole. Multiple simultaneous holders and differing refinements are not represented by the currently registered Stun owners, which have no Ether Basic/EX capability. The reviewed compiler keeps the known TEAM damage stack and owner Proficiency effect as separate typed effects; this implementation note does not resolve the phrase's multi-holder scope.

## Anby (`character:1011`)

The live-3.2 raw record, exact direct move curves, core/cinema text, and static Electric anomaly/Disorder entries are retained. The calculator can apply Anby's reviewed Daze modifiers to the Daze node, but the current request has no Daze output. Cinema 1's Energy Gain Efficiency and the 7.2/3-point Energy restoration effects are preserved as source-linked non-blocking diagnostics because the current request has no Energy resource result; these effects are not represented as Energy Regeneration. Cinema 6 is an explicit 0–8 pre-hit charge state, with +45% ordinary damage when a positive charge is available; charge timing and per-hit consumption are not replayed. The UI portrait uses a neutral placeholder because the source `IconRole01` art is not packaged in this repository.

## Nekomata (`character:1021`)

The full raw payload is preserved from live Nanoka 3.2. The compiler intentionally uses only raw core records `1021501`–`1021507` whose `potential` is `[0]`. The source `potential_detail` labels `102100`–`102105` as 猫的报恩 I–VI / 潜能觉醒, and its alternate passive records `1021508`–`1021514` describe additional potential-only effects and moves. The character/build configuration has no Potential selector, so those variants remain uncompiled; they are not reinterpreted as Cinema.

The base-potential source says `发动最后一段斩击时，有33.33%的概率重复攻击三次` for Cat Claw and `招式发动时，有33.33%的概率重复攻击三次` for Red Blade. The matching raw attack curve describes the main move but provides no separate curve or identity for the repeated attacks. The regular hit calculates normally. If the calculation explicitly selects that a repeat occurred, an exact event-template-filtered child branch reports `AMBIGUOUS_TEXT`; it does not assume the repeated attacks inherit the main multiplier or estimate expected damage from the probability. No blocking diagnosis appears for other Cat Claw stages.

Cinema 1's 16% Physical resistance ignore is matched to Nekomata's Direct Physical attack events, because its text requires an attack hit from behind; separately settled static Anomaly/Disorder records are not treated as attack hits. The actual target stunned state supplies the source's back-hit rule and excludes a second application through the manual back-hit condition. Cinema 2's single-enemy/front-field Energy Gain Efficiency has no Energy resource result in the request and remains source-only; it is not represented as Energy Regeneration. The raw Support Parry parameters are Daze curves, not damage curves, so they remain preserved source data without fabricated Direct entries. The local catalog portrait is a neutral placeholder because the raw `IconRole11` image asset is not packaged in this repository.


## Nicole (`character:1031`)

The live source says EX Special, Chain, and Ultimate create an Ether Energy Field that deals damage. It exposes separate `能量场伤害倍率` curves for source IDs `1031106`, `1031303`, and `1031305`; EX Special also has `蓄力伤害倍率` at source ID `1031103`, and its prose says long-press charge deals additional damage. The text does not establish whether each field/charge coefficient is one event or the complete total, or state the number/interval of hits. The reviewed compiler calculates the exact one-shot cannon entries; only when a current field/charge hit branch is explicitly selected does its source-linked child return `AMBIGUOUS_TEXT`. It does not add a field ratio into the cannon's main multiplier or choose a hit count.

The source signature 13103 has two R5 effects from the same Ether-trigger state. The TEAM target damage component uses its stable non-stacking group; the +0.8 Energy Regeneration effect is an independent SELF panel contribution for each wearer. Two active 13103 holders should therefore apply the TEAM damage bonus once while each wearer keeps their own Energy panel increase.

Cinema 1 states that each additional 0.1 seconds of EX charge increases the Energy Field duration by 0.15 seconds, and Cinema 4 increases the field diameter by 3 meters. These source values are retained, but this request has no field duration/area result and no base duration with which to infer hit count, so they do not alter damage totals.
