export type CharacterLibraryEntry = {
  character_id: string;
  display_name: string;
  specialty: string;
  element: string;
  faction?: string;
};

export type CharacterLibraryFilter = {
  query?: string;
  specialty?: string;
  element?: string;
  faction?: string;
};

/** Numeric IDs, rather than names or lexicographic string order. */
export function sortCharactersById<T extends { character_id: string }>(characters: readonly T[]): T[] {
  const numericId = (id: string) => Number(id.split(":").at(-1)) || 0;
  return [...characters].sort((a, b) => numericId(b.character_id) - numericId(a.character_id));
}

/** Return catalog entries matching the picker filters without mutating the catalog. */
export function filterCharacterCatalog<T extends CharacterLibraryEntry>(
  characters: readonly T[],
  filter: CharacterLibraryFilter,
): T[] {
  const query = filter.query?.trim().toLocaleLowerCase() ?? "";
  return sortCharactersById(characters.filter((character) => {
    const matchesQuery = !query
      || [character.display_name, character.character_id, character.specialty, character.element, character.faction ?? ""]
        .some((value) => value.toLocaleLowerCase().includes(query));
    return matchesQuery
      && (!filter.specialty || character.specialty === filter.specialty)
      && (!filter.element || character.element === filter.element)
      && (!filter.faction || character.faction === filter.faction);
  }));
}

/** The picker must never offer an already active team member as a duplicate. */
export function isCharacterSelectable(
  characterId: string,
  teamCharacterIds: readonly string[],
): boolean {
  return !teamCharacterIds.includes(characterId);
}
