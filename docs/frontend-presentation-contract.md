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
