import { describe, expect, it } from "vitest";
import {
  replaceDriveDiscSubstat,
  selectDriveDiscSetValue,
  updateDriveDiscMainValue,
  type DriveDiscSlotSchema,
  type DriveDiscStatOption,
} from "./driveDiscState";

const options: DriveDiscStatOption[] = [
  { stat_key: "attack-percent", label: "攻击力%", value_per_roll: .03 },
  { stat_key: "crit-rate", label: "暴击率", value_per_roll: .024 },
  { stat_key: "crit-damage", label: "暴击伤害", value_per_roll: .048 },
  { stat_key: "attack-flat", label: "攻击力", value_per_roll: 19 },
  { stat_key: "penetration-flat", label: "穿透值", value_per_roll: 9 },
];
const schema: DriveDiscSlotSchema = {
  slot: 4,
  main_stat_options: [
    { stat_key: "attack-percent", label: "攻击力%", value_per_roll: .30 },
    { stat_key: "crit-rate", label: "暴击率", value_per_roll: .24 },
  ],
};

describe("Drive Disc editor state", () => {
  it("creates four unique two-roll substats without repeating the main stat", () => {
    const disc = selectDriveDiscSetValue(undefined, 4, "drive-disc:31000", schema, options);
    expect(disc.main_stat).toBe("attack-percent");
    expect(disc.substats).toHaveLength(4);
    expect(new Set(disc.substats.map((item) => item.stat)).size).toBe(4);
    expect(disc.substats.some((item) => item.stat === disc.main_stat)).toBe(false);
    expect(disc.substats.reduce((sum, item) => sum + item.roll_count, 0)).toBe(8);
  });

  it("reconciles a changed main stat and preserves legal substat rolls", () => {
    const original = selectDriveDiscSetValue(undefined, 4, "drive-disc:31000", schema, options);
    const changed = updateDriveDiscMainValue(original, "crit-rate", options);
    expect(changed.substats.some((item) => item.stat === "crit-rate")).toBe(false);
    expect(changed.substats).toHaveLength(4);
  });

  it("changes exactly one substat row", () => {
    const original = selectDriveDiscSetValue(undefined, 4, "drive-disc:31000", schema, options);
    const changed = replaceDriveDiscSubstat(original, 0, { stat: "crit-rate", roll_count: 3 });
    expect(changed.substats[0]).toEqual({ stat: "crit-rate", roll_count: 3 });
    expect(changed.substats.slice(1)).toEqual(original.substats.slice(1));
  });
});
