import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import DriveDiscCard from "./components/DriveDiscCard";
import EventTraceDetails, { type EventTraceEnvelope } from "./components/EventTraceDetails";
import NumberField from "./components/NumberField";
import { calculationTeamOrder, createTeamState, teamReducer, type TeamAction } from "./state/teamReducer";
import {
  conditionValuesForViews,
  matchingMoveVariantIndexes,
  projectMoveOptions,
  reconcileEditorState,
  resolveAuthoritativeConditionContext,
  selectMoveVariantConditions,
  type EditorState,
  type MoveVariantProjection,
} from "./state/editorState";
import {
  addDriveDiscSubstat,
  removeDriveDiscSubstat,
  replaceDriveDiscSubstat,
  selectDriveDiscSetValue,
  updateDriveDiscMainValue,
  updateDriveDiscSubstatRollCount,
  type DriveDiscConfig,
  type DriveDiscStatOption,
  type DriveDiscSubstat,
} from "./state/driveDiscState";
import {
  formatBuildContributionValue,
  formatDriveStatValue,
  formatPreviewRatio,
} from "./state/buildPreview";
import {
  createEquipmentConfig,
  parseEquipmentConfig,
  serializeEquipmentConfig,
} from "./state/equipmentConfig";
import { filterCharacterCatalog, isCharacterSelectable } from "./state/characterLibrary";
import { aggregateEditorViews } from "./state/editorAggregation";

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

type DriveDiscSet = {
  set_id: string;
  display_name: string;
  icon_path: string;
  two_piece_text: string;
  four_piece_text: string;
  two_piece_disposition: string;
  four_piece_disposition: string;
  ignored_two_piece_reason: string | null;
  ignored_four_piece_reason: string | null;
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
  variants: { variant_id: string; label: string; multiplier: number | null; repeat_count: number | null; condition_ids: string[]; repeat_count_parameter_id: string | null }[];
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
  diagnostics: { diagnostic_id: string; message: string; blocking: boolean }[];
};

type DriveDiscEditorView = {
  schema_version: string;
  equipped_character_id: string;
  set_counts: { set_id: string; count: number }[];
  slot_schemas: { slot: number; main_stat_options: DriveDiscStatOption[] }[];
  substat_options: DriveDiscStatOption[];
  rule_items: Rule[];
  scenario_conditions: Condition[];
  scenario_trigger_inputs: {
    input_id: string;
    label: string;
    actor_options: string[];
    selected_actor: string | null;
  }[];
  diagnostics: { diagnostic_id: string; message: string; blocking: boolean }[];
};

type BuildPreviewStat = number | null | Record<string, number | null>;

type BuildPreviewContribution = {
  character_id: string;
  contribution_id: string;
  source_id: string;
  source_type: string;
  source_label: string;
  stat: string;
  layer: string;
  value: number | null;
  element: string | null;
  unresolved: string | null;
};

type DriveDiscStatPreview = {
  stat_key: string;
  label: string;
  value_per_roll: number;
  display_value_per_roll: string;
  roll_count: number;
  total_value: number;
  display_total_value: string;
};

type BuildPreviewDisc = {
  slot: number;
  set_id: string;
  set_name: string;
  main_stat: DriveDiscStatPreview | null;
  substats: DriveDiscStatPreview[];
  total_rolls: number;
  complete: boolean;
};

type BuildPreview = {
  schema_version: string;
  character_id: string;
  display_name: string;
  level: number;
  build_mode: "equipment-build";
  base_stats: Record<string, BuildPreviewStat>;
  out_of_combat_stats: Record<string, BuildPreviewStat>;
  provenance: BuildPreviewContribution[];
  drive_discs: BuildPreviewDisc[];
  set_counts: { set_id: string; count: number }[];
  diagnostics: { diagnostic_id: string; message: string; blocking: boolean }[];
  complete: boolean;
};

type CalculationView = {
  move_entry_id: string;
  display_modes?: string[];
  events: {
    semantic_id: string;
    label: string;
    repeat_count: number;
    crit_capability?: string;
    display_modes?: string[];
    modes: Record<string, { value: number | null; known_value: number | null; status: string; diagnostics: { message: string }[]; calculation_breakdown: { node: string; value: number | null; read_rule: string }[] }>;
    common_application_trace: EventTraceEnvelope | null;
  }[];
  totals: Record<string, { value: number | null; complete: boolean; diagnostics: { message: string }[] }>;
  diagnostics: { message: string; blocking: boolean }[];
  resolved_character_snapshots: { character_id: string; stats: Record<string, number | null | Record<string, number | null>> }[];
  panel_traces: { recipient_character_id: string; effect_id: string; source_label: string | null; source_type: string | null; resolved_value: number; modifier_path: string }[];
  build_provenance: { character_id: string; contribution_id: string; source_id: string; source_type: string; source_label: string; stat: string; layer: string; value: number | null; element: string | null; unresolved: string | null }[];
};

