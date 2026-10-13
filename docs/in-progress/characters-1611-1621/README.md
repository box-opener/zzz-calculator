# 1611 / 1621 implementation checkpoint — 2026-10-12

Implementation stopped at the user's request. These are unfinished development drafts, not registered calculator support. The last completed character implementation is Sigrid 1591, commit `5fe341715453167161e21a515805876fe4d3206a`, on `codex/characters-from-1411`.

## Saved work

The `core/` and `tests/` directories here mirror their original repository-relative paths. They preserve both complete Nanoka 3.2 raw records, each character's four Python modules, and the draft definition tests. `shared-integration.patch` preserves the nine unfinished shared-file changes for Claret, including the typed sharpened event/template, factory, modifier support, and preliminary registry helper. Those shared changes were removed from the active code after saving the patch, so the running calculator remains at the previously validated implementation.

The archived patch was checked with `git apply --check` against the active code at this checkpoint. Draft modules are deliberately outside the active package and test suite. Copying the mirrored files back and applying the patch is a development resumption step, not a finished installation; the remaining issues below must still be resolved.

## Claret / 克拉蕾 1611

- Complete source JSON and 25 reviewed Electric curves are saved, including the neutral 毁伤 identity. The source-only compiler's seven tests passed before the later shared integration changes. The later typed definition compiled 25 entries/templates, and syntax compilation succeeded; no registered end-to-end API regression was completed.
- The draft uses Vanguard sharpened damage based on Current DEF. Ordinary Crit Damage starts at 50%; the separate source sharp-crit value of 150% must not replace it. Sharp Explosion and sharpened damage are distinct concepts. The typed settlement/crit contract is unfinished, and no damage formula should be guessed.
- Registry helpers exist in the patch, but the registered character entry, source-backed Core/Extra/Cinema rules, signature mapping/14161 eligibility, presentation, and progress coverage are unfinished. The typed event must preserve Electric element and the known multiplier/variant so known scoped modifiers can match. Its current draft still needs review of those fields and event-crit behavior.
- The known Initial Crit Damage to Initial Crit Rate conversion is `Initial CD * 0.35`. Equipment construction and preview must perform this at the correct initial-panel phase and respect rule activation. A caller-supplied final manual panel must not receive the conversion again. Initial snapshots, build preview, and execution must agree; combat-current Crit Damage must not feed the conversion.
- Core's current Crit Rate and named-move damage, Extra's eligibility/sharp-crit effect, C1 毁伤 multiplier, C2 Electric Resistance Ignore, C4 named moves, and C6 derived 毁伤 still need real rule/scope/API tests. Unsupported sharp settlement must remain a localized diagnostic.

## Roxy / 洛克茜 1621

- Complete source JSON and four modules are saved. The first four definition tests passed with 15 Direct entries and no diagnostics before the later Core changes. Those tests verify source identity/provenance, level-12 curves, Cinema 3/5 levels including Ultimate, and the source-defined Basic/Assist tags.
- The subsequent Core implementation was not retested. It still contains a temporary dynamic `ScenarioCondition` import/placeholder and is not a validated compile checkpoint. Extra/Cinema rules, derived cyclone events, registration, signature mapping, and formal scope/API checks are unfinished.
- Initial Energy Regeneration conversion must use the continuous amount above 1.2: each 0.01 adds 5 ATK (cap 960) and 0.4 Impact (cap 76.8). Core's team Crit Damage reads Roxy's own Current Crit Rate with coefficient 0.4, cap 0.4; a recipient's Crit Rate must not change the result. Vanguard's separate sharp-crit coefficient requires its own supported contract.
- Multiple current attribute buffs can coexist; Wind's contribution must apply once, rather than once per selected attribute. Current Winded vulnerability affects only the specified Direct elements. Extra eligibility requires another Attack/Rupture/Vanguard teammate, and its level-60 self damage bonus is 80%.
- The Winded duration extension is 30 to 50 seconds while the Wind anomaly coefficient remains 12.5. Do not infer additional Wind ticks or ordinary Wind Disorder. C6's source multiplier is exactly 2.5 times the original cyclone, with two separately specified additional cyclones; timing history is not replayed.

## Other remaining work

The shared editor's signature-equipped defaults still differ from `calculator-implementation-spec.md`. A future change must initialize from explicit signature mappings with refinement 5 for A-rank characters and 1 for S-rank characters, preserving manual selections, explicit unequipped states, and imports. This UI work was not implemented at the stop point. W-Engine progress statements about available owner types should be audited alongside completed role registration.

Existing localized source uncertainties remain in `docs/implementation-open-questions.md`; they are separate from the unfinished engineering work recorded here. No merge or pull request was created.
