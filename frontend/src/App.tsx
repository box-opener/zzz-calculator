import { useEffect, useMemo, useState } from "react";

type Character = {
  character_id: string;
  display_name: string;
  rarity: string;
  element: string;
  specialty: string;
  image_path: string;
  image_object_position: string;
};

type Condition = {
  condition_id: string;
  label: string;
  resolution: string;
  value: boolean | null;
  editable: boolean;
};

type Rule = {
  rule_id: string;
  label: string;
  source_label: string;
  availability: string;
  enabled_by_default: boolean;
  toggleable: boolean;
  condition_ids: string[];
  stack: { default: number | null; minimum: number | null; maximum: number | null };
};

type Move = {
  entry_id: string;
  label: string;
  skill_group: string | null;
  damage_tags: string[];
  variants: { label: string; multiplier: number | null; repeat_count: number | null }[];
};

type EditorView = {
  character_id: string;
  display_name: string;
  moves: Move[];
  rule_items: Rule[];
  scenario_conditions: Condition[];
  scenario_trigger_inputs: {
    input_id: string;
    label: string;
    actor_options: string[];
    selected_actor: string | null;
  }[];
};

type CalculationView = {
  move_entry_id: string;
  events: {
    semantic_id: string;
    label: string;
    repeat_count: number;
    modes: Record<string, { value: number | null; known_value: number | null; status: string; diagnostics: { message: string }[]; calculation_breakdown: { node: string; value: number | null; read_rule: string }[] }>;
    common_application_trace: { created_by_effect_id: string | null } | null;
  }[];
  totals: Record<string, { value: number | null; complete: boolean; diagnostics: { message: string }[] }>;
  diagnostics: { message: string; blocking: boolean }[];
  resolved_character_snapshots: { character_id: string; stats: Record<string, number | null> }[];
  panel_traces: { recipient_character_id: string; effect_id: string; resolved_value: number; modifier_path: string }[];
};

const YE_ID = "character:1431";
const ASTRA_ID = "character:1311";
const DEFAULT_STATS = { attack: 1000, crit_rate: 0.5, crit_damage: 0.5 };

async function jsonRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.diagnostics?.[0]?.message ?? `request failed: ${response.status}`);
  return payload as T;
}

