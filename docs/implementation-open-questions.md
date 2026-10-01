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
