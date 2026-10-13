# Frontend Presentation Contract v1

This document defines the boundary between the spec-v1 application layer and
the future browser UI. It does not add combat rules.

## Source ownership

Production character source records live under `core/data/characters/` and are
loaded through `core.data.loader`. Tests use the same records. The old frontend
database, old formulas, and old state objects are not calculation inputs.

Character compiler selection, display metadata, config fields, role/element
metadata, and team-derived eligibility are owned by the presentation registry.
The HTTP layer only transports JSON and does not branch on character IDs.

## Input ownership

The browser submits named build, enemy, scenario-condition, integer-parameter,
rule-selection, stack, and trigger-input values. It does not submit arbitrary
Modifiers, Effect objects, BattleEvent objects, or calculator nodes.

STATIC conditions are read-only in the UI. USER_SELECTED conditions and integer
parameters are submitted by stable presentation IDs. Trigger selections are
translated by the presentation layer into internal `ScenarioTriggerFact`
objects; the browser does not construct those facts.

`enabled_rule_item_ids` remains the single source of truth for the user's
enabled-rule selection. Eligibility, condition satisfaction, and trigger facts
remain separate. A rule is toggleable only when the current scenario makes it
available; an ineligible or blocked rule cannot be forced on by the UI.

For the current Direct UI, `primary_character_id` is also the move owner and
the scenario operator. The browser does not submit an independent operator
identity. Character and enemy calculation inputs are explicit; API requests do
not silently substitute demonstration defaults for missing formal values.

Refreshing a Definition after a compile-config change reconciles existing user
choices by stable ID. Valid condition values, parameter values, rule enable/
disable choices, trigger actors, and stack counts are retained; newly exposed
controls use server defaults; removed or out-of-bounds choices are pruned.
Move projections expose their authored damage type and element plus each
variant's `parameter_value_id`, so the browser can display only controls tied
to the selected entry. Duration defaults and validation remain server-owned;
for a selected Ether/Xuanmo Disorder duration parameter, the browser omits an
untouched default so the server can resolve it against the currently enabled
duration rules.

Source-record selectors are shown only for the compiled current entry and
eligible team effects that consume a real anomaly record. For Nangong Yu's Core
Discharge and Polar Disorder, and Promeia's current Core EX, Chain, or Ultimate
Discharge, the browser sends the selected teammate and element variant as named
selector input; the server verifies that the teammate is present and has the
required compiled source template. Promeia's Core selector is exposed only when
the current target-anomaly and Frost-consumed inputs are selected; her Chain
and Ultimate selectors require the target-anomaly input. These selectors do
not imply a new anomaly, trigger effects on an ordinary anomaly query, or
replay combat history. Yanagi's source selector remains scoped to her own Polar
Disorder rules.

Cissia's catalog rank is mapped from Nanoka's raw rank value by the registry,
and her compiled editor defaults are Core 7, Cinema 0, and skill level 12 for
an S-rank agent. Cinema 3/5 also raise Ultimate and obey the shared level-16
cap. Her poison/recent-poison, Snake Shadow, and Cinema 6 proc inputs remain
current-scene selections; EX extra hits and Cinema 4 awareness stacks are
named 0–3 parameters. The browser does not infer poison, energy, stacks, or
proc timing from a combat history. The signature mapping is available to the
W-Engine picker, while the shared editor's unequipped default remains in
effect.

Starlight - Billy's registry derives Extra Ability eligibility from the actual
team (another Stun, Defense, or Support agent). His editor defaults are Core 7,
Cinema 0, and skill level 12; Cinema 3/5 include Ultimate and obey the shared
level-16 cap. Current Motor Suppression, Turbo, Physical resistance-ignore,
Starshine, and Cinema 6 consumed-stack values are named state inputs. The UI
does not infer them from resources, Daze, action history, or timing. The
signature mapping is available to the W-Engine picker under the shared
unequipped default.

Promeia's catalog rank is mapped from Nanoka's raw rank value, and her compiled
editor defaults are Core 7, Cinema 0, and skill level 12 for an S-rank agent.
Cinema 3/5 also raise Ultimate and obey the shared level-16 cap. Her source
selector consumes a teammate's real ordinary anomaly record only for the
current eligible Core/Chain/Ultimate entry; it preserves that entry's element
variant while using the fixed-ratio (non-tick-profile) Discharge contract.
Extra Ability duration defaults follow the selected ordinary Ice or Lieshuang
record (10/20 seconds, or 13/23 while the eligible Extra rule is enabled).
Duration inputs remain server-owned; an untouched default is omitted so the
server can resolve it from current rule eligibility. Frost consumption, target
anomaly, verdict, and Cinema 6 current states are explicit selections, not
reconstructed from combat history. Her signature is available to the W-Engine
picker under the shared unequipped default.

Pyrois's editor defaults are Core 7, Cinema 0, and skill level 12; Cinema 3/5
include Ultimate under the shared level-16 cap. Extra Ability eligibility is
derived from the actual team when another Stun or Support agent is present.
Sunflame/Sunflare and the named Core/Cinema proc states are explicit current
inputs. The left/right Core child packets retain a local partial result because
their source does not define event identity, and Special: Battle Order retains
a local partial because its actor has no registered panel identity. The
14155 signature is available in the picker; its Pyrois-only Ether Resistance
Ignore is a separate current eclipse-state input, with no 45-second or battle
entry/Ultimate timing replay. The editor's current default leaves mapped W-
Engines unequipped.

## Output ownership

