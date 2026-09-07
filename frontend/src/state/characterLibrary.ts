export type CharacterLibraryEntry = {
  character_id: string;
  display_name: string;
  specialty: string;
  element: string;
};

export type CharacterLibraryFilter = {
  query?: string;
  specialty?: string;
  element?: string;
};

/** Return catalog entries matching the picker filters without mutating the catalog. */
export function filterCharacterCatalog<T extends CharacterLibraryEntry>(
  characters: readonly T[],
  filter: CharacterLibraryFilter,
): T[] {
  const query = filter.query?.trim().toLocaleLowerCase() ?? "";
  return characters.filter((character) => {
    const matchesQuery = !query
      || [character.display_name, character.character_id, character.specialty, character.element]
        .some((value) => value.toLocaleLowerCase().includes(query));
    return matchesQuery
      && (!filter.specialty || character.specialty === filter.specialty)
      && (!filter.element || character.element === filter.element);
  });
}

/** The picker must never offer an already active team member as a duplicate. */
export function isCharacterSelectable(
  characterId: string,
  teamCharacterIds: readonly string[],
): boolean {
  return !teamCharacterIds.includes(characterId);
}
