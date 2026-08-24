import { readFile } from "node:fs/promises";
import path from "node:path";
import { createPanelInput } from "../src/application/create-panel-input.js";
import { calculatePanel } from "../src/domain/engine/calculate-panel.js";
import type { ImportedShowcase } from "../src/domain/model/character-build.js";
import type { FinalPanelStats } from "../src/domain/model/panel.js";
import type { StaticDataRegistry } from "../src/domain/model/static-data.js";

const uid = process.argv[2] ?? "16241824";
const characterId = process.argv[3] ?? "1401";
const normalized = JSON.parse(
  await readFile(path.join(".cache/uid/normalized", `${uid}.json`), "utf8"),
) as ImportedShowcase;
const fixture = JSON.parse(
  await readFile("tests/fixtures/alice-uid-16241824.json", "utf8"),
) as { staticData: StaticDataRegistry };
const build = normalized.builds.find(
  (item) => item.character.id === characterId,
);
if (!build) throw new Error(`标准配置中没有角色 ${characterId}。`);

const propertyMap: Readonly<Record<number, keyof FinalPanelStats>> = {
  1: "hp",
  2: "atk",
  3: "def",
  4: "impact",
  5: "critRate",
  6: "critDmg",
  7: "anomalyMastery",
  8: "anomalyProficiency",
  9: "penRate",
  11: "energyRegen",
  232: "penFlat",
  315: "physicalDmgBonus",
  316: "fireDmgBonus",
  317: "iceDmgBonus",
  318: "electricDmgBonus",
  319: "etherDmgBonus",
};

const calculated = calculatePanel(
  createPanelInput(build, fixture.staticData).input,
).final;
let mismatches = 0;
console.log("属性\t米游社\t计算值\t差异");
for (const property of build.reportedPanel ?? []) {
  const stat = propertyMap[property.propertyId];
  if (!stat) continue;
  const calculatedValue = calculated[stat] ?? 0;
  const difference = calculatedValue - property.final;
  if (Math.abs(difference) > 1e-9) mismatches += 1;
  console.log(`${stat}\t${property.final}\t${calculatedValue}\t${difference}`);
}

if (mismatches > 0) {
  console.error(`发现 ${mismatches} 项米游社面板差异。`);
  process.exitCode = 1;
} else {
  console.log("米游社面板全部匹配。 ✅");
}
