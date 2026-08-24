import { readFile } from "node:fs/promises";
import path from "node:path";
import { calculatePanel } from "../src/domain/engine/calculate-panel.js";
import { createPanelInput } from "../src/application/create-panel-input.js";
import type { CharacterBuild } from "../src/domain/model/character-build.js";
import type {
  FinalPanelStats,
  PanelCalculationInput,
} from "../src/domain/model/panel.js";
import type { StaticDataRegistry } from "../src/domain/model/static-data.js";

interface ReferenceFixture {
  reference: {
    uid: string;
    characterName: string;
  };
  build: CharacterBuild;
  staticData: StaticDataRegistry;
  panelInput: PanelCalculationInput;
  expected: FinalPanelStats;
}

const fixturePath = path.join(
  process.cwd(),
  "tests/fixtures/alice-uid-16241824.json",
);
const fixture = JSON.parse(
  await readFile(fixturePath, "utf8"),
) as ReferenceFixture;
const resolved = createPanelInput(fixture.build, fixture.staticData);
const result = calculatePanel(resolved.input);

console.log(
  `参考面板：${fixture.reference.characterName} / UID ${fixture.reference.uid}`,
);
console.log("属性\t参考值\t计算值\t差异");

let mismatchCount = 0;
for (const [stat, expected] of Object.entries(fixture.expected) as Array<
  [keyof FinalPanelStats, number]
>) {
  const actual = result.final[stat] ?? 0;
  const difference = actual - expected;
  if (Math.abs(difference) > 1e-9) mismatchCount += 1;
  console.log(`${stat}\t${expected}\t${actual}\t${difference}`);
}

if (mismatchCount > 0) {
  console.error(`发现 ${mismatchCount} 项面板差异。`);
  process.exitCode = 1;
} else {
  console.log("全部面板属性匹配。 ✅");
}
