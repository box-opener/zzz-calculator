"""Explicit base-element scope expansion for reviewed compilers."""

from core.types import AnyFilter, EffectFilter, Element, ElementFilter


_ELEMENT_SCOPE: dict[Element, tuple[Element, ...]] = {
    Element.PHYSICAL: (Element.PHYSICAL, Element.LINREN),
    Element.ICE: (Element.ICE, Element.LIESHUANG),
    Element.ETHER: (Element.ETHER, Element.XUANMO),
}


def element_scope_filter(element: Element) -> EffectFilter:
    """Return an explicit filter for a base element and its variants.

    The matcher intentionally keeps ``ElementFilter`` exact.  Compilers must
    expand a base-element rule before it reaches the matcher.
    """

    elements = _ELEMENT_SCOPE.get(element, (element,))
    if len(elements) == 1:
        return ElementFilter(elements[0])
    return AnyFilter(tuple(ElementFilter(item) for item in elements))
