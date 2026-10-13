"""Compare one extra roll through the same formal calculation pipeline."""
from collections.abc import Mapping
from typing import Any

from core.types import DRIVE_DISC_SUBSTAT_VALUES, DriveDiscStatKey
from core.presentation.calculation_service import calculate_payload
from core.presentation.drive_disc_display import drive_disc_stat_label, display_drive_disc_value
from core.presentation.registry import registration_for


def calculate_with_substat_gains(payload: Mapping[str, Any]) -> dict[str, Any]:
    requested = payload.get("substat_analysis")
    if requested is None:
        return calculate_payload(payload)
    team = payload.get("team_character_ids", [])
    if not isinstance(requested, list) or not 1 <= len(requested) <= 3:
        raise ValueError("词条收益角色必须为 1–3 名队伍成员")
    if any(not isinstance(cid, str) or cid not in team for cid in requested) or len(set(requested)) != len(requested):
        raise ValueError("词条收益角色必须属于当前队伍且不能重复")
    baseline = calculate_payload(payload)
    analyses = []
    for cid in requested:
        rows = []
        for stat, increment in DRIVE_DISC_SUBSTAT_VALUES.items():
            if stat is DriveDiscStatKey.PENETRATION_FLAT and registration_for(cid).catalog.specialty == "rupture":
                continue
            row = {"stat": stat.value, "label": drive_disc_stat_label(stat),
                   "increment": increment, "increment_label": display_drive_disc_value(stat, increment), "modes": {}}
            try:
                changed = calculate_payload(payload, substat_increment=(cid, stat))
                for mode, before in baseline["totals"].items():
                    after = changed["totals"].get(mode)
                    complete = bool(before["complete"] and after and after["complete"]
                                    and before["value"] is not None and after["value"] is not None)
                    delta = after["value"] - before["value"] if complete else None
                    row["modes"][mode] = {"complete": complete, "before": before["value"],
                        "after": after["value"] if after else None, "delta": delta,
                        "gain_ratio": delta / before["value"] if complete and before["value"] > 0 else None}
            except (ValueError, KeyError, TypeError) as error:
                row["issue"] = str(error)
            rows.append(row)
        analyses.append({"character_id": cid, "rows": rows})
    return {**baseline, "substat_gains": analyses}
