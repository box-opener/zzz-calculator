import { useEffect, useRef } from "react";

type WEngineOption = {
  wengine_id: string;
  display_name: string;
  rarity: string;
  specialty: string;
  signature_character_id?: string | null;
};

type WEnginePickerProps = {
  engines: readonly WEngineOption[];
  characterId: string;
  specialty: string | undefined;
  selectedId: string | undefined;
  specialtyLabel: (specialty: string) => string;
  onSelect: (wengineId: string | null) => void;
};

export default function WEnginePicker({
  engines,
  characterId,
  specialty,
  selectedId,
  specialtyLabel,
  onSelect,
}: WEnginePickerProps) {
  const pickerRef = useRef<HTMLDetailsElement>(null);
  const summaryRef = useRef<HTMLElement>(null);
  const selected = engines.find((engine) => engine.wengine_id === selectedId);
  const compareEngines = (left: WEngineOption, right: WEngineOption) => {
    const leftSignature = left.signature_character_id === characterId;
    const rightSignature = right.signature_character_id === characterId;
    if (leftSignature !== rightSignature) return leftSignature ? -1 : 1;
    const rarityRank: Record<string, number> = { S: 3, A: 2, B: 1 };
    const rarityDifference = (rarityRank[right.rarity] ?? 0) - (rarityRank[left.rarity] ?? 0);
    if (rarityDifference !== 0) return rarityDifference;
    const leftId = Number(left.wengine_id.match(/(\d+)$/)?.[1] ?? 0);
    const rightId = Number(right.wengine_id.match(/(\d+)$/)?.[1] ?? 0);
    return rightId - leftId;
  };
  const ownEngines = engines
    .filter((engine) => engine.specialty === specialty)
    .sort(compareEngines);
  const otherSpecialties = [...new Set(
    engines
      .filter((engine) => engine.specialty !== specialty)
      .map((engine) => engine.specialty),
  )].sort((left, right) => specialtyLabel(left).localeCompare(specialtyLabel(right), "zh-CN"));

  const choose = (wengineId: string | null, button: HTMLButtonElement) => {
    onSelect(wengineId);
    const picker = button.closest<HTMLDetailsElement>("details.wengine-picker");
    if (picker) {
      picker.querySelectorAll<HTMLDetailsElement>("details[open]").forEach((details) => {
        details.open = false;
      });
      picker.open = false;
      summaryRef.current?.focus();
    }
  };

  useEffect(() => {
    const close = () => {
      const picker = pickerRef.current;
      if (!picker) return;
      picker.querySelectorAll<HTMLDetailsElement>("details[open]").forEach((details) => {
        details.open = false;
      });
      picker.open = false;
    };
    const handlePointerDown = (event: PointerEvent) => {
      const picker = pickerRef.current;
      if (picker?.open && event.target instanceof Node && !picker.contains(event.target)) {
        close();
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && pickerRef.current?.open) {
        event.preventDefault();
        close();
        summaryRef.current?.focus();
      }
    };
    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  return (
    <details className="wengine-picker" ref={pickerRef}>
      <summary
        aria-label={`音擎选择：${selected?.display_name ?? "无音擎"}`}
        className="wengine-picker-summary"
        ref={summaryRef}
      >
        <span>{selected ? selected.display_name : "无音擎"}</span>
        <span aria-hidden="true" className="wengine-picker-chevron">▾</span>
      </summary>
      <div className="wengine-picker-menu">
        <button
          aria-current={selectedId ? undefined : "true"}
          className="wengine-picker-option"
          onClick={(event) => choose(null, event.currentTarget)}
          type="button"
        >
          无音擎
        </button>
        {ownEngines.map((engine) => (
          <button
            aria-current={selectedId === engine.wengine_id ? "true" : undefined}
            className="wengine-picker-option"
            key={engine.wengine_id}
            onClick={(event) => choose(engine.wengine_id, event.currentTarget)}
            type="button"
          >
            {engine.display_name}
          </button>
        ))}
        {otherSpecialties.length > 0 && (
          <details className="wengine-picker-other">
            <summary>其他职业音擎</summary>
            {otherSpecialties.map((otherSpecialty) => (
              <details className="wengine-picker-specialty" key={otherSpecialty}>
                <summary>{specialtyLabel(otherSpecialty)}</summary>
                {engines
                  .filter((engine) => engine.specialty === otherSpecialty)
                  .sort(compareEngines)
                  .map((engine) => (
                    <button
                      aria-current={selectedId === engine.wengine_id ? "true" : undefined}
                      className="wengine-picker-option"
                      key={engine.wengine_id}
                      onClick={(event) => choose(engine.wengine_id, event.currentTarget)}
                      type="button"
                    >
                      {engine.display_name}
                    </button>
                  ))}
              </details>
            ))}
          </details>
        )}
      </div>
    </details>
  );
}