function App() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [primaryId, setPrimaryId] = useState(YE_ID);
  const [supportId, setSupportId] = useState(ASTRA_ID);
  const [currentOperator, setCurrentOperator] = useState(YE_ID);
  const [primaryView, setPrimaryView] = useState<EditorView | null>(null);
  const [supportView, setSupportView] = useState<EditorView | null>(null);
  const [moveEntryId, setMoveEntryId] = useState("");
  const [configs, setConfigs] = useState<Record<string, Record<string, unknown>>>({
    [YE_ID]: { core_level: 1, cinema_level: 0, mingxin_active: true, entry_move_uses_linren: true, enemy_stun_vulnerability_bonus: 1.5 },
    [ASTRA_ID]: { core_level: 1, cinema_level: 0, additional_ability_eligible: true },
  });
  const [conditionValues, setConditionValues] = useState<Record<string, boolean | null>>({});
  const [enabledRules, setEnabledRules] = useState<Set<string>>(new Set());
  const [triggerActors, setTriggerActors] = useState<Record<string, string>>({});
  const [stacks, setStacks] = useState<Record<string, number>>({});
  const [buildStats, setBuildStats] = useState<Record<string, { attack: number; crit_rate: number; crit_damage: number }>>({
    [YE_ID]: { ...DEFAULT_STATS },
    [ASTRA_ID]: { ...DEFAULT_STATS },
  });
  const [enemyDefense, setEnemyDefense] = useState(1000);
  const [enemyResistance, setEnemyResistance] = useState(0.2);
  const [stunVulnerability, setStunVulnerability] = useState(1.5);
  const [calculation, setCalculation] = useState<CalculationView | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [diagnostics, setDiagnostics] = useState<string[]>([]);

  const teamIds = useMemo(() => [primaryId, ...(supportId ? [supportId] : [])], [primaryId, supportId]);
  const allRules = useMemo(() => [...(primaryView?.rule_items ?? []), ...(supportView?.rule_items ?? [])], [primaryView, supportView]);
  const allConditions = useMemo(() => [...(primaryView?.scenario_conditions ?? []), ...(supportView?.scenario_conditions ?? [])], [primaryView, supportView]);
  const allTriggers = useMemo(() => [...(primaryView?.scenario_trigger_inputs ?? []), ...(supportView?.scenario_trigger_inputs ?? [])], [primaryView, supportView]);

  const loadEditors = async (nextPrimary = primaryId, nextSupport = supportId, configSource = configs, conditionSource = conditionValues) => {
    setLoading(true);
    try {
      const [main, support] = await Promise.all([
        jsonRequest<EditorView>("/api/v1/definitions/preview", { method: "POST", body: JSON.stringify({ character_id: nextPrimary, team_character_ids: [nextPrimary, ...(nextSupport ? [nextSupport] : [])], condition_values: conditionSource, ...(configSource[nextPrimary] ?? {}) }) }),
        nextSupport
          ? jsonRequest<EditorView>("/api/v1/definitions/preview", { method: "POST", body: JSON.stringify({ character_id: nextSupport, team_character_ids: [nextPrimary, nextSupport], condition_values: conditionSource, ...(configSource[nextSupport] ?? {}) }) })
          : Promise.resolve(null),
      ]);
      setPrimaryView(main);
      setSupportView(support);
      setMoveEntryId((current) => main.moves.some((move) => move.entry_id === current) ? current : (main.moves[0]?.entry_id || ""));
      const nextConditions: Record<string, boolean | null> = {};
      [...main.scenario_conditions, ...(support?.scenario_conditions ?? [])].forEach((item) => { nextConditions[item.condition_id] = item.value; });
      setConditionValues(nextConditions);
      const available = new Set<string>();
      [...main.rule_items, ...(support?.rule_items ?? [])].forEach((item) => { if (item.enabled_by_default) available.add(item.rule_id); });
      setEnabledRules(available);
      const nextTriggers: Record<string, string> = {};
      [...main.scenario_trigger_inputs, ...(support?.scenario_trigger_inputs ?? [])].forEach((item) => { if (item.actor_options[0]) nextTriggers[item.input_id] = item.selected_actor ?? (currentOperator || item.actor_options[0]); });
      setTriggerActors(nextTriggers);
    } catch (error) {
      setDiagnostics([(error as Error).message]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    jsonRequest<Character[]>("/api/v1/characters")
      .then(setCharacters)
      .then(() => loadEditors())
      .catch((error: Error) => setDiagnostics([error.message]));
    // The catalog is the only initial network request; editor loading follows it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateConfig = (characterId: string, key: string, value: unknown) => {
    const nextConfigs = { ...configs, [characterId]: { ...configs[characterId], [key]: value } };
    setConfigs(nextConfigs);
    void loadEditors(primaryId, supportId, nextConfigs);
  };

  const updateBuildStat = (characterId: string, key: "attack" | "crit_rate" | "crit_damage", value: number) => {
    setBuildStats((current) => ({ ...current, [characterId]: { ...current[characterId], [key]: value } }));
  };

  const calculate = async () => {
    if (!moveEntryId) return;
    setCalculating(true);
    setDiagnostics([]);
    try {
      const result = await jsonRequest<CalculationView>("/api/v1/moves/calculate", {
        method: "POST",
        body: JSON.stringify({
          primary_character_id: primaryId,
          supporting_character_ids: supportId ? [supportId] : [],
          team_character_ids: teamIds,
          current_operator: currentOperator,
          move_entry_id: moveEntryId,
          compile_configs: configs,
          condition_values: conditionValues,
          character_builds: Object.fromEntries(teamIds.map((id) => [id, { level: 60, out_of_combat_stats: { ...DEFAULT_STATS, ...(buildStats[id] ?? DEFAULT_STATS) } }])),
          enemy: { enemy_id: "enemy:ui", level: 60, initial_defense: enemyDefense, damage_resistance: { physical: enemyResistance, ether: enemyResistance }, stun_vulnerability_bonus: stunVulnerability },
          enabled_rule_item_ids: [...enabledRules],
          selected_trigger_inputs: Object.entries(triggerActors).map(([input_id, actor_id]) => ({ input_id, actor_id })),
          rule_stack_counts: stacks,
        }),
      });
      setCalculation(result);
    } catch (error) {
      setDiagnostics([(error as Error).message]);
    } finally {
      setCalculating(false);
    }
  };

  const selectedPrimary = characters.find((item) => item.character_id === primaryId);

  return (
    <main className="app-shell">
      <header className="app-header glass-card">
        <div><p className="eyebrow">SPEC-V1 · PRESENTATION-V1</p><h1>ZZZ Calculator</h1><p className="muted">确定性战斗规则解释器</p></div>
        <div className="header-status"><span className="status-dot" /><span>新计算内核</span></div>
      </header>

      <section className="dashboard-grid">
        <section className="glass-card roster-panel">
          <div className="section-heading"><div><p className="eyebrow">ROSTER</p><h2>队伍与当前角色</h2></div><span className="counter">{teamIds.length}/3</span></div>
          <div className="character-grid">
            {characters.map((character) => (
              <button className={`character-card ${primaryId === character.character_id ? "selected" : ""}`} key={character.character_id} onClick={() => { setPrimaryId(character.character_id); setCurrentOperator(character.character_id); loadEditors(character.character_id, character.character_id === supportId ? "" : supportId); }} type="button">
                <img alt={character.display_name} src={character.image_path} style={{ objectPosition: character.image_object_position }} />
                <span className="character-card-copy"><strong>{character.display_name}</strong><small>{character.specialty} · {character.element}</small></span><span className="rarity">{character.rarity}</span>
              </button>
            ))}
          </div>
          <div className="form-grid two-columns">
            <label>支援角色<select value={supportId} onChange={(event) => { const nextSupport = event.target.value; setSupportId(nextSupport); if (currentOperator === supportId) setCurrentOperator(primaryId); loadEditors(primaryId, nextSupport); }}><option value="">无</option>{characters.filter((item) => item.character_id !== primaryId).map((item) => <option key={item.character_id} value={item.character_id}>{item.display_name}</option>)}</select></label>
            <label>当前操作角色<select value={currentOperator} onChange={(event) => setCurrentOperator(event.target.value)}>{teamIds.map((id) => <option key={id} value={id}>{characters.find((item) => item.character_id === id)?.display_name ?? id}</option>)}</select></label>
          </div>
          {selectedPrimary && <div className="selection-summary"><span className="eyebrow">CURRENT OPERATOR</span><strong>{selectedPrimary.display_name}</strong><span className="muted">{selectedPrimary.character_id}</span></div>}
        </section>

        <section className="glass-card build-panel">
          <div className="section-heading"><div><p className="eyebrow">BUILD INPUT</p><h2>局外面板</h2></div><span className="muted">每个角色独立</span></div>
          <div className="build-character-fields">{teamIds.map((id) => <div className="build-character" key={id}><strong>{characters.find((item) => item.character_id === id)?.display_name ?? id}</strong><div className="form-grid three-columns"><label>攻击力<input type="number" value={buildStats[id]?.attack ?? 1000} onChange={(event) => updateBuildStat(id, "attack", Number(event.target.value))} /></label><label>暴击率<input type="number" step="0.01" value={buildStats[id]?.crit_rate ?? 0.5} onChange={(event) => updateBuildStat(id, "crit_rate", Number(event.target.value))} /></label><label>暴击伤害<input type="number" step="0.01" value={buildStats[id]?.crit_damage ?? 0.5} onChange={(event) => updateBuildStat(id, "crit_damage", Number(event.target.value))} /></label></div></div>)}</div>
          <div className="section-heading compact"><div><p className="eyebrow">TARGET</p><h2>敌人</h2></div></div>
          <div className="form-grid three-columns"><label>防御力<input type="number" value={enemyDefense} onChange={(event) => setEnemyDefense(Number(event.target.value))} /></label><label>属性抗性<input type="number" step="0.01" value={enemyResistance} onChange={(event) => setEnemyResistance(Number(event.target.value))} /></label><label>失衡易伤<input type="number" step="0.01" value={stunVulnerability} onChange={(event) => setStunVulnerability(Number(event.target.value))} /></label></div>
        </section>
      </section>

      <section className="workspace-grid">
        <section className="glass-card controls-panel">
          <div className="section-heading"><div><p className="eyebrow">SCENARIO</p><h2>场景与规则</h2></div>{loading && <span className="muted">读取中…</span>}</div>
          <div className="form-grid two-columns config-fields"><label>叶瞬光核心等级<input type="number" min="1" max="7" value={Number(configs[YE_ID]?.core_level ?? 1)} onChange={(event) => updateConfig(YE_ID, "core_level", Number(event.target.value))} /></label><label>叶瞬光影画<input type="number" min="0" max="6" value={Number(configs[YE_ID]?.cinema_level ?? 0)} onChange={(event) => updateConfig(YE_ID, "cinema_level", Number(event.target.value))} /></label><label>耀嘉音核心等级<input type="number" min="1" max="7" value={Number(configs[ASTRA_ID]?.core_level ?? 1)} onChange={(event) => updateConfig(ASTRA_ID, "core_level", Number(event.target.value))} /></label><label>耀嘉音影画<input type="number" min="0" max="6" value={Number(configs[ASTRA_ID]?.cinema_level ?? 0)} onChange={(event) => updateConfig(ASTRA_ID, "cinema_level", Number(event.target.value))} /></label><label className="check-field">叶瞬光：明心境<input type="checkbox" checked={Boolean(configs[YE_ID]?.mingxin_active)} onChange={(event) => updateConfig(YE_ID, "mingxin_active", event.target.checked)} /></label><label className="check-field">叶瞬光：入场结算凛刃<input type="checkbox" checked={Boolean(configs[YE_ID]?.entry_move_uses_linren)} onChange={(event) => updateConfig(YE_ID, "entry_move_uses_linren", event.target.checked)} /></label><label className="check-field">耀嘉音：额外能力<input type="checkbox" checked={Boolean(configs[ASTRA_ID]?.additional_ability_eligible)} onChange={(event) => updateConfig(ASTRA_ID, "additional_ability_eligible", event.target.checked)} /></label></div>
          <div className="control-list">{allConditions.map((condition) => <label className="toggle-row" key={condition.condition_id}><span><strong>{condition.label}</strong><small>{condition.resolution}{condition.editable ? " · 可选" : " · 编译期"}</small></span><input disabled={!condition.editable} type="checkbox" checked={condition.value === true || conditionValues[condition.condition_id] === true} onChange={(event) => { const next = { ...conditionValues, [condition.condition_id]: event.target.checked }; setConditionValues(next); void loadEditors(primaryId, supportId, configs, next); }} /></label>)}</div>
          <div className="rule-list">{allRules.map((rule) => <label className={`rule-row ${rule.availability !== "available" ? "disabled" : ""}`} key={rule.rule_id}><span><strong>{rule.label}</strong><small>{rule.source_label} · {rule.availability}</small></span><input disabled={!rule.toggleable} type="checkbox" checked={enabledRules.has(rule.rule_id)} onChange={(event) => setEnabledRules((current) => { const next = new Set(current); if (event.target.checked) next.add(rule.rule_id); else next.delete(rule.rule_id); return next; })} />{rule.stack.minimum !== null && <input className="stack-input" type="number" min={rule.stack.minimum} max={rule.stack.maximum ?? undefined} value={stacks[rule.rule_id] ?? rule.stack.default ?? rule.stack.minimum} onChange={(event) => setStacks((current) => ({ ...current, [rule.rule_id]: Number(event.target.value) }))} />}</label>)}</div>
          {allTriggers.length > 0 && <><div className="section-heading compact"><div><p className="eyebrow">TRIGGER FACTS</p><h2>场景触发</h2></div></div><div className="form-grid two-columns">{allTriggers.map((trigger) => <label key={trigger.input_id}>{trigger.label}<select value={triggerActors[trigger.input_id] ?? ""} onChange={(event) => setTriggerActors((current) => ({ ...current, [trigger.input_id]: event.target.value }))}><option value="">未指定</option>{trigger.actor_options.map((actor) => <option key={actor} value={actor}>{characters.find((item) => item.character_id === actor)?.display_name ?? actor}</option>)}</select></label>)}</div></>}
        </section>

        <section className="glass-card result-panel">
          <div className="section-heading"><div><p className="eyebrow">MOVE CALCULATION</p><h2>招式结算</h2></div><button className="primary-button" disabled={calculating || loading || !moveEntryId} onClick={calculate} type="button">{calculating ? "计算中…" : "计算"}</button></div>
          <label className="move-select">招式<select value={moveEntryId} onChange={(event) => setMoveEntryId(event.target.value)}>{(primaryView?.moves ?? []).map((move) => <option key={move.entry_id} value={move.entry_id}>{move.label}</option>)}</select></label>
          {calculation ? <div className="calculation-output"><div className="totals-grid">{["non-crit", "expected", "full-crit"].map((mode) => <div className="total-card" key={mode}><small>{mode}</small><strong>{formatNumber(calculation.totals[mode]?.value)}</strong><span className={calculation.totals[mode]?.complete ? "complete" : "incomplete"}>{calculation.totals[mode]?.complete ? "complete" : "partial"}</span></div>)}</div><div className="event-list">{calculation.events.map((event) => <article className="event-card" key={event.semantic_id}><div><strong>{event.label}</strong><small>{event.semantic_id} · ×{event.repeat_count}</small></div><div className="event-values">{["non-crit", "expected", "full-crit"].map((mode) => <span key={mode}><small>{mode} · {event.modes[mode]?.status}</small><b>{formatNumber(event.modes[mode]?.known_value)}</b></span>)}</div><details className="event-details"><summary>查看 breakdown</summary><div className="breakdown-list">{(event.modes.expected?.calculation_breakdown ?? []).map((node) => <div key={node.node}><span>{node.node}</span><b>{formatNumber(node.value)}</b><small>{node.read_rule}</small></div>)}</div>{Object.entries(event.modes).flatMap(([mode, item]) => item.diagnostics.map((diagnostic, index) => <p className="inline-diagnostic" key={`${mode}-${index}`}>{mode}: {diagnostic.message}</p>))}</details></article>)}</div>{calculation.panel_traces.length > 0 && <div className="trace-list"><p className="eyebrow">PANEL PROVENANCE</p>{calculation.panel_traces.map((trace) => <div className="trace-row" key={`${trace.effect_id}-${trace.recipient_character_id}`}><span>{trace.recipient_character_id}</span><strong>+{formatNumber(trace.resolved_value)}</strong><small>{trace.modifier_path} · {trace.effect_id}</small></div>)}</div>}{calculation.resolved_character_snapshots.length > 0 && <div className="trace-list"><p className="eyebrow">RESOLVED PANELS</p>{calculation.resolved_character_snapshots.map((snapshot) => <div className="snapshot-row" key={snapshot.character_id}><strong>{snapshot.character_id}</strong><span>攻击力 {formatNumber(snapshot.stats.attack)}</span><span>暴击率 {formatNumber(snapshot.stats.crit_rate)}</span></div>)}</div>}{calculation.diagnostics.length > 0 && <div className="diagnostic-list">{calculation.diagnostics.map((item, index) => <div className="diagnostic" key={`${item.message}-${index}`}><strong>{item.blocking ? "BLOCKED" : "NOTE"}</strong><span>{item.message}</span></div>)}</div>}</div> : <div className="empty-state"><span className="empty-icon">◈</span><strong>选择招式后开始结算</strong><p className="muted">结果、派生事件和白盒说明将由计算内核返回。</p></div>}
        </section>
      </section>

      {diagnostics.length > 0 && <section className="diagnostics glass-card"><p className="eyebrow">DIAGNOSTICS</p>{diagnostics.map((message) => <div className="diagnostic" key={message}><strong>API</strong><span>{message}</span></div>)}</section>}
    </main>
  );
}

function formatNumber(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 2 }).format(value);
}

export default App;
