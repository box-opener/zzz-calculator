# Frontend Presentation Contract v1

This document defines the boundary between the spec-v1 application layer and
the future browser UI. It does not add combat rules.

## Source ownership

Production character source records live under `core/data/characters/` and are
loaded through `core.data.loader`. Tests use the same records. The old frontend
database, old formulas, and old state objects are not calculation inputs.

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
