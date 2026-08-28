import { useEffect, useMemo, useReducer, useState } from "react";
import { teamReducer } from "./state/teamReducer";
import {
  reconcileEditorState,
  resolveAuthoritativeConditionContext,
  type EditorState,
} from "./state/editorState";

type Character = {
  character_id: string;
  display_name: string;
  rarity: string;
  element: string;
  specialty: string;
  image_path: string;
  image_object_position: string;
};

type WEngine = {
  wengine_id: string;
  display_name: string;
  rarity: string;
  specialty: string;
  icon_key: string;
  signature_character_id: string | null;
};

type Condition = {
  condition_id: string;
  label: string;
  resolution: string;
  value: boolean | null;
  editable: boolean;
};

type Parameter = {
  parameter_id: string;
  label: string;
  resolution: string;
  value: number | null;
  minimum: number;
  maximum: number | null;
};

type CompileField = {
  field_id: string;
  label: string;
  field_type: "integer" | "boolean" | "select";
  value: boolean | number | string;
  minimum: number | null;
  maximum: number | null;
  editable: boolean;
  options: string[];
  help_text: string | null;
};

type Rule = {
  rule_id: string;
  label: string;
  source_label: string;
  source_type?: string;
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
  multiplier_relation: string;
  variants: { label: string; multiplier: number | null; repeat_count: number | null; condition_ids: string[]; repeat_count_parameter_id: string | null }[];
};

type EditorView = {
  character_id: string;
  display_name: string;
  moves: Move[];
  rule_items: Rule[];
  scenario_conditions: Condition[];
  scenario_parameters: Parameter[];
  compile_config_fields: CompileField[];
  scenario_trigger_inputs: {
    input_id: string;
    label: string;
    actor_options: string[];
    selected_actor: string | null;
  }[];
};

type WEngineEditorView = {
  schema_version: string;
  wengine_id: string;
  equipped_character_id: string;
  display_name: string;
  rarity: string;
  specialty: string;
  rule_items: Rule[];
  scenario_conditions: Condition[];
  scenario_parameters: Parameter[];
  scenario_trigger_inputs: {
    input_id: string;
    label: string;
    actor_options: string[];
    selected_actor: string | null;
  }[];
  diagnostics: { message: string; blocking: boolean }[];
};

type CalculationView = {
  move_entry_id: string;
  events: {
    semantic_id: string;
    label: string;
    repeat_count: number;
    modes: Record<string, { value: number | null; known_value: number | null; status: string; diagnostics: { message: string }[]; calculation_breakdown: { node: string; value: number | null; read_rule: string }[] }>;
    common_application_trace: { created_by_effect_id: string | null; rule_matches: { rule_id: string; source_label: string | null; source_type?: string | null; status: string; effects: { effect_id: string; source_label: string | null; source_type?: string | null; status: string }[] }[]; applied_modifiers: { effect_id: string; source_label: string | null; source_type?: string | null; modifier_path: string; value: number | null }[]; event_stat_modifiers: { effect_id: string; source_label: string | null; source_type?: string | null; modifier_path: string; value: number | null }[]; event_multiplier_modifiers: { effect_id: string; source_label: string | null; source_type?: string | null; modifier_path: string; value: number | null }[] } | null;
  }[];
  totals: Record<string, { value: number | null; complete: boolean; diagnostics: { message: string }[] }>;
  diagnostics: { message: string; blocking: boolean }[];
  resolved_character_snapshots: { character_id: string; stats: Record<string, number | null | Record<string, number | null>> }[];
  panel_traces: { recipient_character_id: string; effect_id: string; source_label: string | null; source_type: string | null; resolved_value: number; modifier_path: string }[];
  build_provenance: { character_id: string; contribution_id: string; source_id: string; source_type: string; source_label: string; stat: string; layer: string; value: number | null; element: string | null; unresolved: string | null }[];
};

