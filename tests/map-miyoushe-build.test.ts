import assert from "node:assert/strict";
import test from "node:test";
import { mapMiyousheResponse } from "../src/importers/miyoushe/map-miyoushe-build.js";

test("米游社爱丽丝字段映射为标准 CharacterBuild", () => {
  const result = mapMiyousheResponse("16241824", {
    retcode: 0,
    data: {
      list: [
        {
          avatar: {
            id: 1401,
            level: 60,
            promotes: 6,
            rank: 2,
            skills: [
              { skill_type: 0, level: 12 },
              { skill_type: 5, level: 7 },
            ],
            properties: [
              { property_id: 2, final_val: "3103", base: "1593", add: "1510" },
            ],
          },
          weapon: { id: 14140, level: 60, star: 1 },
          equip: [
            {
              id: 32641,
              level: 15,
              rarity: "S",
              equipment_type: 1,
              equip_suit: { suit_id: 32600 },
              main_properties: [{ property_id: 11103, base: "2200" }],
              properties: [
                { property_id: 31203, base: "45", add: 4 },
                { property_id: 13102, base: "9.6%", add: 1 },
              ],
            },
          ],
        },
      ],
    },
  });

  const build = result.builds[0];
  if (!build) throw new Error("未生成角色配置");
  const disc = build.driveDiscs[0];
  if (!disc) throw new Error("未生成驱动盘配置");
  assert.equal(build.source.type, "miyoushe");
  assert.deepEqual(build.character, {
    id: "1401",
    level: 60,
    promotion: 6,
    cinema: 2,
    coreLevel: 7,
    skillLevels: { basic: 12, core: 7 },
  });
  assert.equal(build.weapon?.id, "14140");
  assert.equal(disc.setId, "32600");
  assert.equal(disc.mainStats[0]?.value, 2200);
  assert.equal(disc.subStats[1]?.key, "defPct");
  assert.equal(disc.subStats[1]?.value, 9.6);
  assert.equal(build.reportedPanel?.[0]?.final, 3103);
});
