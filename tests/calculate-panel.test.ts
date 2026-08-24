import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import type { CharacterBuild } from "../src/domain/model/character-build.js";
import type {
  FinalPanelStats,
  PanelCalculationInput,
} from "../src/domain/model/panel.js";
import { calculatePanel } from "../src/domain/engine/calculate-panel.js";
import type { StaticDataRegistry } from "../src/domain/model/static-data.js";
import { createPanelInput } from "../src/application/create-panel-input.js";

interface AliceFixture {
  build: CharacterBuild;
  staticData: StaticDataRegistry;
  panelInput: PanelCalculationInput;
  expected: FinalPanelStats;
}

async function loadFixture(): Promise<AliceFixture> {
  const fixturePath = path.join(
    process.cwd(),
    "tests/fixtures/alice-uid-16241824.json",
  );
  return JSON.parse(await readFile(fixturePath, "utf8")) as AliceFixture;
}

test("爱丽丝 UID 16241824 参考面板可以被基础引擎精确复现", async () => {
  const fixture = await loadFixture();
  const result = calculatePanel(fixture.panelInput);
  assert.deepEqual(result.final, fixture.expected);
  assert.deepEqual(result.warnings, []);
});

test("参考面板保留了六个驱动盘和计算追踪", async () => {
  const fixture = await loadFixture();
  const result = calculatePanel(fixture.panelInput);
  assert.equal(fixture.build.driveDiscs.length, 6);
  assert.ok(result.trace.some((entry) => entry.sourceId === "weapon:14140:secondary"));
  assert.ok(result.trace.some((entry) => entry.sourceId === "set:32600:2pc"));
  assert.ok(result.trace.some((entry) => entry.stat === "anomalyMastery"));
});

test("标准 CharacterBuild 可以自动解析成相同的面板输入", async () => {
  const fixture = await loadFixture();
  const resolved = createPanelInput(fixture.build, fixture.staticData);
  const result = calculatePanel(resolved.input);
  assert.deepEqual(result.final, fixture.expected);
  assert.equal(
    resolved.input.modifiers.length,
    fixture.panelInput.modifiers.length,
  );
});
