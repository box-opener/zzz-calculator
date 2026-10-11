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

Enemy `is_stunned` and `stun_vulnerability_bonus` are independent named inputs.
The latter is supplied once by the enemy settlement environment; a character
compiler must not carry a second copy. A veil-like mechanism is represented as
an explicit vulnerability settlement policy for the current event, not as a
replacement of the enemy's base stun-vulnerability value.
