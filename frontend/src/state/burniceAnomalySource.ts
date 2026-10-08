export type BurniceAnomalySourceOption = {
  key: string;
  characterId: string;
  element: string;
};

type SourceEditor = {
  character_id: string;
  reviewed_anomaly_source_elements?: readonly string[];
} | null;

export function burniceAnomalySourceOptions(
  teamIds: readonly string[],
  editors: Readonly<Record<string, SourceEditor>>,
): BurniceAnomalySourceOption[] {
  return teamIds.flatMap((characterId) => {
    const elements = editors[characterId]?.reviewed_anomaly_source_elements ?? [];
    return elements
      .filter((element) => element !== "luminance")
      .map((element) => ({
        key: `${characterId}|${element}`,
        characterId,
        element,
      }));
  });
}

export function defaultBurniceAnomalySource(
  options: readonly BurniceAnomalySourceOption[],
  burniceId = "character:1171",
): BurniceAnomalySourceOption | null {
  return options.find((option) => option.characterId === burniceId)
    ?? options[0]
    ?? null;
}

export function selectedBurniceAnomalySource(
  options: readonly BurniceAnomalySourceOption[],
  selectedKey: string | null,
  burniceId = "character:1171",
): BurniceAnomalySourceOption | null {
  return options.find((option) => option.key === selectedKey)
    ?? defaultBurniceAnomalySource(options, burniceId);
}