const YE_ID = "character:1431";
const ASTRA_ID = "character:1311";
const DEFAULT_STATS = { hp: 10000, attack: 1000, defense: 500, impact: 100, anomaly_mastery: 100, anomaly_proficiency: 100, energy_regen: 1.2, crit_rate: 0.5, crit_damage: 0.5, penetration_rate: 0, penetration_flat: 0, element_damage_bonus: { physical: 0, ether: 0 } };

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
  const [wengines, setWengines] = useState<WEngine[]>([]);
  const [{ primaryId, supportId }, dispatchTeam] = useReducer(teamReducer, { primaryId: YE_ID, supportId: ASTRA_ID });
  const [primaryView, setPrimaryView] = useState<EditorView | null>(null);
  const [supportView, setSupportView] = useState<EditorView | null>(null);
  const [wengineViews, setWengineViews] = useState<Record<string, WEngineEditorView | null>>({});
  const [moveEntryId, setMoveEntryId] = useState("");
  const [configs, setConfigs] = useState<Record<string, Record<string, unknown>>>({});
  const [conditionValues, setConditionValues] = useState<Record<string, boolean | null>>({});
  const [parameterValues, setParameterValues] = useState<Record<string, number | null>>({});
  const [enabledRules, setEnabledRules] = useState<Set<string>>(new Set());
  const [disabledRules, setDisabledRules] = useState<Set<string>>(new Set());
  const [triggerActors, setTriggerActors] = useState<Record<string, string>>({});
  const [stacks, setStacks] = useState<Record<string, number>>({});
  const [buildStats, setBuildStats] = useState<Record<string, typeof DEFAULT_STATS>>({
    [YE_ID]: { ...DEFAULT_STATS, element_damage_bonus: { ...DEFAULT_STATS.element_damage_bonus } },
    [ASTRA_ID]: { ...DEFAULT_STATS, element_damage_bonus: { ...DEFAULT_STATS.element_damage_bonus } },
  });
  const [characterLevels, setCharacterLevels] = useState<Record<string, number>>({ [YE_ID]: 60, [ASTRA_ID]: 60 });
  const [buildModes, setBuildModes] = useState<Record<string, "manual-panel" | "equipment-build">>({ [YE_ID]: "manual-panel", [ASTRA_ID]: "manual-panel" });
  const [wengineSelections, setWengineSelections] = useState<Record<string, { id: string; level: number; refinement: number }>>({});
  const [enemyLevel, setEnemyLevel] = useState(60);
  const [enemyDamageReduction, setEnemyDamageReduction] = useState(0);
  const [enemyIsStunned, setEnemyIsStunned] = useState(false);
  const [enemyDefense, setEnemyDefense] = useState(1000);
  const [enemyPhysicalResistance, setEnemyPhysicalResistance] = useState(0.2);
  const [enemyEtherResistance, setEnemyEtherResistance] = useState(0.2);
  const [stunVulnerability, setStunVulnerability] = useState(1.5);
  const [calculation, setCalculation] = useState<CalculationView | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [diagnostics, setDiagnostics] = useState<string[]>([]);

  const teamIds = useMemo(() => [primaryId, ...(supportId ? [supportId] : [])], [primaryId, supportId]);
  const activeWengineViews = useMemo(
    () => teamIds.map((id) => wengineViews[id]).filter((view): view is WEngineEditorView => Boolean(view)),
    [teamIds, wengineViews],
  );
  const allRules = useMemo(() => [
    ...(primaryView?.rule_items ?? []),
    ...(supportView?.rule_items ?? []),
    ...activeWengineViews.flatMap((view) => view.rule_items),
  ], [primaryView, supportView, activeWengineViews]);
  const allConditions = useMemo(() => [
    ...(primaryView?.scenario_conditions ?? []),
    ...(supportView?.scenario_conditions ?? []),
    ...activeWengineViews.flatMap((view) => view.scenario_conditions),
  ], [primaryView, supportView, activeWengineViews]);
  const allParameters = useMemo(() => [
    ...(primaryView?.scenario_parameters ?? []),
    ...(supportView?.scenario_parameters ?? []),
    ...activeWengineViews.flatMap((view) => view.scenario_parameters),
  ], [primaryView, supportView, activeWengineViews]);
  const allTriggers = useMemo(() => [
    ...(primaryView?.scenario_trigger_inputs ?? []),
    ...(supportView?.scenario_trigger_inputs ?? []),
    ...activeWengineViews.flatMap((view) => view.scenario_trigger_inputs),
  ], [primaryView, supportView, activeWengineViews]);
  const allConfigFields = useMemo(() => [
    ...(primaryView?.compile_config_fields ?? []).map((field) => ({ owner: primaryId, field })),
    ...(supportView?.compile_config_fields ?? []).map((field) => ({ owner: supportId, field })),
  ], [primaryId, supportId, primaryView, supportView]);
  const selectedMove = primaryView?.moves.find((move) => move.entry_id === moveEntryId);

  const loadEditors = async (
    nextPrimary = primaryId,
    nextSupport = supportId,
    configSource = configs,
    conditionSource = conditionValues,
    stateOverride: Partial<EditorState> = {},
    wengineSource = wengineSelections,
    buildModesSource = buildModes,
  ) => {
    setLoading(true);
    try {
      const nextTeam = [nextPrimary, ...(nextSupport ? [nextSupport] : [])];
      const [main, support] = await Promise.all([
        jsonRequest<EditorView>("/api/v1/definitions/preview", { method: "POST", body: JSON.stringify({ character_id: nextPrimary, team_character_ids: [nextPrimary, ...(nextSupport ? [nextSupport] : [])], condition_values: conditionSource, compile_config: configSource[nextPrimary] ?? {} }) }),
        nextSupport
          ? jsonRequest<EditorView>("/api/v1/definitions/preview", { method: "POST", body: JSON.stringify({ character_id: nextSupport, team_character_ids: [nextPrimary, nextSupport], condition_values: conditionSource, compile_config: configSource[nextSupport] ?? {} }) })
          : Promise.resolve(null),
      ]);
      const authoritativeConditionContext = resolveAuthoritativeConditionContext(
        conditionSource,
        [
          ...main.scenario_conditions,
          ...(support?.scenario_conditions ?? []),
        ],
      );
      const nextWengineViews = await Promise.all(
        nextTeam.map((owner) => {
          const selection = wengineSource[owner];
          if (!selection?.id || (buildModesSource[owner] ?? "manual-panel") !== "equipment-build") {
            return Promise.resolve(null);
          }
          return jsonRequest<WEngineEditorView>("/api/v1/wengines/preview", {
            method: "POST",
            body: JSON.stringify({
              wengine_id: selection.id,
              equipped_character_id: owner,
              team_character_ids: nextTeam,
              level: selection.level,
              refinement: selection.refinement,
              condition_context: authoritativeConditionContext,
            }),
          });
        }),
      );
      setPrimaryView(main);
      setSupportView(support);
      setWengineViews(Object.fromEntries(nextTeam.map((owner, index) => [owner, nextWengineViews[index] ?? null])));
      setMoveEntryId((current) => main.moves.some((move) => move.entry_id === current) ? current : (main.moves[0]?.entry_id || ""));
      const nextConfigs = { ...configSource };
      ([{ owner: nextPrimary, fields: main.compile_config_fields }, ...(support ? [{ owner: nextSupport, fields: support.compile_config_fields }] : [])]).forEach(({ owner, fields }) => {
        const next = { ...(nextConfigs[owner] ?? {}) };
        fields.forEach((field) => {
          if (field.field_id.startsWith("skill_level:")) {
            const group = field.field_id.slice("skill_level:".length);
            next.skill_levels = { ...((next.skill_levels as Record<string, number> | undefined) ?? {}), [group]: field.value };
          } else {
            next[field.field_id] = field.value;
          }
        });
        nextConfigs[owner] = next;
      });
      setConfigs(nextConfigs);
      const reconciled = reconcileEditorState(
        {
          conditionValues: authoritativeConditionContext,
          parameterValues,
          enabledRules,
          disabledRules,
          triggerActors,
          stacks,
          ...stateOverride,
        },
          {
            conditions: [
              ...main.scenario_conditions,
              ...(support?.scenario_conditions ?? []),
              ...nextWengineViews.flatMap((view) => view?.scenario_conditions ?? []),
            ],
            parameters: [
              ...main.scenario_parameters,
              ...(support?.scenario_parameters ?? []),
              ...nextWengineViews.flatMap((view) => view?.scenario_parameters ?? []),
            ],
            rules: [
              ...main.rule_items,
              ...(support?.rule_items ?? []),
              ...nextWengineViews.flatMap((view) => view?.rule_items ?? []),
            ],
            triggers: [
              ...main.scenario_trigger_inputs,
              ...(support?.scenario_trigger_inputs ?? []),
              ...nextWengineViews.flatMap((view) => view?.scenario_trigger_inputs ?? []),
            ],
          },
        nextTeam,
      );
      setConditionValues(reconciled.conditionValues);
      setParameterValues(reconciled.parameterValues);
      setEnabledRules(reconciled.enabledRules);
      setDisabledRules(reconciled.disabledRules);
      setTriggerActors(reconciled.triggerActors);
      setStacks(reconciled.stacks);
    } catch (error) {
      setDiagnostics([(error as Error).message]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    Promise.all([
      jsonRequest<Character[]>("/api/v1/characters"),
      jsonRequest<WEngine[]>("/api/v1/wengines"),
    ])
      .then(([loadedCharacters, loadedWengines]) => {
        setCharacters(loadedCharacters);
        setWengines(loadedWengines);
        const nextSelections = loadedWengines.reduce<Record<string, { id: string; level: number; refinement: number }>>((current, item) => {
          const owner = item.signature_character_id;
          if (owner && !current[owner]) {
            current[owner] = { id: item.wengine_id, level: 60, refinement: 1 };
          }
          return current;
        }, {});
        setWengineSelections((current) => {
          const next = { ...nextSelections, ...current };
          loadedWengines.forEach((item) => {
            if (item.signature_character_id && !next[item.signature_character_id]) {
              next[item.signature_character_id] = { id: item.wengine_id, level: 60, refinement: 1 };
            }
          });
          return next;
        });
        return loadEditors(primaryId, supportId, configs, conditionValues, {}, nextSelections);
      })
      .catch((error: Error) => setDiagnostics([error.message]));
    // The catalog is the only initial network request; editor loading follows it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateConfig = (characterId: string, key: string, value: unknown) => {
    const nextConfigs = { ...configs, [characterId]: { ...configs[characterId], [key]: value } };
    setConfigs(nextConfigs);
    void loadEditors(primaryId, supportId, nextConfigs, conditionValues, {}, wengineSelections);
  };

  const updateBuildStat = (characterId: string, key: "attack" | "crit_rate" | "crit_damage" | "penetration_rate" | "penetration_flat", value: number) => {
    setBuildStats((current) => ({ ...current, [characterId]: { ...current[characterId], [key]: value } }));
  };

  const updateElementBonus = (characterId: string, element: "physical" | "ether", value: number) => {
    setBuildStats((current) => ({ ...current, [characterId]: { ...current[characterId], element_damage_bonus: { ...current[characterId]?.element_damage_bonus, [element]: value } } }));
  };

  const updateConfigField = (owner: string, field: CompileField, value: boolean | number | string) => {
    if (field.field_id.startsWith("skill_level:")) {
      const group = field.field_id.slice("skill_level:".length);
      const nextConfigs = { ...configs, [owner]: { ...configs[owner], skill_levels: { ...((configs[owner]?.skill_levels as Record<string, number> | undefined) ?? {}), [group]: Number(value) } } };
      setConfigs(nextConfigs);
      void loadEditors(primaryId, supportId, nextConfigs, conditionValues, {}, wengineSelections);
      return;
    }
    updateConfig(owner, field.field_id, value);
  };

  const selectVariant = (variantIndex: number) => {
    if (!selectedMove) return;
    const next = { ...conditionValues };
    selectedMove.variants.forEach((variant, index) => variant.condition_ids.forEach((conditionId) => { next[conditionId] = index === variantIndex; }));
    setConditionValues(next);
    void loadEditors(primaryId, supportId, configs, next, { conditionValues: next }, wengineSelections);
  };

  const updateWengineSelection = (
    owner: string,
    selection: { id: string; level: number; refinement: number },
  ) => {
    const nextSelections = { ...wengineSelections, [owner]: selection };
    setWengineSelections(nextSelections);
    void loadEditors(primaryId, supportId, configs, conditionValues, {}, nextSelections);
  };

  const updateBuildMode = (owner: string, mode: "manual-panel" | "equipment-build") => {
    const nextModes = { ...buildModes, [owner]: mode };
    setBuildModes(nextModes);
    void loadEditors(primaryId, supportId, configs, conditionValues, {}, wengineSelections, nextModes);
  };

  const buildPayloads = () => Object.fromEntries(teamIds.map((id) => {
    const mode = buildModes[id] ?? "manual-panel";
    const selection = wengineSelections[id];
    if (mode === "equipment-build") {
      return [id, {
        level: characterLevels[id] ?? 60,
        build_mode: mode,
        base_stats: { ...buildStats[id], element_damage_bonus: { ...buildStats[id]?.element_damage_bonus } },
        ...(selection?.id ? { wengine_id: selection.id, wengine_level: selection.level, wengine_refinement: selection.refinement } : {}),
      }];
    }
    return [id, { level: characterLevels[id] ?? 60, out_of_combat_stats: { ...buildStats[id], element_damage_bonus: { ...buildStats[id]?.element_damage_bonus } } }];
  }));

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
          move_entry_id: moveEntryId,
          compile_configs: configs,
          condition_values: Object.fromEntries(
            allConditions
              .filter((condition) => condition.editable)
              .map((condition) => [condition.condition_id, conditionValues[condition.condition_id] ?? null]),
          ),
          parameter_values: parameterValues,
          character_builds: buildPayloads(),
          enemy: { enemy_id: "enemy:ui", level: enemyLevel, initial_defense: enemyDefense, damage_resistance: { physical: enemyPhysicalResistance, ether: enemyEtherResistance }, damage_reduction: enemyDamageReduction, stun_vulnerability_bonus: stunVulnerability, is_stunned: enemyIsStunned },
          enabled_rule_item_ids: [...enabledRules],
          selected_trigger_inputs: Object.entries(triggerActors).filter(([, actor_id]) => actor_id).map(([input_id, actor_id]) => ({ input_id, actor_id })),
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
  const configFieldValue = (owner: string, field: CompileField) => {
    if (field.field_id.startsWith("skill_level:")) {
      const group = field.field_id.slice("skill_level:".length);
      return ((configs[owner]?.skill_levels as Record<string, number> | undefined)?.[group] ?? field.value);
    }
    return configs[owner]?.[field.field_id] ?? field.value;
  };

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
              <button className={`character-card ${primaryId === character.character_id ? "selected" : ""}`} key={character.character_id} onClick={() => { const nextSupport = character.character_id === supportId ? primaryId : supportId; dispatchTeam({ type: "select-primary", characterId: character.character_id }); loadEditors(character.character_id, nextSupport); }} type="button">
                <img alt={character.display_name} src={character.image_path} style={{ objectPosition: character.image_object_position }} />
                <span className="character-card-copy"><strong>{character.display_name}</strong><small>{character.specialty} · {character.element}</small></span><span className="rarity">{character.rarity}</span>
              </button>
            ))}
          </div>
          <div className="form-grid two-columns">
            <label>支援角色<select value={supportId} onChange={(event) => { const nextSupport = event.target.value === primaryId ? "" : event.target.value; dispatchTeam({ type: "select-support", characterId: nextSupport }); loadEditors(primaryId, nextSupport); }}><option value="">无</option>{characters.filter((item) => item.character_id !== primaryId).map((item) => <option key={item.character_id} value={item.character_id}>{item.display_name}</option>)}</select></label>
            <label>当前操作角色<input readOnly value={characters.find((item) => item.character_id === primaryId)?.display_name ?? primaryId} /></label>
          </div>
          {selectedPrimary && <div className="selection-summary"><span className="eyebrow">CURRENT OPERATOR</span><strong>{selectedPrimary.display_name}</strong><span className="muted">{selectedPrimary.character_id}</span></div>}
        </section>

        <section className="glass-card build-panel">
          <div className="section-heading"><div><p className="eyebrow">BUILD INPUT</p><h2>局外面板</h2></div><span className="muted">每个角色独立</span></div>
          <div className="build-character-fields">{teamIds.map((id) => <div className="build-character" key={id}><strong>{characters.find((item) => item.character_id === id)?.display_name ?? id}</strong><div className="form-grid three-columns"><label>面板模式<select value={buildModes[id] ?? "manual-panel"} onChange={(event) => updateBuildMode(id, event.target.value as "manual-panel" | "equipment-build")}><option value="manual-panel">手工局外面板</option><option value="equipment-build">装备配置</option></select></label><label>等级<input type="number" min="1" max="60" value={characterLevels[id] ?? 60} onChange={(event) => setCharacterLevels((current) => ({ ...current, [id]: Number(event.target.value) }))} /></label><label>攻击力<input type="number" value={buildStats[id]?.attack ?? 1000} onChange={(event) => updateBuildStat(id, "attack", Number(event.target.value))} /></label><label>暴击率<input type="number" step="0.01" value={buildStats[id]?.crit_rate ?? 0.5} onChange={(event) => updateBuildStat(id, "crit_rate", Number(event.target.value))} /></label><label>暴击伤害<input type="number" step="0.01" value={buildStats[id]?.crit_damage ?? 0.5} onChange={(event) => updateBuildStat(id, "crit_damage", Number(event.target.value))} /></label><label>穿透率<input type="number" step="0.01" value={buildStats[id]?.penetration_rate ?? 0} onChange={(event) => updateBuildStat(id, "penetration_rate", Number(event.target.value))} /></label><label>穿透值<input type="number" value={buildStats[id]?.penetration_flat ?? 0} onChange={(event) => updateBuildStat(id, "penetration_flat", Number(event.target.value))} /></label><label>物理伤害加成<input type="number" step="0.01" value={buildStats[id]?.element_damage_bonus.physical ?? 0} onChange={(event) => updateElementBonus(id, "physical", Number(event.target.value))} /></label><label>以太伤害加成<input type="number" step="0.01" value={buildStats[id]?.element_damage_bonus.ether ?? 0} onChange={(event) => updateElementBonus(id, "ether", Number(event.target.value))} /></label></div>{(buildModes[id] ?? "manual-panel") === "equipment-build" && <div className="form-grid three-columns"><label>音擎<select value={wengineSelections[id]?.id ?? ""} onChange={(event) => updateWengineSelection(id, { ...(wengineSelections[id] ?? { level: 60, refinement: 1 }), id: event.target.value })}><option value="">无</option>{wengines.filter((item) => item.specialty === characters.find((character) => character.character_id === id)?.specialty).map((item) => <option key={item.wengine_id} value={item.wengine_id}>{item.display_name}</option>)}</select></label><label>音擎等级<input type="number" min="60" max="60" value={wengineSelections[id]?.level ?? 60} readOnly /></label><label>精炼<input type="number" min="1" max="5" value={wengineSelections[id]?.refinement ?? 1} onChange={(event) => updateWengineSelection(id, { ...(wengineSelections[id] ?? { id: "", level: 60 }), refinement: Number(event.target.value) })} /></label></div>}</div>)}</div>
          {calculation && calculation.build_provenance.length > 0 && <div className="trace-list"><p className="eyebrow">BUILD PROVENANCE</p>{calculation.build_provenance.map((trace) => <div className="trace-row" key={trace.contribution_id}><span>{trace.character_id}</span><strong>{trace.value === null ? "?" : `+${formatNumber(trace.value)}`}</strong><small>{trace.source_label} · {trace.stat} · {trace.layer}</small></div>)}</div>}
          <div className="section-heading compact"><div><p className="eyebrow">TARGET</p><h2>敌人</h2></div></div>
          <div className="form-grid three-columns"><label>等级<input type="number" min="1" max="80" value={enemyLevel} onChange={(event) => setEnemyLevel(Number(event.target.value))} /></label><label>防御力<input type="number" value={enemyDefense} onChange={(event) => setEnemyDefense(Number(event.target.value))} /></label><label>物理抗性<input type="number" step="0.01" value={enemyPhysicalResistance} onChange={(event) => setEnemyPhysicalResistance(Number(event.target.value))} /></label><label>以太抗性<input type="number" step="0.01" value={enemyEtherResistance} onChange={(event) => setEnemyEtherResistance(Number(event.target.value))} /></label><label>失衡易伤<input type="number" step="0.01" value={stunVulnerability} onChange={(event) => setStunVulnerability(Number(event.target.value))} /></label><label>减易伤<input type="number" step="0.01" value={enemyDamageReduction} onChange={(event) => setEnemyDamageReduction(Number(event.target.value))} /></label><label className="check-field">当前处于失衡<input type="checkbox" checked={enemyIsStunned} onChange={(event) => setEnemyIsStunned(event.target.checked)} /></label></div>
        </section>
      </section>

      <section className="workspace-grid">
        <section className="glass-card controls-panel">
          <div className="section-heading"><div><p className="eyebrow">SCENARIO</p><h2>场景与规则</h2></div>{loading && <span className="muted">读取中…</span>}</div>
          <div className="form-grid two-columns config-fields">{allConfigFields.map(({ owner, field }) => <label className={field.field_type === "boolean" ? "check-field" : ""} key={`${owner}-${field.field_id}`}>{field.label}{field.field_type === "boolean" ? <input disabled={!field.editable} type="checkbox" checked={Boolean(configFieldValue(owner, field))} onChange={(event) => updateConfigField(owner, field, event.target.checked)} /> : field.field_type === "select" ? <select disabled={!field.editable} value={String(configFieldValue(owner, field))} onChange={(event) => updateConfigField(owner, field, Number(event.target.value))}>{field.options.map((option) => <option key={option} value={option}>{option}</option>)}</select> : <input disabled={!field.editable} type="number" min={field.minimum ?? undefined} max={field.maximum ?? undefined} value={Number(configFieldValue(owner, field))} onChange={(event) => updateConfigField(owner, field, Number(event.target.value))} />}</label>)}</div>
          <div className="control-list">{allConditions.map((condition) => <label className="toggle-row" key={condition.condition_id}><span><strong>{condition.label}</strong><small>{condition.resolution}{condition.editable ? " · 可选" : " · 编译期"}</small></span><input disabled={!condition.editable} type="checkbox" checked={condition.value === true || conditionValues[condition.condition_id] === true} onChange={(event) => { const next = { ...conditionValues, [condition.condition_id]: event.target.checked }; setConditionValues(next); void loadEditors(primaryId, supportId, configs, next, { conditionValues: next }); }} /></label>)}</div>
          {allParameters.length > 0 && <div className="parameter-list"><div className="section-heading compact"><div><p className="eyebrow">SCENARIO PARAMETERS</p><h2>次数与数值输入</h2></div></div>{allParameters.map((parameter) => <label key={parameter.parameter_id}>{parameter.label}<input type="number" min={parameter.minimum} max={parameter.maximum ?? undefined} placeholder={parameter.value === null ? "未指定" : undefined} value={parameterValues[parameter.parameter_id] ?? parameter.value ?? ""} onChange={(event) => setParameterValues((current) => ({ ...current, [parameter.parameter_id]: event.target.value === "" ? null : Number(event.target.value) }))} /></label>)}</div>}
          {selectedMove && selectedMove.multiplier_relation === "mutually-exclusive-variant" && <div className="variant-control"><div className="section-heading compact"><div><p className="eyebrow">MULTIPLIER VARIANT</p><h2>倍率版本</h2></div></div>{selectedMove.variants.map((variant, index) => <label className="variant-option" key={`${selectedMove.entry_id}-${index}`}><input name="move-variant" type="radio" checked={variant.condition_ids.length > 0 && variant.condition_ids.every((conditionId) => conditionValues[conditionId] === true)} onChange={() => selectVariant(index)} /><span>{variant.label}</span></label>)}</div>}
          <div className="rule-list">{allRules.map((rule) => <label className={`rule-row ${rule.availability !== "available" ? "disabled" : ""}`} key={rule.rule_id}><span><strong>{rule.label}</strong><small>{rule.source_label} · {rule.availability}</small></span><input disabled={!rule.toggleable} type="checkbox" checked={enabledRules.has(rule.rule_id)} onChange={(event) => { const checked = event.target.checked; setEnabledRules((current) => { const next = new Set(current); if (checked) next.add(rule.rule_id); else next.delete(rule.rule_id); return next; }); setDisabledRules((current) => { const next = new Set(current); if (checked) next.delete(rule.rule_id); else next.add(rule.rule_id); return next; }); }} />{rule.stack.minimum !== null && <input className="stack-input" type="number" min={rule.stack.minimum} max={rule.stack.maximum ?? undefined} value={stacks[rule.rule_id] ?? rule.stack.default ?? rule.stack.minimum} onChange={(event) => setStacks((current) => ({ ...current, [rule.rule_id]: Number(event.target.value) }))} />}</label>)}</div>
          {allTriggers.length > 0 && <><div className="section-heading compact"><div><p className="eyebrow">TRIGGER FACTS</p><h2>场景触发</h2></div></div><div className="form-grid two-columns">{allTriggers.map((trigger) => <label key={trigger.input_id}>{trigger.label}<select value={triggerActors[trigger.input_id] ?? ""} onChange={(event) => setTriggerActors((current) => { const next = { ...current }; if (event.target.value) next[trigger.input_id] = event.target.value; else delete next[trigger.input_id]; return next; })}><option value="">未指定</option>{trigger.actor_options.map((actor) => <option key={actor} value={actor}>{characters.find((item) => item.character_id === actor)?.display_name ?? actor}</option>)}</select></label>)}</div></>}
        </section>

        <section className="glass-card result-panel">
          <div className="section-heading"><div><p className="eyebrow">MOVE CALCULATION</p><h2>招式结算</h2></div><button className="primary-button" disabled={calculating || loading || !moveEntryId} onClick={calculate} type="button">{calculating ? "计算中…" : "计算"}</button></div>
          <label className="move-select">招式<select value={moveEntryId} onChange={(event) => setMoveEntryId(event.target.value)}>{(primaryView?.moves ?? []).map((move) => <option key={move.entry_id} value={move.entry_id}>{move.label}</option>)}</select></label>
          {calculation ? <div className="calculation-output"><div className="totals-grid">{["non-crit", "expected", "full-crit"].map((mode) => <div className="total-card" key={mode}><small>{mode}</small><strong>{formatNumber(calculation.totals[mode]?.value)}</strong><span className={calculation.totals[mode]?.complete ? "complete" : "incomplete"}>{calculation.totals[mode]?.complete ? "complete" : "partial"}</span></div>)}</div><div className="event-list">{calculation.events.map((event) => <article className="event-card" key={event.semantic_id}><div><strong>{event.label}</strong><small>{event.semantic_id} · ×{event.repeat_count}</small></div><div className="event-values">{["non-crit", "expected", "full-crit"].map((mode) => <span key={mode}><small>{mode} · {event.modes[mode]?.status}</small><b>{formatNumber(event.modes[mode]?.known_value)}</b></span>)}</div><details className="event-details"><summary>查看 breakdown</summary><div className="breakdown-list">{(event.modes.expected?.calculation_breakdown ?? []).map((node) => <div key={node.node}><span>{node.node}</span><b>{formatNumber(node.value)}</b><small>{node.read_rule}</small></div>)}</div>{event.common_application_trace && <div className="application-trace"><p className="eyebrow">RULE / EFFECT TRACE</p>{event.common_application_trace.rule_matches.filter((match) => match.status !== "not-matched").map((match) => <div className="trace-match" key={match.rule_id}><strong>{match.source_label ?? match.rule_id}</strong><span>{match.status}</span>{match.effects.filter((effect) => effect.status === "matched").map((effect) => <small key={effect.effect_id}>{effect.source_label ?? effect.effect_id}</small>)}</div>)}{[...event.common_application_trace.applied_modifiers, ...event.common_application_trace.event_stat_modifiers, ...event.common_application_trace.event_multiplier_modifiers].map((modifier) => <div className="trace-match" key={modifier.effect_id}><strong>{modifier.source_label ?? modifier.effect_id}</strong><span>{modifier.modifier_path}</span><small>{formatNumber(modifier.value)}</small></div>)}</div>}{Object.entries(event.modes).flatMap(([mode, item]) => item.diagnostics.map((diagnostic, index) => <p className="inline-diagnostic" key={`${mode}-${index}`}>{mode}: {diagnostic.message}</p>))}</details></article>)}</div>{calculation.panel_traces.length > 0 && <div className="trace-list"><p className="eyebrow">PANEL PROVENANCE</p>{calculation.panel_traces.map((trace) => <div className="trace-row" key={`${trace.effect_id}-${trace.recipient_character_id}`}><span>{trace.recipient_character_id}</span><strong>+{formatNumber(trace.resolved_value)}</strong><small>{trace.source_label ?? trace.effect_id} · {trace.modifier_path}</small></div>)}</div>}{calculation.resolved_character_snapshots.length > 0 && <div className="trace-list"><p className="eyebrow">RESOLVED PANELS</p>{calculation.resolved_character_snapshots.map((snapshot) => <div className="snapshot-row" key={snapshot.character_id}><strong>{snapshot.character_id}</strong><span>攻击力 {formatNumber(typeof snapshot.stats.attack === "number" ? snapshot.stats.attack : null)}</span><span>暴击率 {formatNumber(typeof snapshot.stats.crit_rate === "number" ? snapshot.stats.crit_rate : null)}</span><span>属性加成 {formatElementBonuses(snapshot.stats.element_damage_bonus)}</span></div>)}</div>}{calculation.diagnostics.length > 0 && <div className="diagnostic-list">{calculation.diagnostics.map((item, index) => <div className="diagnostic" key={`${item.message}-${index}`}><strong>{item.blocking ? "BLOCKED" : "NOTE"}</strong><span>{item.message}</span></div>)}</div>}</div> : <div className="empty-state"><span className="empty-icon">◈</span><strong>选择招式后开始结算</strong><p className="muted">结果、派生事件和白盒说明将由计算内核返回。</p></div>}
        </section>
      </section>

      {diagnostics.length > 0 && <section className="diagnostics glass-card"><p className="eyebrow">DIAGNOSTICS</p>{diagnostics.map((message) => <div className="diagnostic" key={message}><strong>API</strong><span>{message}</span></div>)}</section>}
    </main>
  );
}

function formatNumber(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 2 }).format(value);
}

function formatElementBonuses(value: number | Record<string, number | null> | null) {
  if (!value || typeof value !== "object") return "—";
  return Object.entries(value).map(([element, amount]) => `${element} ${formatNumber(amount)}`).join(" · ") || "—";
}

export default App;