const YE_ID = "character:1431";
const ASTRA_ID = "character:1311";
const DEFAULT_STATS = { hp: 10000, attack: 1000, defense: 500, impact: 100, anomaly_mastery: 100, anomaly_proficiency: 100, energy_regen: 1.2, crit_rate: 0.5, crit_damage: 0.5, penetration_rate: 0, penetration_flat: 0, element_damage_bonus: { physical: 0, ether: 0, electric: 0 } };

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
  const [driveDiscSets, setDriveDiscSets] = useState<DriveDiscSet[]>([]);
  const [teamState, dispatchTeam] = useReducer(teamReducer, createTeamState([YE_ID, ASTRA_ID]));
  const { teamCharacterIds, currentOperatorId } = teamState;
  const [editorViews, setEditorViews] = useState<Record<string, EditorView | null>>({});
  const [wengineViews, setWengineViews] = useState<Record<string, WEngineEditorView | null>>({});
  const [driveDiscViews, setDriveDiscViews] = useState<Record<string, DriveDiscEditorView | null>>({});
  const [moveEntryId, setMoveEntryId] = useState("");
  const [configs, setConfigs] = useState<Record<string, Record<string, unknown>>>({});
  const [conditionValues, setConditionValues] = useState<Record<string, boolean | null>>({});
  const [parameterValues, setParameterValues] = useState<Record<string, number | null>>({});
  const conditionValuesRef = useRef<Record<string, boolean | null>>({});
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
  const [driveDiscSelections, setDriveDiscSelections] = useState<Record<string, DriveDiscConfig[]>>({});
  const [buildPreviews, setBuildPreviews] = useState<Record<string, BuildPreview | null>>({});
  const [enemyLevel, setEnemyLevel] = useState(60);
  const [enemyDamageReduction, setEnemyDamageReduction] = useState(0);
  const [enemyIsStunned, setEnemyIsStunned] = useState(false);
  const [enemyDefense, setEnemyDefense] = useState(1000);
  const [enemyPhysicalResistance, setEnemyPhysicalResistance] = useState(0.2);
  const [enemyEtherResistance, setEnemyEtherResistance] = useState(0.2);
  const [enemyElectricResistance, setEnemyElectricResistance] = useState(0.2);
  const [stunVulnerability, setStunVulnerability] = useState(1.5);
  const [calculation, setCalculation] = useState<CalculationView | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [diagnostics, setDiagnostics] = useState<string[]>([]);
  const [equipmentFeedback, setEquipmentFeedback] = useState<Record<string, { kind: "success" | "error"; message: string }>>({});
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [librarySlot, setLibrarySlot] = useState<number | null>(null);
  const [libraryQuery, setLibraryQuery] = useState("");
  const [librarySpecialty, setLibrarySpecialty] = useState("");
  const [libraryElement, setLibraryElement] = useState("");
  const editorGeneration = useRef(0);
  const editorAbortController = useRef<AbortController | null>(null);
  const equipmentImportInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const commitConditionValues = (next: Record<string, boolean | null>) => {
    conditionValuesRef.current = next;
    setConditionValues(next);
  };

  const teamIds = teamCharacterIds;
  const requestTeam = useMemo(() => calculationTeamOrder(teamIds, currentOperatorId), [teamIds, currentOperatorId]);
  const supportingIds = requestTeam.supportingCharacterIds;
  const aggregatedEditors = useMemo(
    () => aggregateEditorViews(teamIds, editorViews, wengineViews, driveDiscViews),
    [teamIds, editorViews, wengineViews, driveDiscViews],
  );
  const allRules = aggregatedEditors.ruleItems;
  const allConditions = aggregatedEditors.conditions;
  const allParameters = aggregatedEditors.parameters;
  const allTriggers = aggregatedEditors.triggers;
  const allConfigFields = aggregatedEditors.configFields;
  const operatorMoves = editorViews[currentOperatorId]?.moves ?? [];
  const moveOptions = useMemo(
    () => projectMoveOptions(operatorMoves),
    [operatorMoves],
  );
  const selectedMove = operatorMoves.find((move) => move.entry_id === moveEntryId);
  const selectedMoveVariantIndexes = selectedMove
    ? matchingMoveVariantIndexes(selectedMove, conditionValues)
    : [];
  const selectedMoveOption: MoveVariantProjection | undefined = selectedMove
    ? selectedMove.multiplier_relation === "mutually-exclusive-variant"
      ? selectedMoveVariantIndexes.length === 1
        ? moveOptions.find((option) => (
          option.entryId === selectedMove.entry_id
          && option.variantIndex === selectedMoveVariantIndexes[0]
        ))
        : undefined
      : moveOptions.find((option) => option.entryId === selectedMove.entry_id)
    : undefined;
  const moveSelectionIssue = !selectedMove
    ? "请选择招式"
    : selectedMove.multiplier_relation === "mutually-exclusive-variant"
      ? selectedMoveVariantIndexes.length === 1
        ? null
        : selectedMoveVariantIndexes.length === 0
          ? `${selectedMove.label}需要选择一个倍率版本`
          : `${selectedMove.label}的倍率条件冲突，请只保留一个版本`
      : null;
  const moveVariantConditionIds = useMemo(() => new Set(
    teamIds
      .flatMap((owner) => editorViews[owner]?.moves ?? [])
      .filter((move) => move.multiplier_relation === "mutually-exclusive-variant")
      .flatMap((move) => move.variants.flatMap((variant) => variant.condition_ids)),
  ), [editorViews, teamIds]);
  const visibleScenarioConditions = useMemo(() => {
    const seen = new Set<string>();
    return allConditions.filter((condition) => {
      if (!condition.editable || moveVariantConditionIds.has(condition.condition_id)) {
        return false;
      }
      if (seen.has(condition.condition_id)) return false;
      seen.add(condition.condition_id);
      return true;
    });
  }, [allConditions, moveVariantConditionIds]);

  const loadEditors = async (
    nextTeam: string[] = teamIds,
    nextOperator = currentOperatorId,
    configSource = configs,
    conditionSource = conditionValuesRef.current,
    stateOverride: Partial<EditorState> = {},
    wengineSource = wengineSelections,
    buildModesSource = buildModes,
    driveDiscSource = driveDiscSelections,
    characterLevelsSource = characterLevels,
  ) => {
    const generation = editorGeneration.current + 1;
    editorGeneration.current = generation;
    editorAbortController.current?.abort();
    const abortController = new AbortController();
    editorAbortController.current = abortController;
    setLoading(true);
    try {
      const normalizedTeam = [...new Set(nextTeam)].slice(0, 3);
      const normalizedOperator = normalizedTeam.includes(nextOperator)
        ? nextOperator
        : normalizedTeam[0] ?? "";
      const nextEditorViews = await Promise.all(
        normalizedTeam.map((owner) => jsonRequest<EditorView>("/api/v1/definitions/preview", {
          method: "POST",
          body: JSON.stringify({
            character_id: owner,
            team_character_ids: normalizedTeam,
            condition_values: conditionSource,
            compile_config: configSource[owner] ?? {},
          }),
          signal: abortController.signal,
        })),
      );
      const authoritativeConditionContext = resolveAuthoritativeConditionContext(
        conditionSource,
        nextEditorViews.flatMap((view) => view.scenario_conditions),
      );
      const nextWengineViews = await Promise.all(
        normalizedTeam.map((owner) => {
          const selection = wengineSource[owner];
          if (!selection?.id || (buildModesSource[owner] ?? "manual-panel") !== "equipment-build") {
            return Promise.resolve(null);
          }
          return jsonRequest<WEngineEditorView>("/api/v1/wengines/preview", {
            method: "POST",
            body: JSON.stringify({
              wengine_id: selection.id,
              equipped_character_id: owner,
              team_character_ids: normalizedTeam,
              level: selection.level,
              refinement: selection.refinement,
              condition_context: authoritativeConditionContext,
            }),
            signal: abortController.signal,
          });
        }),
      );
      const nextDriveDiscViews = await Promise.all(
        normalizedTeam.map((owner) => {
          if ((buildModesSource[owner] ?? "manual-panel") !== "equipment-build") {
            return Promise.resolve(null);
          }
          return jsonRequest<DriveDiscEditorView>("/api/v1/drive-discs/preview", {
            method: "POST",
            body: JSON.stringify({
              equipped_character_id: owner,
              team_character_ids: normalizedTeam,
              discs: driveDiscSource[owner] ?? [],
              condition_context: authoritativeConditionContext,
            }),
            signal: abortController.signal,
          });
        }),
      );
      const nextBuildPreviews = await Promise.all(
        normalizedTeam.map((owner) => {
          if ((buildModesSource[owner] ?? "manual-panel") !== "equipment-build") {
            return Promise.resolve(null);
          }
          const selection = wengineSource[owner];
          return jsonRequest<BuildPreview>("/api/v1/builds/preview", {
            method: "POST",
            body: JSON.stringify({
              character_id: owner,
              level: characterLevelsSource[owner] ?? 60,
              ...(selection?.id ? {
                wengine_id: selection.id,
                wengine_level: selection.level,
                wengine_refinement: selection.refinement,
              } : {}),
              drive_discs: driveDiscSource[owner] ?? [],
            }),
            signal: abortController.signal,
          });
        }),
      );
      if (generation !== editorGeneration.current) return;
      setEditorViews(Object.fromEntries(normalizedTeam.map((owner, index) => [owner, nextEditorViews[index] ?? null])));
      setWengineViews(Object.fromEntries(normalizedTeam.map((owner, index) => [owner, nextWengineViews[index] ?? null])));
      setDriveDiscViews(Object.fromEntries(normalizedTeam.map((owner, index) => [owner, nextDriveDiscViews[index] ?? null])));
      setBuildPreviews(Object.fromEntries(normalizedTeam.map((owner, index) => [owner, nextBuildPreviews[index] ?? null])));
      const operatorView = nextEditorViews[normalizedTeam.indexOf(normalizedOperator)];
      setMoveEntryId((current) => operatorView?.moves.some((move) => move.entry_id === current) ? current : (operatorView?.moves[0]?.entry_id || ""));
      const nextConfigs = { ...configSource };
      nextEditorViews.forEach(({ character_id: owner, compile_config_fields: fields }) => {
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
              ...nextEditorViews.flatMap((view) => view.scenario_conditions),
              ...nextWengineViews.flatMap((view) => view?.scenario_conditions ?? []),
              ...nextDriveDiscViews.flatMap((view) => view?.scenario_conditions ?? []),
            ],
            parameters: [
              ...nextEditorViews.flatMap((view) => view.scenario_parameters),
              ...nextWengineViews.flatMap((view) => view?.scenario_parameters ?? []),
            ],
            rules: [
              ...nextEditorViews.flatMap((view) => view.rule_items),
              ...nextWengineViews.flatMap((view) => view?.rule_items ?? []),
              ...nextDriveDiscViews.flatMap((view) => view?.rule_items ?? []),
            ],
            triggers: [
              ...nextEditorViews.flatMap((view) => view.scenario_trigger_inputs),
              ...nextWengineViews.flatMap((view) => view?.scenario_trigger_inputs ?? []),
              ...nextDriveDiscViews.flatMap((view) => view?.scenario_trigger_inputs ?? []),
            ],
          },
        normalizedTeam,
      );
      commitConditionValues(reconciled.conditionValues);
      setParameterValues(reconciled.parameterValues);
      setEnabledRules(reconciled.enabledRules);
      setDisabledRules(reconciled.disabledRules);
      setTriggerActors(reconciled.triggerActors);
      setStacks(reconciled.stacks);
    } catch (error) {
      if ((error as Error).name === "AbortError" || generation !== editorGeneration.current) return;
      setDiagnostics([(error as Error).message]);
    } finally {
      if (generation === editorGeneration.current) setLoading(false);
    }
  };

  const applyTeamAction = (action: Exclude<TeamAction, { type: "select-primary" | "select-support" }>) => {
    const next = teamReducer(teamState, action);
    if (!("teamCharacterIds" in next) || next === teamState) return;
    dispatchTeam(action);
    setCalculation(null);
    void loadEditors(
      next.teamCharacterIds,
      next.currentOperatorId,
      configs,
      conditionValuesRef.current,
      {},
      wengineSelections,
      buildModes,
      driveDiscSelections,
      characterLevels,
    );
  };

  const openCharacterLibrary = (slotIndex: number) => {
    setLibrarySlot(slotIndex);
    setLibraryQuery("");
    setLibrarySpecialty("");
    setLibraryElement("");
    setLibraryOpen(true);
  };

  const closeCharacterLibrary = () => {
    setLibraryOpen(false);
    setLibrarySlot(null);
  };

  const selectLibraryCharacter = (characterId: string) => {
    if (librarySlot === null) return;
    if (librarySlot < teamIds.length) {
      applyTeamAction({ type: "replace-character", slotIndex: librarySlot, characterId });
    } else {
      applyTeamAction({ type: "add-character", characterId });
    }
    closeCharacterLibrary();
  };

  const filteredLibraryCharacters = useMemo(() => {
    return filterCharacterCatalog(characters, {
      query: libraryQuery,
      specialty: librarySpecialty,
      element: libraryElement,
    });
  }, [characters, libraryElement, libraryQuery, librarySpecialty]);

  useEffect(() => {
    Promise.all([
      jsonRequest<Character[]>("/api/v1/characters"),
      jsonRequest<WEngine[]>("/api/v1/wengines"),
      jsonRequest<DriveDiscSet[]>("/api/v1/drive-discs"),
    ])
      .then(([loadedCharacters, loadedWengines, loadedDriveDiscSets]) => {
        setCharacters(loadedCharacters);
        setWengines(loadedWengines);
        setDriveDiscSets(loadedDriveDiscSets);
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
        return loadEditors(teamIds, currentOperatorId, configs, conditionValuesRef.current, {}, nextSelections);
      })
      .catch((error: Error) => setDiagnostics([error.message]));
    // The catalog is the only initial network request; editor loading follows it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateConfig = (characterId: string, key: string, value: unknown) => {
    const nextConfigs = { ...configs, [characterId]: { ...configs[characterId], [key]: value } };
    setConfigs(nextConfigs);
    void loadEditors(teamIds, currentOperatorId, nextConfigs, conditionValuesRef.current, {}, wengineSelections);
  };

  const updateBuildStat = (characterId: string, key: "attack" | "crit_rate" | "crit_damage" | "penetration_rate" | "penetration_flat", value: number) => {
    setBuildStats((current) => ({ ...current, [characterId]: { ...current[characterId], [key]: value } }));
  };

  const updateCharacterLevel = (characterId: string, value: number) => {
    const nextLevels = { ...characterLevels, [characterId]: value };
    setCharacterLevels(nextLevels);
    if ((buildModes[characterId] ?? "manual-panel") === "equipment-build") {
      void loadEditors(
        teamIds,
        currentOperatorId,
        configs,
        conditionValuesRef.current,
        {},
        wengineSelections,
        buildModes,
        driveDiscSelections,
        nextLevels,
      );
    }
  };

  const updateElementBonus = (characterId: string, element: string, value: number) => {
    setBuildStats((current) => ({ ...current, [characterId]: { ...current[characterId], element_damage_bonus: { ...current[characterId]?.element_damage_bonus, [element]: value } } }));
  };

  const updateConfigField = (owner: string, field: CompileField, value: boolean | number | string) => {
    if (field.field_id.startsWith("skill_level:")) {
      const group = field.field_id.slice("skill_level:".length);
      const nextConfigs = { ...configs, [owner]: { ...configs[owner], skill_levels: { ...((configs[owner]?.skill_levels as Record<string, number> | undefined) ?? {}), [group]: Number(value) } } };
      setConfigs(nextConfigs);
      void loadEditors(teamIds, currentOperatorId, nextConfigs, conditionValuesRef.current, {}, wengineSelections);
      return;
    }
    updateConfig(owner, field.field_id, value);
  };

  const selectVariant = (entryId: string, variantIndex: number) => {
    const move = operatorMoves.find((item) => item.entry_id === entryId);
    if (!move) return;
    const next = selectMoveVariantConditions(
      conditionValuesRef.current,
      move,
      variantIndex,
      allConditions,
    );
    setMoveEntryId(entryId);
    setCalculation(null);
    commitConditionValues(next);
    void loadEditors(teamIds, currentOperatorId, configs, next, { conditionValues: next }, wengineSelections);
  };

  const selectMoveOption = (optionKey: string) => {
    const option = moveOptions.find((item) => item.optionKey === optionKey);
    if (!option) return;
    if (option.variantIndex !== null) {
      selectVariant(option.entryId, option.variantIndex);
      return;
    }
    setMoveEntryId(option.entryId);
    setCalculation(null);
  };

  const updateWengineSelection = (
    owner: string,
    selection: { id: string; level: number; refinement: number },
  ) => {
    const nextSelections = { ...wengineSelections, [owner]: selection };
    setWengineSelections(nextSelections);
    void loadEditors(teamIds, currentOperatorId, configs, conditionValuesRef.current, {}, nextSelections);
  };

  const exportEquipmentConfig = (owner: string) => {
    const selection = wengineSelections[owner];
    const config = createEquipmentConfig(
      owner,
      selection?.id
        ? { id: selection.id, level: selection.level, refinement: selection.refinement }
        : null,
      driveDiscSelections[owner] ?? [],
    );
    const blob = new Blob([serializeEquipmentConfig(config)], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const safeCharacterId = owner.replace(/[^a-z0-9._-]+/gi, "_");
    anchor.href = url;
    anchor.download = `zzz-equipment-${safeCharacterId}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    setEquipmentFeedback((current) => ({
      ...current,
      [owner]: { kind: "success", message: "配置已导出为 JSON，可随时重新导入。" },
    }));
  };

  const importEquipmentConfig = async (owner: string, file: File) => {
    try {
      const result = parseEquipmentConfig(
        await file.text(),
        owner,
        {
          wengines,
          driveDiscSets,
          slotSchemas: driveDiscViews[owner]?.slot_schemas,
          substatOptions: driveDiscViews[owner]?.substat_options,
          characterSpecialty: characters.find((item) => item.character_id === owner)?.specialty,
        },
      );
      if (!result.ok) {
        setEquipmentFeedback((current) => ({
          ...current,
          [owner]: { kind: "error", message: `导入失败：${result.message}` },
        }));
        setDiagnostics([`装备配置导入失败：${result.message}`]);
        return;
      }

      const nextWengineSelections = { ...wengineSelections };
      if (result.config.wengine) {
        nextWengineSelections[owner] = { ...result.config.wengine };
      } else {
        delete nextWengineSelections[owner];
      }
      const nextDriveDiscSelections = {
        ...driveDiscSelections,
        [owner]: result.config.drive_discs,
      };
      const nextBuildModes = { ...buildModes, [owner]: "equipment-build" as const };
      const nextCharacterLevels = { ...characterLevels, [owner]: 60 };

      // Commit all imported values together, then issue one authoritative
      // editor/build refresh using the complete next state.
      setWengineSelections(nextWengineSelections);
      setDriveDiscSelections(nextDriveDiscSelections);
      setBuildModes(nextBuildModes);
      setCharacterLevels(nextCharacterLevels);
      setEquipmentFeedback((current) => ({
        ...current,
        [owner]: { kind: "success", message: `已导入 ${result.config.drive_discs.length} 个驱动盘${result.config.wengine ? "与 1 把音擎" : ""}。` },
      }));
      setDiagnostics([]);
      void loadEditors(
        teamIds,
        currentOperatorId,
        configs,
        conditionValuesRef.current,
        {},
        nextWengineSelections,
        nextBuildModes,
        nextDriveDiscSelections,
        nextCharacterLevels,
      );
    } catch (error) {
      setEquipmentFeedback((current) => ({
        ...current,
        [owner]: { kind: "error", message: `导入失败：${(error as Error).message}` },
      }));
      setDiagnostics([`装备配置导入失败：${(error as Error).message}`]);
    }
  };

  const updateBuildMode = (owner: string, mode: "manual-panel" | "equipment-build") => {
    const nextModes = { ...buildModes, [owner]: mode };
    const nextLevels = mode === "equipment-build"
      ? { ...characterLevels, [owner]: 60 }
      : characterLevels;
    setBuildModes(nextModes);
    setCharacterLevels(nextLevels);
    void loadEditors(
      teamIds,
      currentOperatorId,
      configs,
      conditionValuesRef.current,
      {},
      wengineSelections,
      nextModes,
      driveDiscSelections,
      nextLevels,
    );
  };

  const updateDriveDisc = (owner: string, slot: number, nextDisc: DriveDiscConfig | null) => {
    const current = driveDiscSelections[owner] ?? [];
    const nextForOwner = nextDisc
      ? [...current.filter((item) => item.slot !== slot), nextDisc].sort((a, b) => a.slot - b.slot)
      : current.filter((item) => item.slot !== slot);
    const nextSelections = { ...driveDiscSelections, [owner]: nextForOwner };
    setDriveDiscSelections(nextSelections);
    void loadEditors(
      teamIds,
      currentOperatorId,
      configs,
      conditionValuesRef.current,
      {},
      wengineSelections,
      buildModes,
      nextSelections,
    );
  };

  const selectDriveDiscSet = (owner: string, slot: number, setId: string) => {
    if (!setId) {
      updateDriveDisc(owner, slot, null);
      return;
    }
    const schema = driveDiscViews[owner]?.slot_schemas.find((item) => item.slot === slot);
    if (!schema) return;
    const current = driveDiscSelections[owner]?.find((item) => item.slot === slot);
    updateDriveDisc(
      owner,
      slot,
      selectDriveDiscSetValue(
        current,
        slot,
        setId,
        schema,
      ),
    );
  };

  const updateDriveDiscMain = (owner: string, slot: number, mainStat: string) => {
    const current = driveDiscSelections[owner]?.find((item) => item.slot === slot);
    if (!current) return;
    updateDriveDisc(
      owner,
      slot,
      updateDriveDiscMainValue(
        current,
        mainStat || null,
      ),
    );
  };

  const updateDriveDiscSubstat = (owner: string, slot: number, index: number, next: DriveDiscSubstat) => {
    const current = driveDiscSelections[owner]?.find((item) => item.slot === slot);
    if (!current) return;
    updateDriveDisc(owner, slot, replaceDriveDiscSubstat(current, index, next));
  };

  const updateDriveDiscSubstatRoll = (owner: string, slot: number, index: number, delta: number) => {
    const current = driveDiscSelections[owner]?.find((item) => item.slot === slot);
    if (!current) return;
    updateDriveDisc(owner, slot, updateDriveDiscSubstatRollCount(current, index, delta));
  };

  const addDriveDiscSubstatRow = (owner: string, slot: number, stat: string) => {
    const current = driveDiscSelections[owner]?.find((item) => item.slot === slot);
    if (!current || !stat) return;
    updateDriveDisc(owner, slot, addDriveDiscSubstat(current, stat));
  };

  const removeDriveDiscSubstatRow = (owner: string, slot: number, index: number) => {
    const current = driveDiscSelections[owner]?.find((item) => item.slot === slot);
    if (!current) return;
    updateDriveDisc(owner, slot, removeDriveDiscSubstat(current, index));
  };

  const buildPayloads = () => Object.fromEntries(teamIds.map((id) => {
    const mode = buildModes[id] ?? "manual-panel";
    const selection = wengineSelections[id];
    if (mode === "equipment-build") {
      return [id, {
        level: characterLevels[id] ?? 60,
        build_mode: mode,
        ...(selection?.id ? { wengine_id: selection.id, wengine_level: selection.level, wengine_refinement: selection.refinement } : {}),
        drive_discs: driveDiscSelections[id] ?? [],
      }];
    }
    const stats = buildStats[id] ?? { ...DEFAULT_STATS, element_damage_bonus: { ...DEFAULT_STATS.element_damage_bonus } };
    return [id, { level: characterLevels[id] ?? 60, out_of_combat_stats: { ...stats, element_damage_bonus: { ...stats.element_damage_bonus } } }];
  }));

  const calculate = async () => {
    if (!moveEntryId || moveSelectionIssue) {
      if (moveSelectionIssue) setDiagnostics([moveSelectionIssue]);
      return;
    }
    setCalculating(true);
    setDiagnostics([]);
    try {
      const scenarioConditionValues = conditionValuesForViews(
        conditionValuesRef.current,
        allConditions,
      );
      const result = await jsonRequest<CalculationView>("/api/v1/moves/calculate", {
        method: "POST",
        body: JSON.stringify({
          primary_character_id: requestTeam.primaryCharacterId,
          current_operator: currentOperatorId,
          supporting_character_ids: supportingIds,
          // The team state keeps a stable slot order for the library. The
          // calculation transport puts the current operator first because
          // Direct UI defines primary as both operator and move owner.
          team_character_ids: requestTeam.teamCharacterIds,
          move_entry_id: moveEntryId,
          compile_configs: Object.fromEntries(teamIds.map((id) => [id, configs[id] ?? {}])),
          condition_values: scenarioConditionValues,
          parameter_values: parameterValues,
          character_builds: buildPayloads(),
          enemy: { enemy_id: "enemy:ui", level: enemyLevel, initial_defense: enemyDefense, damage_resistance: { physical: enemyPhysicalResistance, ether: enemyEtherResistance, electric: enemyElectricResistance }, damage_reduction: enemyDamageReduction, stun_vulnerability_bonus: stunVulnerability, is_stunned: enemyIsStunned },
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

  const selectedCurrent = characters.find((item) => item.character_id === currentOperatorId);
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
          <div className="section-heading"><div><p className="eyebrow">ROSTER · TEAM BUILDER</p><h2>队伍与当前角色</h2><p className="roster-hint">从角色库选择 1–3 名角色；槽位顺序会保留，当前操作角色负责招式结算。</p></div><span className="counter">{teamIds.length}/3</span></div>
          <div className="team-slot-grid">
            {Array.from({ length: 3 }, (_, slotIndex) => {
              const id = teamIds[slotIndex];
              const character = characters.find((item) => item.character_id === id);
              if (!id || !character) {
                return <button className="team-slot team-slot-empty" key={`empty-${slotIndex}`} onClick={() => openCharacterLibrary(slotIndex)} type="button">
                  <span className="team-slot-plus" aria-hidden="true">＋</span>
                  <strong>添加角色</strong>
                  <small>第 {slotIndex + 1} 个队伍槽位</small>
                </button>;
              }
              const isOperator = id === currentOperatorId;
              return <article className={`team-slot team-slot-filled ${isOperator ? "team-slot-operator" : ""}`} key={id}>
                <div className="team-slot-art">
                  <img alt={character.display_name} src={character.image_path} style={{ objectPosition: character.image_object_position }} />
                  <span className="rarity">{character.rarity}</span>
                  {isOperator && <span className="operator-badge">当前操作</span>}
                </div>
                <div className="team-slot-copy"><strong>{character.display_name}</strong><small>{specialtyLabel(character.specialty)} · {elementLabel(character.element)}</small></div>
                <div className="team-slot-actions">
                  <button className="secondary-button" disabled={isOperator} onClick={() => applyTeamAction({ type: "set-current-operator", characterId: id })} type="button">设为当前操作</button>
                  <button className="secondary-button" onClick={() => openCharacterLibrary(slotIndex)} type="button">替换</button>
                  <button className="secondary-button team-slot-remove" disabled={teamIds.length <= 1} onClick={() => applyTeamAction({ type: "remove-character", characterId: id })} type="button">移除</button>
                </div>
              </article>;
            })}
          </div>
          {selectedCurrent && <div className="selection-summary"><span className="eyebrow">CURRENT OPERATOR</span><strong>{selectedCurrent.display_name}</strong><span className="muted">{selectedCurrent.character_id} · {supportingIds.length} 名支援角色</span></div>}
          <LivePanel
            teamIds={teamIds}
            characters={characters}
            previews={buildPreviews}
            manualStats={buildStats}
            buildModes={buildModes}
            loading={loading}
          />
        </section>

        {libraryOpen && <div className="library-overlay" role="presentation" onMouseDown={(event) => { if (event.currentTarget === event.target) closeCharacterLibrary(); }}>
          <section className="character-library" role="dialog" aria-modal="true" aria-labelledby="character-library-title">
            <header className="character-library-header">
              <div><p className="eyebrow">CHARACTER LIBRARY</p><h2 id="character-library-title">角色库</h2><p className="muted">选择角色加入第 {(librarySlot ?? 0) + 1} 个队伍槽位；已在队伍中的角色不可重复选择。</p></div>
              <button className="icon-button library-close" aria-label="关闭角色库" onClick={closeCharacterLibrary} type="button">×</button>
            </header>
            <div className="character-library-filters">
              <label><span>搜索角色</span><input value={libraryQuery} onChange={(event) => setLibraryQuery(event.target.value)} placeholder="名称、职业或属性" /></label>
              <label><span>职业</span><select value={librarySpecialty} onChange={(event) => setLibrarySpecialty(event.target.value)}><option value="">全部职业</option>{Array.from(new Set(characters.map((item) => item.specialty))).map((specialty) => <option key={specialty} value={specialty}>{specialtyLabel(specialty)}</option>)}</select></label>
              <label><span>属性</span><select value={libraryElement} onChange={(event) => setLibraryElement(event.target.value)}><option value="">全部属性</option>{Array.from(new Set(characters.map((item) => item.element))).map((element) => <option key={element} value={element}>{elementLabel(element)}</option>)}</select></label>
            </div>
            <div className="library-results" aria-live="polite">
              {filteredLibraryCharacters.map((character) => {
                const alreadySelected = !isCharacterSelectable(character.character_id, teamIds);
                return <button className={`library-character ${alreadySelected ? "library-character-selected" : ""}`} disabled={alreadySelected} key={character.character_id} onClick={() => selectLibraryCharacter(character.character_id)} type="button">
                  <img alt="" src={character.image_path} style={{ objectPosition: character.image_object_position }} />
                  <span className="library-character-copy"><strong>{character.display_name}</strong><small>{specialtyLabel(character.specialty)} · {elementLabel(character.element)}</small></span>
                  <span className="rarity">{character.rarity}</span>
                  {alreadySelected && <span className="library-selected-mark">队伍中</span>}
                </button>;
              })}
              {filteredLibraryCharacters.length === 0 && <div className="library-empty">没有符合筛选条件的角色。</div>}
            </div>
          </section>
        </div>}

        <section className="glass-card build-panel">
          <div className="section-heading build-panel-heading"><div><p className="eyebrow">BUILD INPUT</p><h2>角色装备配置</h2></div><span className="muted">每个角色独立保存</span></div>
          <div className="build-character-fields">
            {teamIds.map((id, teamIndex) => {
              const equipmentMode = (buildModes[id] ?? "manual-panel") === "equipment-build";
              const driveView = driveDiscViews[id];
              const selectedDiscs = driveDiscSelections[id] ?? [];
              const preview = buildPreviews[id];
              const basePanel = preview?.base_stats;
              const character = characters.find((item) => item.character_id === id);
              const selectedElement = character?.element ?? "physical";
              const feedback = equipmentFeedback[id];
              const roleLabel = teamIndex === 0 ? "主控角色" : "支援角色";
              return (
                <article className={`build-character ${equipmentMode ? "build-character-equipment" : "build-character-manual"}`} key={id}>
                  <header className="build-character-heading">
                    <div className="build-character-identity">
                      {character ? <img alt="" src={character.image_path} style={{ objectPosition: character.image_object_position }} /> : <span className="build-character-avatar">?</span>}
                      <div>
                        <span className="build-character-role">{roleLabel}</span>
                        <strong>{character?.display_name ?? id}</strong>
                        <small>{character ? `${character.specialty} · ${character.element}` : id}</small>
                      </div>
                    </div>
                    <div className="equipment-tools">
                      <span className="equipment-schema-note">JSON · schema v1</span>
                      <button className="toolbar-button" type="button" onClick={() => equipmentImportInputRefs.current[id]?.click()}>
                        <span aria-hidden="true">↑</span> 导入配置
                      </button>
                      <button className="toolbar-button" type="button" onClick={() => exportEquipmentConfig(id)}>
                        <span aria-hidden="true">↓</span> 导出配置
                      </button>
                      <input
                        ref={(element) => { equipmentImportInputRefs.current[id] = element; }}
                        className="sr-only"
                        type="file"
                        accept="application/json,.json"
                        aria-label={`${character?.display_name ?? id}装备配置文件`}
                        onChange={(event) => {
                          const file = event.currentTarget.files?.[0];
                          event.currentTarget.value = "";
                          if (file) void importEquipmentConfig(id, file);
                        }}
                      />
                    </div>
                  </header>
                  <div className="equipment-schema-copy">导入或导出当前角色的音擎与 1–6 号位驱动盘；文件会校验角色、槽位、套装和词条。</div>
                  {feedback && <p className={`equipment-feedback ${feedback.kind}`}>{feedback.kind === "success" ? "✓" : "!"} {feedback.message}</p>}

                  <div className="build-mode-strip">
                    <label className="select-field"><span>面板模式</span><select value={buildModes[id] ?? "manual-panel"} onChange={(event) => updateBuildMode(id, event.target.value as "manual-panel" | "equipment-build")}><option value="manual-panel">手工局外面板</option><option value="equipment-build">装备配置</option></select></label>
                    <NumberField
                      label="角色等级"
                      value={characterLevels[id] ?? 60}
                      integer
                      min={equipmentMode ? 60 : 1}
                      max={60}
                      unit="级"
                      helper={equipmentMode ? "装备构筑固定为 60 级" : "可编辑范围 1–60"}
                      readOnly={equipmentMode}
                      onCommit={(value) => updateCharacterLevel(id, value)}
                    />
                  </div>

                  <div className="build-stats-section">
                    <div className="subsection-heading"><div><span className="eyebrow">PANEL SNAPSHOT</span><h3>{equipmentMode ? "装备后面板预览" : "手工局外面板"}</h3></div><span className="subsection-badge">{equipmentMode ? "只读预览" : "可编辑"}</span></div>
                    <div className="number-field-grid">
                      <NumberField label={equipmentMode ? "无装备基础攻击力" : "攻击力"} value={equipmentMode ? numericPreviewStat(basePanel?.attack) : (buildStats[id]?.attack ?? 1000)} min={0} helper={equipmentMode ? "来自角色基础属性" : "内核值 · 直接攻击力"} readOnly={equipmentMode} displayValue={equipmentMode ? formatPanelDisplay(basePanel?.attack) : undefined} onCommit={(value) => updateBuildStat(id, "attack", value)} />
                      <NumberField label="暴击率" value={equipmentMode ? numericPreviewStat(basePanel?.crit_rate) : (buildStats[id]?.crit_rate ?? 0.5)} min={0} unit="%" displayAsPercent={!equipmentMode} helper={equipmentMode ? "装备解析结果" : "底层 ratio 值按百分比编辑"} readOnly={equipmentMode} displayValue={equipmentMode ? previewRatioText(basePanel?.crit_rate) || "—" : undefined} onCommit={(value) => updateBuildStat(id, "crit_rate", value)} />
                      <NumberField label="暴击伤害" value={equipmentMode ? numericPreviewStat(basePanel?.crit_damage) : (buildStats[id]?.crit_damage ?? 0.5)} min={0} unit="%" displayAsPercent={!equipmentMode} helper={equipmentMode ? "装备解析结果" : "底层 ratio 值按百分比编辑"} readOnly={equipmentMode} displayValue={equipmentMode ? previewRatioText(basePanel?.crit_damage) || "—" : undefined} onCommit={(value) => updateBuildStat(id, "crit_damage", value)} />
                      <NumberField label="穿透率" value={equipmentMode ? numericPreviewStat(basePanel?.penetration_rate) : (buildStats[id]?.penetration_rate ?? 0)} min={0} unit="%" displayAsPercent={!equipmentMode} helper={equipmentMode ? "装备解析结果" : "底层 ratio 值按百分比编辑"} readOnly={equipmentMode} displayValue={equipmentMode ? previewRatioText(basePanel?.penetration_rate) || "—" : undefined} onCommit={(value) => updateBuildStat(id, "penetration_rate", value)} />
                      <NumberField label="穿透值" value={equipmentMode ? numericPreviewStat(basePanel?.penetration_flat) : (buildStats[id]?.penetration_flat ?? 0)} min={0} helper={equipmentMode ? "装备解析结果" : "内核值 · 固定数值"} readOnly={equipmentMode} displayValue={equipmentMode ? formatPanelDisplay(basePanel?.penetration_flat) : undefined} onCommit={(value) => updateBuildStat(id, "penetration_flat", value)} />
                      <NumberField label="物理伤害加成" value={equipmentMode ? numericPreviewStat((basePanel?.element_damage_bonus as Record<string, number | null> | undefined)?.physical) : (buildStats[id]?.element_damage_bonus.physical ?? 0)} min={0} unit="%" displayAsPercent={!equipmentMode} helper={equipmentMode ? "装备解析结果" : "底层 ratio 值按百分比编辑"} readOnly={equipmentMode} displayValue={equipmentMode ? previewElementRatioText(basePanel?.element_damage_bonus, "physical") || "—" : undefined} onCommit={(value) => updateElementBonus(id, "physical", value)} />
                      <NumberField label="以太伤害加成" value={equipmentMode ? numericPreviewStat((basePanel?.element_damage_bonus as Record<string, number | null> | undefined)?.ether) : (buildStats[id]?.element_damage_bonus.ether ?? 0)} min={0} unit="%" displayAsPercent={!equipmentMode} helper={equipmentMode ? "装备解析结果" : "底层 ratio 值按百分比编辑"} readOnly={equipmentMode} displayValue={equipmentMode ? previewElementRatioText(basePanel?.element_damage_bonus, "ether") || "—" : undefined} onCommit={(value) => updateElementBonus(id, "ether", value)} />
                      {!(["physical", "ether"] as string[]).includes(selectedElement) && <NumberField label={`${elementLabel(selectedElement)}伤害加成`} value={equipmentMode ? numericPreviewStat((basePanel?.element_damage_bonus as Record<string, number | null> | undefined)?.[selectedElement]) : (buildStats[id]?.element_damage_bonus[selectedElement as keyof typeof DEFAULT_STATS.element_damage_bonus] ?? 0)} min={0} unit="%" displayAsPercent={!equipmentMode} helper={equipmentMode ? "装备解析结果" : "底层 ratio 值按百分比编辑"} readOnly={equipmentMode} displayValue={equipmentMode ? previewElementRatioText(basePanel?.element_damage_bonus, selectedElement) || "—" : undefined} onCommit={(value) => updateElementBonus(id, selectedElement, value)} />}
                    </div>
                  </div>

                  {equipmentMode && <div className="equipment-build-details">
                    <div className="subsection-heading"><div><span className="eyebrow">W-ENGINE</span><h3>音擎</h3></div><span className="subsection-badge">专精匹配</span></div>
                    <div className="wengine-fields">
                      <label className="select-field wengine-select"><span>音擎</span><select value={wengineSelections[id]?.id ?? ""} onChange={(event) => updateWengineSelection(id, { ...(wengineSelections[id] ?? { level: 60, refinement: 1 }), id: event.target.value })}><option value="">无</option>{wengines.filter((item) => item.specialty === character?.specialty).map((item) => <option key={item.wengine_id} value={item.wengine_id}>{item.display_name}</option>)}</select></label>
                      <NumberField label="音擎等级" value={wengineSelections[id]?.level ?? 60} integer min={60} max={60} unit="级" helper="当前构筑等级上限" readOnly />
                      <NumberField label="精炼" value={wengineSelections[id]?.refinement ?? 1} integer min={1} max={5} unit="阶" helper="范围 1–5 阶" onCommit={(value) => updateWengineSelection(id, { ...(wengineSelections[id] ?? { id: "", level: 60 }), refinement: value })} />
                    </div>
                  </div>}

                  {equipmentMode && <div className="drive-disc-section-wrap">
                    <div className="subsection-heading drive-disc-area-heading"><div><span className="eyebrow">DRIVE DISCS</span><h3>驱动盘</h3></div><span className="subsection-badge">6 个槽位</span></div>
                    <div className="drive-disc-grid">
                      {(driveView?.slot_schemas ?? []).map((schema) => {
                        const disc = selectedDiscs.find((item) => item.slot === schema.slot);
                        const discPreview = preview?.drive_discs.find((item) => item.slot === schema.slot);
                        return <DriveDiscCard
                          key={`${id}-disc-${schema.slot}`}
                          schema={schema}
                          disc={disc}
                          preview={discPreview}
                          driveDiscSets={driveDiscSets}
                          substatOptions={driveView?.substat_options ?? []}
                          diagnostics={driveView?.diagnostics ?? []}
                          onSelectSet={(setId) => selectDriveDiscSet(id, schema.slot, setId)}
                          onUpdateMain={(mainStat) => updateDriveDiscMain(id, schema.slot, mainStat)}
                          onUpdateSubstat={(index, next) => updateDriveDiscSubstat(id, schema.slot, index, next)}
                          onUpdateRoll={(index, delta) => updateDriveDiscSubstatRoll(id, schema.slot, index, delta)}
                          onRemoveSubstat={(index) => removeDriveDiscSubstatRow(id, schema.slot, index)}
                          onAddSubstat={(stat) => addDriveDiscSubstatRow(id, schema.slot, stat)}
                          formatValue={formatDriveValue}
                        />;
                      })}
                    </div>
                    {driveView && driveView.set_counts.length > 0 && <div className="drive-set-summary"><span className="drive-set-summary-label">套装统计</span>{driveView.set_counts.map((item) => <span key={item.set_id}>{driveDiscSets.find((set) => set.set_id === item.set_id)?.display_name ?? item.set_id} ×{item.count}</span>)}</div>}
                  </div>}
                </article>
              );
            })}
          </div>
          {calculation && calculation.build_provenance.length > 0 && <div className="trace-list"><p className="eyebrow">BUILD PROVENANCE</p>{calculation.build_provenance.map((trace) => <div className="trace-row" key={trace.contribution_id}><span>{trace.character_id}</span><strong>{trace.value === null ? "?" : `+${formatNumber(trace.value)}`}</strong><small>{trace.source_label} · {trace.stat} · {trace.layer}</small></div>)}</div>}
          <div className="section-heading compact"><div><p className="eyebrow">TARGET</p><h2>敌人</h2></div></div>
          <div className="target-fields">
            <NumberField label="等级" value={enemyLevel} integer min={1} max={80} unit="级" helper="敌人等级 1–80" onCommit={setEnemyLevel} />
            <NumberField label="防御力" value={enemyDefense} min={0} helper="敌方初始防御力" onCommit={setEnemyDefense} />
            <NumberField label="物理抗性" value={enemyPhysicalResistance} unit="%" displayAsPercent helper="底层 ratio 值按百分比编辑" onCommit={setEnemyPhysicalResistance} />
            <NumberField label="以太抗性" value={enemyEtherResistance} unit="%" displayAsPercent helper="底层 ratio 值按百分比编辑" onCommit={setEnemyEtherResistance} />
            <NumberField label="电抗性" value={enemyElectricResistance} unit="%" displayAsPercent helper="底层 ratio 值按百分比编辑" onCommit={setEnemyElectricResistance} />
            <NumberField label="失衡易伤" value={stunVulnerability} unit="×" helper="伤害倍率，例如 1.5×" onCommit={setStunVulnerability} />
            <NumberField label="减易伤" value={enemyDamageReduction} unit="%" displayAsPercent helper="底层 ratio 值按百分比编辑" onCommit={setEnemyDamageReduction} />
            <label className="check-field"><span>当前处于失衡</span><input type="checkbox" checked={enemyIsStunned} onChange={(event) => setEnemyIsStunned(event.target.checked)} /></label>
          </div>
        </section>
      </section>

      <section className="workspace-grid">
        <section className="glass-card controls-panel">
          <div className="section-heading"><div><p className="eyebrow">SCENARIO</p><h2>场景与规则</h2></div>{loading && <span className="muted">读取中…</span>}</div>
          <div className="config-field-grid">{allConfigFields.map(({ owner, field }) => {
            const fieldValue = configFieldValue(owner, field);
            const unit = field.field_id.includes("level") ? "级" : field.field_id.includes("stack") ? "层" : undefined;
            if (field.field_type === "boolean") {
              return <label className="check-field" key={`${owner}-${field.field_id}`}><span><strong>{field.label}</strong><small>{field.help_text ?? "编译期配置"}</small></span><input disabled={!field.editable} type="checkbox" checked={Boolean(fieldValue)} onChange={(event) => updateConfigField(owner, field, event.target.checked)} /></label>;
            }
            if (field.field_type === "select") {
              return <label className="select-field" key={`${owner}-${field.field_id}`}><span>{field.label}</span><select disabled={!field.editable} value={String(fieldValue)} onChange={(event) => updateConfigField(owner, field, Number(event.target.value))}>{field.options.map((option) => <option key={option} value={option}>{option}</option>)}</select></label>;
            }
            return <NumberField key={`${owner}-${field.field_id}`} label={field.label} value={Number(fieldValue)} integer min={field.minimum ?? undefined} max={field.maximum ?? undefined} unit={unit} helper={field.help_text ?? "整数配置"} disabled={!field.editable} onCommit={(value) => updateConfigField(owner, field, value)} />;
          })}</div>
          {visibleScenarioConditions.length > 0 && <div className="control-list"><div className="section-heading compact"><div><p className="eyebrow">CHARACTER STATES</p><h2>角色状态</h2><p className="control-section-hint">只显示可直接理解的独立状态；招式倍率在右侧招式下拉框中选择。</p></div></div>{visibleScenarioConditions.map((condition) => <label className="toggle-row" key={condition.condition_id}><span><strong>{condition.label}</strong><small>{condition.resolution} · 影响相关规则</small></span><input type="checkbox" checked={condition.value === true || conditionValues[condition.condition_id] === true} onChange={(event) => { const next = { ...conditionValuesRef.current, [condition.condition_id]: event.target.checked }; commitConditionValues(next); void loadEditors(teamIds, currentOperatorId, configs, next, { conditionValues: next }); }} /></label>)}</div>}
          {allParameters.length > 0 && <div className="parameter-list"><div className="section-heading compact"><div><p className="eyebrow">SCENARIO PARAMETERS</p><h2>次数与数值输入</h2></div></div><div className="parameter-field-grid">{allParameters.map((parameter) => { const currentValue = parameterValues[parameter.parameter_id] !== undefined ? parameterValues[parameter.parameter_id] : parameter.value; return <NumberField key={parameter.parameter_id} label={parameter.label} value={currentValue} integer min={parameter.minimum} max={parameter.maximum ?? undefined} unit={parameter.parameter_id.includes("count") || parameter.parameter_id.includes("repeat") ? "次" : undefined} helper={parameter.resolution} placeholder={currentValue === null ? "未指定" : undefined} onCommit={(value) => setParameterValues((current) => ({ ...current, [parameter.parameter_id]: value }))} />; })}</div></div>}
          <div className="rule-list">{allRules.map((rule) => <div className={`rule-row ${rule.availability !== "available" ? "disabled" : ""}`} key={rule.rule_id}><span><strong>{rule.label}</strong><small>{rule.source_label} · {rule.availability}</small></span><input disabled={!rule.toggleable} type="checkbox" checked={enabledRules.has(rule.rule_id)} onChange={(event) => { const checked = event.target.checked; setEnabledRules((current) => { const next = new Set(current); if (checked) next.add(rule.rule_id); else next.delete(rule.rule_id); return next; }); setDisabledRules((current) => { const next = new Set(current); if (checked) next.delete(rule.rule_id); else next.add(rule.rule_id); return next; }); }} />{rule.stack.minimum !== null && <NumberField className="stack-field" label="层数" unit="层" integer min={rule.stack.minimum} max={rule.stack.maximum ?? undefined} value={stacks[rule.rule_id] ?? rule.stack.default ?? rule.stack.minimum} helper={`范围 ${rule.stack.minimum}–${rule.stack.maximum ?? "∞"}`} onCommit={(value) => setStacks((current) => ({ ...current, [rule.rule_id]: value }))} />}</div>)}</div>
          {allTriggers.length > 0 && <><div className="section-heading compact"><div><p className="eyebrow">TRIGGER FACTS</p><h2>场景触发</h2><p className="control-section-hint">需要明确入场角色的 Effect 会在这里显示；留空时计算 trace 会标记为 blocked。</p></div></div><div className="trigger-field-grid">{allTriggers.map((trigger) => { const selectedActor = triggerActors[trigger.input_id]; return <label className={`trigger-field ${selectedActor ? "trigger-field-selected" : "trigger-field-missing"}`} key={trigger.input_id}><span>{trigger.label}</span><select value={selectedActor ?? ""} onChange={(event) => setTriggerActors((current) => { const next = { ...current }; if (event.target.value) next[trigger.input_id] = event.target.value; else delete next[trigger.input_id]; return next; })}><option value="">未指定</option>{trigger.actor_options.map((actor) => <option key={actor} value={actor}>{characters.find((item) => item.character_id === actor)?.display_name ?? actor}</option>)}</select><small>{selectedActor ? `已指定：${characters.find((item) => item.character_id === selectedActor)?.display_name ?? selectedActor}` : "⚠ 需要指定入场角色"}</small></label>; })}</div></>}
        </section>

        <section className="glass-card result-panel">
          <div className="section-heading"><div><p className="eyebrow">MOVE CALCULATION</p><h2>招式结算</h2></div><button className="primary-button" disabled={calculating || loading || !moveEntryId || Boolean(moveSelectionIssue)} onClick={calculate} type="button">{calculating ? "计算中…" : "计算"}</button></div>
          <label className="move-select">招式<select value={selectedMoveOption?.optionKey ?? ""} onChange={(event) => selectMoveOption(event.target.value)}><option value="" disabled>{moveSelectionIssue ?? "请选择招式"}</option>{moveOptions.map((option) => <option key={option.optionKey} value={option.optionKey}>{option.label}</option>)}</select></label>
          {moveSelectionIssue && <p className="control-section-hint">⚠ {moveSelectionIssue}；未发送计算请求。</p>}
          {calculation ? <div className="calculation-output"><div className="totals-grid">{(calculation.display_modes ?? ["non-crit", "expected", "full-crit"]).map((mode) => <div className="total-card" key={mode}><small>{mode}</small><strong>{formatNumber(calculation.totals[mode]?.value)}</strong><span className={calculation.totals[mode]?.complete ? "complete" : "incomplete"}>{calculation.totals[mode]?.complete ? "complete" : "partial"}</span></div>)}</div><div className="event-list">{calculation.events.map((event) => <article className="event-card" key={event.semantic_id}><div><strong>{event.label}</strong><small>{event.semantic_id} · ×{event.repeat_count}</small></div><div className="event-values">{(event.display_modes ?? ["non-crit", "expected", "full-crit"]).map((mode) => <span key={mode}><small>{mode} · {event.modes[mode]?.status}</small><b>{formatNumber(event.modes[mode]?.known_value)}</b></span>)}</div><details className="event-details"><summary>查看 breakdown</summary><div className="breakdown-list">{(event.modes.expected?.calculation_breakdown ?? []).map((node) => <div key={node.node}><span>{node.node}</span><b>{formatNumber(node.value)}</b><small>{node.read_rule}</small></div>)}</div>{event.common_application_trace && <EventTraceDetails trace={event.common_application_trace} rules={allRules} conditions={allConditions} conditionValues={conditionValuesRef.current} enabledRuleIds={enabledRules} formatNumber={formatNumber} isEquipmentSource={isEquipmentSource} />}{Object.entries(event.modes).flatMap(([mode, item]) => item.diagnostics.map((diagnostic, index) => <p className="inline-diagnostic" key={`${mode}-${index}`}>{mode}: {diagnostic.message}</p>))}</details></article>)}</div>{calculation.panel_traces.length > 0 && <div className="trace-list"><p className="eyebrow">PANEL PROVENANCE</p>{calculation.panel_traces.map((trace) => <div className="trace-row" key={`${trace.effect_id}-${trace.recipient_character_id}`}><span>{trace.recipient_character_id}</span><strong>+{formatNumber(trace.resolved_value)}</strong><small>{trace.source_label ?? trace.effect_id} · {trace.modifier_path}</small></div>)}</div>}{calculation.resolved_character_snapshots.length > 0 && <div className="trace-list"><p className="eyebrow">RESOLVED PANELS</p>{calculation.resolved_character_snapshots.map((snapshot) => <div className="snapshot-row" key={snapshot.character_id}><strong>{snapshot.character_id}</strong><span>攻击力 {formatNumber(typeof snapshot.stats.attack === "number" ? snapshot.stats.attack : null)}</span><span>暴击率 {formatNumber(typeof snapshot.stats.crit_rate === "number" ? snapshot.stats.crit_rate : null)}</span><span>属性加成 {formatElementBonuses(snapshot.stats.element_damage_bonus)}</span></div>)}</div>}{calculation.diagnostics.length > 0 && <div className="diagnostic-list">{calculation.diagnostics.map((item, index) => <div className="diagnostic" key={`${item.message}-${index}`}><strong>{item.blocking ? "BLOCKED" : "NOTE"}</strong><span>{item.message}</span></div>)}</div>}</div> : <div className="empty-state"><span className="empty-icon">◈</span><strong>选择招式后开始结算</strong><p className="muted">结果、派生事件和白盒说明将由计算内核返回。</p></div>}
        </section>
      </section>

      {diagnostics.length > 0 && <section className="diagnostics glass-card"><p className="eyebrow">DIAGNOSTICS</p>{diagnostics.map((message) => <div className="diagnostic" key={message}><strong>API</strong><span>{message}</span></div>)}</section>}
    </main>
  );
}

function formatNumber(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 2 }).format(value);
}

function elementLabel(element: string) {
  return ({ physical: "物理", ether: "以太", electric: "电", ice: "冰", fire: "火", wind: "风" } as Record<string, string>)[element] ?? element;
}

function specialtyLabel(specialty: string) {
  return ({ attack: "强攻", anomaly: "异常", support: "支援", stun: "击破" } as Record<string, string>)[specialty] ?? specialty;
}

type LivePanelProps = {
  teamIds: string[];
  characters: Character[];
  previews: Record<string, BuildPreview | null>;
  manualStats: Record<string, typeof DEFAULT_STATS>;
  buildModes: Record<string, "manual-panel" | "equipment-build">;
  loading: boolean;
};

const LIVE_PANEL_STATS: { key: string; label: string; ratio?: boolean }[] = [
  { key: "hp", label: "生命值" },
  { key: "attack", label: "攻击力" },
  { key: "defense", label: "防御力" },
  { key: "impact", label: "冲击力" },
  { key: "crit_rate", label: "暴击率", ratio: true },
  { key: "crit_damage", label: "暴击伤害", ratio: true },
  { key: "anomaly_proficiency", label: "异常精通" },
  { key: "anomaly_mastery", label: "异常掌控" },
  { key: "penetration_flat", label: "穿透值" },
  { key: "penetration_rate", label: "穿透率", ratio: true },
  { key: "energy_regen", label: "能量自动回复" },
];

function LivePanel({ teamIds, characters, previews, manualStats, buildModes, loading }: LivePanelProps) {
  return <section className="live-panel" aria-label="实时局外面板">
    <div className="section-heading compact live-panel-heading">
      <div><p className="eyebrow">LIVE OUT-OF-COMBAT PANEL</p><h2>实时局外面板</h2><p className="live-panel-subtitle">当前队伍的最终局外属性与来源</p></div>
      <span className={`live-update-status ${loading ? "updating" : "synced"}`} aria-live="polite">{loading ? "更新中…" : "已同步"}</span>
    </div>
    <div className="live-panel-list">
      {teamIds.map((id, teamIndex) => {
        const preview = buildModes[id] === "equipment-build" ? previews[id] : null;
        const manual = manualStats[id] ?? DEFAULT_STATS;
        const stats = preview?.out_of_combat_stats;
        const character = characters.find((item) => item.character_id === id);
        const status = preview
          ? (preview.complete ? "已解析" : "配置未完成")
          : buildModes[id] === "equipment-build" ? "等待解析" : "手工面板";
        const statusClass = preview?.complete === false ? "incomplete" : preview ? "complete" : "neutral";
        const readStat = (key: string, ratio = false) => {
          const value = preview ? numericPreviewStat(stats?.[key]) : manual[key as keyof typeof manual] as number;
          return formatPanelValue(value, ratio);
        };
        const elementValue = preview ? stats?.element_damage_bonus : manual.element_damage_bonus;
        return <article className={`live-panel-card live-panel-card-${teamIndex} ${preview?.complete === false ? "live-panel-card-incomplete" : ""}`} key={id}>
          <div className="live-panel-card-heading">
            <div className="live-panel-character">
              {character ? <img alt="" src={character.image_path} style={{ objectPosition: character.image_object_position }} /> : <span className="live-panel-avatar">?</span>}
              <div><strong>{character?.display_name ?? id}</strong><small>{teamIndex === 0 ? "主控角色" : "支援角色"}{character ? ` · ${character.element}` : ""}</small></div>
            </div>
            <span className={`live-panel-status ${statusClass}`}>{status}</span>
          </div>
          <div className="live-panel-featured-grid">
            <div className="live-panel-stat live-panel-featured-stat"><span>攻击力</span><strong>{readStat("attack")}</strong><small>ATK</small></div>
            <div className="live-panel-stat live-panel-featured-stat"><span>暴击率</span><strong>{readStat("crit_rate", true)}</strong><small>CRIT RATE</small></div>
            <div className="live-panel-stat live-panel-featured-stat"><span>暴击伤害</span><strong>{readStat("crit_damage", true)}</strong><small>CRIT DMG</small></div>
            <div className="live-panel-stat live-panel-featured-stat live-panel-element-bonuses"><span>元素增伤</span><strong>{formatElementBonuses(elementValue as Record<string, number | null> | null)}</strong><small>ELEMENT BONUS</small></div>
          </div>
          <div className="live-panel-secondary-grid">
            {LIVE_PANEL_STATS.filter(({ key }) => !["attack", "crit_rate", "crit_damage"].includes(key)).map(({ key, label, ratio }) => <div className="live-panel-stat" key={key}><span>{label}</span><strong>{readStat(key, ratio)}</strong></div>)}
          </div>
          <details className="live-panel-provenance" open={Boolean(preview)}>
            <summary><span>来源明细</span><small>{preview ? `${preview.provenance.length} 项装备/基础贡献` : "手工输入值"}</small></summary>
            <div className="provenance-list">
              {preview ? preview.provenance.map((item) => <div className="provenance-row" key={item.contribution_id}>
                <span>{item.source_label}</span><strong>{formatBuildContributionValue(item)}</strong><small>{item.stat}{item.element ? ` · ${item.element}` : ""}</small>
              </div>) : <div className="provenance-row provenance-manual"><span>手工局外面板</span><strong>已应用</strong><small>攻击、双暴与元素增伤来自左侧可编辑面板</small></div>}
            </div>
          </details>
        </article>;
      })}
    </div>
  </section>;
}

function numericPreviewStat(value: BuildPreviewStat | undefined): number | "" {
  return typeof value === "number" ? value : "";
}

function formatPanelDisplay(value: BuildPreviewStat | undefined): string {
  return typeof value === "number" ? formatNumber(value) : "—";
}

function previewRatioText(value: BuildPreviewStat | undefined): string {
  return typeof value === "number" ? formatPreviewRatio(value) : "";
}

function previewElementRatioText(value: BuildPreviewStat | undefined, element: string): string {
  if (!value || typeof value !== "object") return "";
  const amount = value[element];
  return typeof amount === "number" ? formatPreviewRatio(amount) : "";
}

function formatPanelValue(value: number | "" | undefined, ratio = false) {
  if (value === "" || value === undefined) return "—";
  return ratio ? formatPreviewRatio(value) : formatNumber(value);
}

function formatDriveValue(stat: string, value: number) {
  return formatDriveStatValue(stat, value);
}

function formatElementBonuses(value: number | Record<string, number | null> | null) {
  if (!value || typeof value !== "object") return "—";
  return Object.entries(value).map(([element, amount]) => `${element} ${amount === null ? "—" : `${formatNumber(amount * 100)}%`}`).join(" · ") || "—";
}

function isEquipmentSource(sourceType: string | null | undefined) {
  return sourceType === "weapon" || sourceType === "drive-disc";
}

export default App;
