import assert from "node:assert/strict";
import test from "node:test";
import { mapEnkaShowcase } from "../src/importers/enka/map-enka-build.js";
import type { EnkaResponse } from "../src/importers/enka/types.js";

test("Enka 文档结构可以转换为标准 CharacterBuild", () => {
  const response: EnkaResponse = {
    uid: "16241824",
    ttl: 300,
    PlayerInfo: {
      SocialDetail: { ProfileDetail: { Nickname: "nina27" } },
      ShowcaseDetail: {
        AvatarList: [
          {
            Id: 1401,
            Level: 60,
            PromotionLevel: 6,
            TalentLevel: 2,
            CoreSkillEnhancement: 7,
            SkillLevelList: [
              { Index: 0, Level: 12 },
              { Index: 1, Level: 12 },
            ],
            Weapon: {
              Uid: 123,
              Id: 14140,
              Level: 60,
              BreakLevel: 5,
              UpgradeLevel: 1,
            },
            EquippedList: Array.from({ length: 6 }, (_, index) => ({
              Slot: index + 1,
              Equipment: {
                Uid: index + 100,
                Id: 32600 + index,
                Level: 15,
                MainStatList: [
                  { PropertyId: index === 0 ? 11101 : 12101, PropertyValue: 100 },
                ],
                RandomPropertyList: [
                  { PropertyId: 31203, PropertyValue: 9, PropertyLevel: 1 },
                ],
              },
            })),
          },
        ],
      },
    },
  };

  const result = mapEnkaShowcase(response);
  assert.equal(result.uid, "16241824");
  assert.equal(result.nickname, "nina27");
  assert.equal(result.builds.length, 1);

  const build = result.builds[0];
  if (!build) throw new Error("预期存在一个导入角色");
  assert.equal(build.character.id, "1401");
  assert.equal(build.character.cinema, 2);
  assert.equal(build.character.skillLevels.basic, 12);
  assert.equal(build.weapon?.id, "14140");
  assert.equal(build.driveDiscs.length, 6);
  assert.equal(build.driveDiscs[0]?.subStats[0]?.key, "anomalyProficiency");
});
