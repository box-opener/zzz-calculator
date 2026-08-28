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

The current Stage18-2 slices additionally include reviewed max-level data for
the Ye Shunguang signature W-Engine `14143`, Astra signature W-Engine `14131`,
and the Stage18-2.5 attack/support validation set. Their static panel
contributions and reviewed damage-relevant combat Effects enter the existing
Build Assembly / Matcher / Execution pipeline; non-damage resource effects are
retained in raw source text but are outside the current damage scope.
Non-max-level W-Engine values are intentionally not part of this slice and
produce an explicit diagnostic.

Natural-language parsing and full event dispatch remain outside this stage;
the existing direct-damage calculator, matcher, and reviewed character/build
compilers are reused by the W-Engine validation slice.

## Tests

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest
```
