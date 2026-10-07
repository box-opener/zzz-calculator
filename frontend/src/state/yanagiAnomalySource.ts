export type YanagiAnomalySourceOption = {
  key: string;
  characterId: string;
  element: string;
};

type SourceEditor = {
  character_id: string;
  anomaly_source_elements?: readonly string[];
} | null;

export function yanagiAnomalySourceOptions(
  teamIds: readonly string[],
  editors: Readonly<Record<string, SourceEditor>>,
): YanagiAnomalySourceOption[] {
  return teamIds.flatMap((characterId) => {
    const elements = editors[characterId]?.anomaly_source_elements ?? [];
    return elements
      .filter((element) => element !== "luminance")
      .map((element) => ({
        key: `${characterId}|${element}`,
        characterId,
        element,
      }));
  });
}

export function defaultYanagiAnomalySource(
  options: readonly YanagiAnomalySourceOption[],
  yanagiId = "character:1221",
): YanagiAnomalySourceOption | null {
  return options.find((option) => option.characterId === yanagiId) ?? null;
}

export function selectedYanagiAnomalySource(
  options: readonly YanagiAnomalySourceOption[],
  selectedKey: string | null,
  yanagiId = "character:1221",
): YanagiAnomalySourceOption | null {
  return options.find((option) => option.key === selectedKey)
    ?? defaultYanagiAnomalySource(options, yanagiId);
}
