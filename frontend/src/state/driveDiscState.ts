export type DriveDiscSubstat = { stat: string; roll_count: number };
export type DriveDiscConfig = {
  slot: number;
  set_id: string;
  main_stat: string;
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

function fillSubstats(
  current: DriveDiscSubstat[],
  mainStat: string,
  substatOptions: DriveDiscStatOption[],
): DriveDiscSubstat[] {
  const retained = current.filter(
    (item, index, values) => item.stat !== mainStat
      && values.findIndex((value) => value.stat === item.stat) === index,
  );
  for (const option of substatOptions) {
    if (retained.length >= 4) break;
    if (option.stat_key !== mainStat && !retained.some((item) => item.stat === option.stat_key)) {
      retained.push({ stat: option.stat_key, roll_count: 2 });
    }
  }
  return retained.slice(0, 4);
}

export function selectDriveDiscSetValue(
  current: DriveDiscConfig | undefined,
  slot: number,
  setId: string,
  schema: DriveDiscSlotSchema,
  substatOptions: DriveDiscStatOption[],
): DriveDiscConfig {
  const main = schema.main_stat_options.some((item) => item.stat_key === current?.main_stat)
    ? current!.main_stat
    : (schema.main_stat_options[0]?.stat_key ?? "");
  return {
    slot,
    set_id: setId,
    main_stat: main,
    substats: fillSubstats(current?.substats ?? [], main, substatOptions),
  };
}

export function updateDriveDiscMainValue(
  current: DriveDiscConfig,
  mainStat: string,
  substatOptions: DriveDiscStatOption[],
): DriveDiscConfig {
  return {
    ...current,
    main_stat: mainStat,
    substats: fillSubstats(current.substats, mainStat, substatOptions),
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
