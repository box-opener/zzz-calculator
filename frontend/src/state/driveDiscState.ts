export type DriveDiscSubstat = { stat: string; roll_count: number };
export type DriveDiscConfig = {
  slot: number;
  set_id: string;
  main_stat: string | null;
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

export function isDriveDiscComplete(current: DriveDiscConfig): boolean {
  const totalRolls = current.substats.reduce(
    (sum, item) => sum + item.roll_count,
    0,
  );
  return current.main_stat !== null
    && current.substats.length === 4
    && (totalRolls === 8 || totalRolls === 9);
}
