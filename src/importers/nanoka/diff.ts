import type {
  NanokaManifest,
  NanokaManifestName,
  NanokaSnapshot,
} from "./client.js";

export interface ManifestDiff {
  beforeCount: number;
  afterCount: number;
  added: string[];
  removed: string[];
  changed: string[];
}

export interface NanokaDiffReport {
  source: "nanoka.cc";
  fromVersion: string;
  toVersion: string;
  generatedAt: string;
  manifests: Record<NanokaManifestName, ManifestDiff>;
}

export function diffNanokaSnapshots(
  before: NanokaSnapshot,
  after: NanokaSnapshot,
): NanokaDiffReport {
  return {
    source: "nanoka.cc",
    fromVersion: before.version,
    toVersion: after.version,
    generatedAt: new Date().toISOString(),
    manifests: {
      character: diffManifest(
        before.manifests.character,
        after.manifests.character,
      ),
      weapon: diffManifest(before.manifests.weapon, after.manifests.weapon),
      equipment: diffManifest(
        before.manifests.equipment,
        after.manifests.equipment,
      ),
      monster: diffManifest(before.manifests.monster, after.manifests.monster),
      boss: diffManifest(before.manifests.boss, after.manifests.boss),
    },
  };
}

export function diffManifest(
  before: NanokaManifest,
  after: NanokaManifest,
): ManifestDiff {
  const beforeIds = new Set(Object.keys(before));
  const afterIds = new Set(Object.keys(after));
  return {
    beforeCount: beforeIds.size,
    afterCount: afterIds.size,
    added: [...afterIds].filter((id) => !beforeIds.has(id)).sort(compareIds),
    removed: [...beforeIds].filter((id) => !afterIds.has(id)).sort(compareIds),
    changed: [...afterIds]
      .filter(
        (id) =>
          beforeIds.has(id) &&
          stableStringify(before[id]) !== stableStringify(after[id]),
      )
      .sort(compareIds),
  };
}

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(",")}]`;
  }
  if (value && typeof value === "object") {
    return `{${Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => `${JSON.stringify(key)}:${stableStringify(item)}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function compareIds(left: string, right: string): number {
  return Number(left) - Number(right) || left.localeCompare(right);
}
