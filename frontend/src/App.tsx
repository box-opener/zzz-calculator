import { useEffect, useState } from "react";

type Character = {
  character_id: string;
  display_name: string;
  rarity: string;
  element: string;
  specialty: string;
  image_path: string;
  image_object_position: string;
};

type Diagnostic = {
  diagnostic_id: string;
  kind: string;
  message: string;
  blocking: boolean;
};

function App() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/characters")
      .then(async (response) => {
        if (!response.ok) throw new Error(`catalog request failed: ${response.status}`);
        return (await response.json()) as Character[];
      })
      .then((items) => {
        setCharacters(items);
        setSelectedId(items[0]?.character_id ?? null);
      })
      .catch((error: Error) => {
        setDiagnostics([
          {
            diagnostic_id: "frontend:catalog",
            kind: "missing-data",
            message: error.message,
            blocking: true,
          },
        ]);
      })
      .finally(() => setLoading(false));
  }, []);

  const selected = characters.find((item) => item.character_id === selectedId);

  return (
    <main className="app-shell">
      <header className="app-header glass-card">
        <div>
          <p className="eyebrow">SPEC-V1 · PRESENTATION-V1</p>
          <h1>ZZZ Calculator</h1>
          <p className="muted">确定性战斗规则解释器</p>
        </div>
        <div className="header-status">
          <span className="status-dot" />
          <span>新计算内核</span>
        </div>
      </header>

      <section className="dashboard-grid">
        <section className="glass-card roster-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">ROSTER</p>
              <h2>角色</h2>
            </div>
            <span className="counter">{characters.length}/3</span>
          </div>
          {loading && <p className="muted">正在读取生产角色数据…</p>}
          <div className="character-grid">
            {characters.map((character) => (
              <button
                className={`character-card ${selectedId === character.character_id ? "selected" : ""}`}
                key={character.character_id}
                onClick={() => setSelectedId(character.character_id)}
                type="button"
              >
                <img
                  alt={character.display_name}
                  src={character.image_path}
                  style={{ objectPosition: character.image_object_position }}
                />
                <span className="character-card-copy">
                  <strong>{character.display_name}</strong>
                  <small>{character.specialty} · {character.element}</small>
                </span>
                <span className="rarity">{character.rarity}</span>
              </button>
            ))}
          </div>
          {selected && (
            <div className="selection-summary">
              <span className="eyebrow">CURRENT OPERATOR</span>
              <strong>{selected.display_name}</strong>
              <span className="muted">{selected.character_id}</span>
            </div>
          )}
        </section>

        <section className="glass-card contract-panel">
          <p className="eyebrow">PRESENTATION CONTRACT</p>
          <h2>新前端壳</h2>
          <p className="muted">
            当前页面只消费版本化展示数据。伤害公式、规则匹配、暴击模式和派生事件均由 Python 内核负责。
          </p>
          <div className="contract-list">
            <div><span>生产数据</span><strong>core/data/characters</strong></div>
            <div><span>状态来源</span><strong>CalculationScenario</strong></div>
            <div><span>结果来源</span><strong>Presentation DTO</strong></div>
            <div><span>旧逻辑</span><strong className="blocked-text">未加载</strong></div>
          </div>
          <div className="feature-pills">
            <span>三模式结果</span>
            <span>事件 Trace</span>
            <span>诊断</span>
          </div>
        </section>
      </section>

      {diagnostics.length > 0 && (
        <section className="diagnostics glass-card">
          <p className="eyebrow">DIAGNOSTICS</p>
          {diagnostics.map((diagnostic) => (
            <div className="diagnostic" key={diagnostic.diagnostic_id}>
              <strong>{diagnostic.kind}</strong>
              <span>{diagnostic.message}</span>
            </div>
          ))}
        </section>
      )}
    </main>
  );
}

export default App;
