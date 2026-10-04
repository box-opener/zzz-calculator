import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import WEnginePicker from "./WEnginePicker";

const engines = [
  { wengine_id: "wengine:12001", display_name: "强攻S较小编号", rarity: "S", specialty: "attack", signature_character_id: null },
  { wengine_id: "wengine:12002", display_name: "强攻专武A", rarity: "A", specialty: "attack", signature_character_id: "character:demo" },
  { wengine_id: "wengine:12011", display_name: "强攻S较大编号", rarity: "S", specialty: "attack", signature_character_id: null },
  { wengine_id: "wengine:11001", display_name: "强攻B", rarity: "B", specialty: "attack", signature_character_id: null },
  { wengine_id: "wengine:13001", display_name: "支援S音擎", rarity: "S", specialty: "support", signature_character_id: null },
  { wengine_id: "wengine:13002", display_name: "支援A音擎", rarity: "A", specialty: "support", signature_character_id: null },
  { wengine_id: "wengine:14001", display_name: "击破S音擎", rarity: "S", specialty: "stun", signature_character_id: null },
];

const specialtyLabel = (specialty: string) => ({
  attack: "强攻",
  stun: "击破",
  support: "支援",
}[specialty] ?? specialty);

describe("WEnginePicker", () => {
  it("keeps same-specialty choices in the first level and nests other specialties", () => {
    const markup = renderToStaticMarkup(
      <WEnginePicker
        engines={engines}
        characterId="character:demo"
        specialty="attack"
        selectedId="wengine:13001"
        specialtyLabel={specialtyLabel}
        onSelect={() => undefined}
      />,
    );
    const ownChoices = ["强攻专武A", "强攻S较大编号", "强攻S较小编号", "强攻B"]
      .map((name) => markup.indexOf(`${name}</button>`));
    const otherSpecialtyMenu = markup.indexOf("其他职业音擎");
    const secondLevel = markup.indexOf("支援</summary>");
    const thirdLevel = markup.indexOf("支援S音擎</button>");

    expect(markup).toContain('aria-label="音擎选择：支援S音擎"');
    expect(markup).toContain("无音擎</button>");
    expect(ownChoices.every((position) => position > -1)).toBe(true);
    expect(ownChoices).toEqual([...ownChoices].sort((left, right) => left - right));
    expect(ownChoices.at(-1)).toBeLessThan(otherSpecialtyMenu);
    expect(otherSpecialtyMenu).toBeLessThan(secondLevel);
    expect(secondLevel).toBeLessThan(thirdLevel);
    expect(markup).toContain('aria-current="true"');
  });
});
