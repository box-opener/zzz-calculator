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

There are no damage calculators, event dispatchers, Effect matchers, character
data parsers, or natural-language parsers in this ticket.

## Tests

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest
```
