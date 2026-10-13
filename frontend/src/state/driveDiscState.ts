export type DriveDiscSubstat =
  | { stat: string; roll_count: number; value?: never }
  | { stat: string; value: number; roll_count?: never };
export type DriveDiscConfig = {
  slot: number;
  set_id: string;
  main_stat: string | null;
  main_stat_value?: number;
  level?: number;
  substats: DriveDiscSubstat[];
};

export type DriveDiscStatOption = {
  stat_key: string;
  label: string;
  value_per_roll: number;
};

export type DriveDiscSlotSchema = {
  slot: number;
  main_stat_options: DriveDiscStatOption[];
};

function removeMainStatConflict(
  current: DriveDiscSubstat[],
  mainStat: string | null,
): DriveDiscSubstat[] {
  return mainStat === null
    ? [...current]
    : current.filter((item) => item.stat !== mainStat);
}

export function selectDriveDiscSetValue(
  current: DriveDiscConfig | undefined,
  slot: number,
  setId: string,
  schema: DriveDiscSlotSchema,
): DriveDiscConfig {
  const main = schema.main_stat_options.length === 1
    ? schema.main_stat_options[0].stat_key
    : (schema.main_stat_options.some((item) => item.stat_key === current?.main_stat)
      ? current?.main_stat ?? null
      : null);
  return {
    slot,
    set_id: setId,
    main_stat: main,
    substats: removeMainStatConflict(current?.substats ?? [], main),
  };
}

export function updateDriveDiscMainValue(
  current: DriveDiscConfig,
  mainStat: string | null,
): DriveDiscConfig {
  return {
    ...current,
    main_stat: mainStat,
    main_stat_value: undefined,
    substats: removeMainStatConflict(current.substats, mainStat),
  };
}

export function addDriveDiscSubstat(
  current: DriveDiscConfig,
  stat: string,
  rollCount = 1,
): DriveDiscConfig {
  if (
    current.substats.length >= 4
    || !stat
    || stat === current.main_stat
    || current.substats.some((item) => item.stat === stat)
  ) {
    return current;
  }
  return {
    ...current,
    substats: [...current.substats, { stat, roll_count: rollCount }],
  };
}

export function removeDriveDiscSubstat(
  current: DriveDiscConfig,
  index: number,
): DriveDiscConfig {
  return {
    ...current,
    substats: current.substats.filter((_, itemIndex) => itemIndex !== index),
  };
}

export function replaceDriveDiscSubstat(
  current: DriveDiscConfig,
  index: number,
  next: DriveDiscSubstat,
): DriveDiscConfig {
  return {
    ...current,
    substats: current.substats.map((item, itemIndex) => itemIndex === index ? next : item),
  };
}

export function updateDriveDiscSubstatRollCount(
  current: DriveDiscConfig,
  index: number,
  delta: number,
): DriveDiscConfig {
  const substat = current.substats[index];
  if (!substat || typeof substat.roll_count !== "number" || !Number.isFinite(delta) || !Number.isInteger(delta)) return current;
  const rollCount = Math.min(6, Math.max(1, substat.roll_count + delta));
  if (rollCount === substat.roll_count) return current;
  return replaceDriveDiscSubstat(current, index, { stat: substat.stat, roll_count: rollCount });
}

export function isDriveDiscComplete(current: DriveDiscConfig): boolean {
  if (
    typeof current.main_stat_value === "number"
    && current.substats.length <= 4
    && current.substats.every((item) => "value" in item)
  ) return true;
  const totalRolls = current.substats.reduce(
    (sum, item) => sum + (typeof item.roll_count === "number" ? item.roll_count : 0),
    0,
  );
  return current.main_stat !== null
    && current.substats.length === 4
    && (totalRolls === 8 || totalRolls === 9);
}
