"""Reviewed static full-gauge anomaly source profiles for UI scenarios."""

from core.types import Element


FULL_GAUGE_ANOMALY_PROFILE: dict[Element, tuple[float, int]] = {
    Element.PHYSICAL: (7.13, 1),
    Element.LINREN: (7.13, 1),
    Element.ICE: (5.0, 1),
    Element.LIESHUANG: (5.0, 1),
    Element.ETHER: (0.625, 20),
    Element.XUANMO: (0.625, 20),
    Element.FIRE: (0.5, 20),
    Element.ELECTRIC: (1.25, 10),
    Element.WIND: (17.5, 1),
}


def anomaly_source_tick_multiplier(element: Element) -> float:
    """Return one anomaly-damage tick multiplier for the selected element."""

    try:
        return FULL_GAUGE_ANOMALY_PROFILE[element][0]
    except KeyError as exc:
        raise ValueError(f"unsupported ordinary anomaly source element: {element}") from exc


__all__ = ["FULL_GAUGE_ANOMALY_PROFILE", "anomaly_source_tick_multiplier"]
