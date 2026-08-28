# ZZZ Calculator

This branch implements the frozen `spec-v1` documents as a new deterministic
Python core. The legacy calculator is intentionally not part of the working
tree; it remains recoverable from the Git history and the `spec-v1` tag.

Current scope is deliberately limited to:

- domain enums and discriminated unions;
- `Character`, `Enemy`, `BattleState`, `DamageEvent`, `AnomalyRecord`, `State`,
  and `Effect` models;
- calculation-node names and aggregation metadata;
- unit tests for structural invariants.

The current Stage18-2 slice additionally includes reviewed max-level data for
the Ye Shunguang signature W-Engine `14143` and Astra signature W-Engine
`14131`.  Their static panel contributions and reviewed combat Effects enter
the existing Build Assembly / Matcher / Execution pipeline.  Non-max-level
W-Engine values are intentionally not part of this slice and produce an
explicit diagnostic.

There are no damage calculators, event dispatchers, Effect matchers, character
data parsers, or natural-language parsers in this ticket.

## Tests

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest
```
