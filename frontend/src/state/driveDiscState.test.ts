import { describe, expect, it } from "vitest";
import {
  addDriveDiscSubstat,
  isDriveDiscComplete,
  removeDriveDiscSubstat,
  replaceDriveDiscSubstat,
  selectDriveDiscSetValue,
  updateDriveDiscMainValue,
  type DriveDiscSlotSchema,
} from "./driveDiscState";
const schema: DriveDiscSlotSchema = {
  slot: 4,
  main_stat_options: [
    { stat_key: "attack-percent", label: "攻击力%", value_per_roll: .30 },
    { stat_key: "crit-rate", label: "暴击率", value_per_roll: .24 },
  ],
};

describe("Drive Disc editor state", () => {
  it("does not fabricate main or substats for a newly selected flexible slot", () => {
    const disc = selectDriveDiscSetValue(undefined, 4, "drive-disc:31000", schema);
    expect(disc.main_stat).toBeNull();
    expect(disc.substats).toEqual([]);
  });

  it("sets a unique main stat for fixed slots", () => {
    const fixedSchema: DriveDiscSlotSchema = {
      slot: 1,
      main_stat_options: [{ stat_key: "hp-flat", label: "生命值", value_per_roll: 2200 }],
    };
    const disc = selectDriveDiscSetValue(undefined, 1, "drive-disc:31000", fixedSchema);
    expect(disc.main_stat).toBe("hp-flat");
    expect(disc.substats).toEqual([]);
  });

  it("reconciles a changed main stat by removing only the exact conflict", () => {
    const original = selectDriveDiscSetValue(undefined, 4, "drive-disc:31000", schema);
    const withSubstats = {
      ...original,
      main_stat: "attack-percent",
      substats: [
        { stat: "crit-rate", roll_count: 2 },
        { stat: "crit-damage", roll_count: 3 },
      ],
    };
    const changed = updateDriveDiscMainValue(withSubstats, "crit-rate");
    expect(changed.substats.some((item) => item.stat === "crit-rate")).toBe(false);
    expect(changed.substats).toEqual([{ stat: "crit-damage", roll_count: 3 }]);
  });

  it("changes exactly one substat row", () => {
    const original = addDriveDiscSubstat(
      selectDriveDiscSetValue(undefined, 4, "drive-disc:31000", schema),
      "attack-percent",
    );
    const changed = replaceDriveDiscSubstat(original, 0, { stat: "crit-rate", roll_count: 3 });
    expect(changed.substats[0]).toEqual({ stat: "crit-rate", roll_count: 3 });
    expect(changed.substats.slice(1)).toEqual(original.substats.slice(1));
  });

  it("allows the user to add and remove individual substat rows", () => {
    const original = selectDriveDiscSetValue(undefined, 4, "drive-disc:31000", schema);
    const added = addDriveDiscSubstat(original, "crit-rate");
    expect(added.substats).toEqual([{ stat: "crit-rate", roll_count: 1 }]);
    expect(removeDriveDiscSubstat(added, 0).substats).toEqual([]);
  });

  it("does not present a partial disc as complete from roll count alone", () => {
    const partial = {
      ...selectDriveDiscSetValue(undefined, 4, "drive-disc:31000", schema),
      substats: [
        { stat: "crit-rate", roll_count: 2 },
        { stat: "crit-damage", roll_count: 2 },
        { stat: "attack-flat", roll_count: 2 },
        { stat: "penetration-flat", roll_count: 2 },
      ],
    };
    expect(isDriveDiscComplete(partial)).toBe(false);
    expect(isDriveDiscComplete({ ...partial, main_stat: "attack-percent" })).toBe(true);
  });
});