The v2 browser may request `substat_analysis` for up to three unique active
teammates. The server selects the S-rank increment from the existing Drive Disc
stat table and runs the same calculation pipeline with one additional typed
Build contribution. The browser never supplies a free-form contribution or
damage multiplier. Baseline and comparison use the same scene, equipment,
selected rules and target. Incomplete modes retain null gains, and a zero
baseline has no percentage ratio. Raw panel Crit Rate is preserved for
conversions; only event Crit probability is bounded during Crit-region evaluation.

Effective-stat selections are display/config metadata. They do not exclude
unselected equipment stats from damage, and flat companion/penetration rolls
remain damage inputs while being excluded from the effective-stat total.
Real enemy choices retain the sourced identity, variant, version and growth
curve; manual overrides are explicit. Missing source resistance values are
identified in the UI rather than described as sourced neutral resistance.

Presentation output is versioned as `presentation-v1`. Three crit-display
executions are kept separately. Each mode owns its own value, known value,
status, diagnostics, and calculation breakdown. Events are aligned only by
`DamageEventSemanticId`, never by array position.

Panel provenance is emitted by the application execution layer as
`PanelModifierExecutionTrace`. The UI displays that source information and
does not infer it from before/after snapshots.

The browser formats values only. It does not perform damage multiplication,
crit calculations, repeat-count multiplication, total aggregation, modifier
matching, or eligibility evaluation.

## Norma (`character:1571`)

Norma is presented as an S-rank Fire Stun agent with Core 7, Cinema 0, and
skill level 12 defaults. Cinema 3/5 include Ultimate and respect the shared
level-16 cap. Her reviewed Direct moves expose the source-backed Core, Cinema,
and current-state inputs; Extra eligibility is derived from another Attack or
Rupture agent, or a teammate sharing her raw faction ID. The level-60-only
Term `1000012` state is separate from Technical Gap stacks, and no character
level selector is exposed. The selected C6 high-explosive missile represents
one current packet rather than a simulated firing sequence. Norma's own
Penetration Force conversion is shown as a localized incomplete result while
the Stun panel contract has no Force stat source; autonomous turret actor
ownership remains a separate local diagnostic.

## Sigrid (`character:1591`)

Sigrid's editor defaults to Core 7, Cinema 0, and skill level 12; Cinema 3/5
include Ultimate and obey the shared level-16 cap. The team derives her Extra
Ability eligibility from another Stun or Support agent, and the level-60 ATK
bonus is fixed at 840 rather than exposed as a character-level slider. Sky
Rider state, its separate eight-second Crit Rate state, Chain/Cinema states,
Winded target state, and current Charge/Cinema 6 inputs are submitted using
their named conditions and parameters. The Core's Stun Vulnerability uses the
enemy's shared `is_stunned` state. The signature mapping is available in the
W-Engine picker; the shared editor continues to start mapped engines
unequipped.

Enemy `is_stunned` and `stun_vulnerability_bonus` are independent named inputs.
`stun_vulnerability_bonus` is an additive bonus: a sourced total multiplier of
150% (`stun_multiplier=1.5`) becomes 50% (`stun_vulnerability_bonus=0.5`). Both
ordinary and endgame targets use this conversion; the editor shows the extra
percentage, and the vulnerability calculator adds the unit base exactly once.
The latter is supplied once by the enemy settlement environment; a character
compiler must not carry a second copy. A veil-like mechanism is represented as
an explicit vulnerability settlement policy for the current event, not as a
replacement of the enemy's base stun-vulnerability value.

## Imported snapshots and equipment drafts

Miyoushe account profiles in `zzz-miyoushe-profiles-v1` are immutable imported
snapshots. Fetching the same UID again replaces that account's entire saved
profile. Loading a character creates a deep independent editor copy, including
skills, weapon, drive-disc substats and effective-stat selections. Edits,
equipment-file imports and clearing discs affect the current configuration.
They never write back to the saved profile. Loading the saved character again
restores its imported configuration. Export uses a timestamped `-copy-` JSON
filename and is labelled as saving a separate configuration.

Build Preview exposes `stat_breakdown` for HP, Attack, Defense, Anomaly
Mastery and Energy Regen. Each value contains `white_value` and
`additional_value`. The server obtains white values from character base stats
plus Build's `white-value` contributions (including W-Engine base Attack or
Defense), and additions from final out-of-combat value minus white. Missing
values remain null. The UI displays the existing total above both components
and colors the addition green; it does not reconstruct stat layers itself.

Each equipped drive-disc card has a delete action, and each character has a
clear-all action. Both update only that character's current drive-disc array
and request an authoritative editor/build refresh, including set counts and
set rule eligibility. Level, weapon and other characters' equipment remain
part of the current configuration.

## Endgame scenes

The offline season endpoints expose pinned formal `3.2` snapshots for `boss`
and `shiyu`. `endgame_selection` names a season, stage, room, target, optional
buff, current integer states, excluded field rules, HP tier and explicit
enemy overrides. The server validates membership and compiles reviewed
clauses; the browser never supplies field Effect objects or multipliers.
Field rules have `environment` provenance and no character owner. Personal
states and role-specific panel effects use explicit team recipients. Global
anomaly source panels and every extra-substat query use that same scene.
`scenario_provenance` records source version/hash, target, buffs, current
facts, overrides and unresolved clauses. Missing resistance values remain
unresolved in endgame calculation until explicitly supplied. HP tier changes
the sourced maximum HP metadata, never the combat level coefficient.
`zzz-scene-config-v1` files store the field/target scene separately from
character equipment files, and reject a different snapshot hash on import.
The team and equipment remain the user's currently loaded configuration.
