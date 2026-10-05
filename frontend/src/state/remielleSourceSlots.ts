export type RemielleSourceCharacter = {
  character_id: string;
  display_name: string;
  element: string;
};

export type RemielleSourceEditor = {
  luminance_source_elements?: string[];
};

export type RemielleOrdinarySourceOption = {
  key: string;
  characterId: string;
  characterName: string;
  element: string;
  defaultForCharacter: boolean;
};

export function remielleOrdinarySourceOptions(
  teamIds: string[],
  characters: RemielleSourceCharacter[],
  editorViews: Record<string, RemielleSourceEditor | null | undefined>,
  remielleId = "character:1581",
): RemielleOrdinarySourceOption[] {
  return teamIds.flatMap((characterId) => {
    if (characterId === remielleId) return [];
    const character = characters.find((item) => item.character_id === characterId);
    const elements = editorViews[characterId]?.luminance_source_elements?.length
      ? editorViews[characterId]?.luminance_source_elements ?? []
      : character?.element ? [character.element] : [];
    const validElements = elements.filter((element) => element !== "luminance");
    const preferred = validElements.includes(character?.element ?? "")
      ? character?.element
      : validElements[0];
    return validElements.map((element) => ({
      key: `ordinary:${characterId}|${element}`,
      characterId,
      characterName: character?.display_name ?? characterId,
      element,
      defaultForCharacter: element === preferred,
    }));
  });
}

export function defaultRemielleSourceSlots(
  teamIds: string[],
  options: RemielleOrdinarySourceOption[],
): string[] {
  const activeDefaults = teamIds.flatMap((characterId) => (
    options
      .filter((item) => item.characterId === characterId && item.defaultForCharacter)
      .map((item) => item.key)
  ));
  return [
    ...activeDefaults,
    ...Array.from({ length: Math.max(0, 3 - activeDefaults.length) }, () => ""),
  ].slice(0, 3);
}

export function serializeRemielleSourceSlots(
  selections: string[],
  options: RemielleOrdinarySourceOption[],
  remielleId = "character:1581",
) {
  return selections.flatMap((value, index) => {
    if (!value) return [];
    const slotId = `slot-${index + 1}`;
    if (value.startsWith("ordinary:")) {
      const selected = options.find((item) => item.key === value);
      return selected
        ? [{
            slot_id: slotId,
            kind: "ordinary-anomaly",
            source_character_id: selected.characterId,
            element: selected.element,
          }]
        : [];
    }
    return [{ slot_id: slotId, kind: value, source_character_id: remielleId }];
  });
}
