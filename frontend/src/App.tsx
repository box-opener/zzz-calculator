import { useEffect, useMemo, useReducer, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import DriveDiscCard from "./components/DriveDiscCard";
import EventTraceDetails, { type EventTraceEnvelope } from "./components/EventTraceDetails";
import NumberField from "./components/NumberField";
import WEnginePicker from "./components/WEnginePicker";
import {
  canAddToTeamSlot,
  calculationTeamOrder,
  createTeamState,
  isCurrentCalculationResponse,
  teamReducer,
  type CalculationGeneration,
  type TeamAction,
} from "./state/teamReducer";
import {
  conditionValuesForViews,
  conditionCheckboxChecked,
  matchingMoveVariantIndexes,
  projectMoveOptions,
  reconcileEditorState,
  refreshConditionDefault,
  resolveAuthoritativeConditionContext,
  selectMoveVariantConditions,
  stackValueForDisplay,
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
  characterConfigFilename,
  createCharacterConfig,
  parseCharacterConfig,
  serializeCharacterConfig,
} from "./state/equipmentConfig";
import { filterCharacterCatalog, isCharacterSelectable } from "./state/characterLibrary";
import { aggregateEditorViews } from "./state/editorAggregation";
import { calculationNodeLabel, formatMultiplierPercent } from "./state/calculationDisplay";
import {
  defaultRemielleSourceSlots as remielleDefaultSourceSlots,
  remielleOrdinarySourceOptions as buildRemielleOrdinarySourceOptions,
  serializeRemielleSourceSlots,
} from "./state/remielleSourceSlots";
import {
  selectedYanagiAnomalySource,
  yanagiAnomalySourceOptions,
} from "./state/yanagiAnomalySource";

type Character = {
  character_id: string;
  display_name: string;
  code_name: string;
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
  field_type: "integer" | "boolean" | "select" | "slider";
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
  eligibility?: string;
  availability: string;
  enabled_by_default: boolean;
  toggleable: boolean;
  condition_ids: string[];
  condition_not_ids: string[];
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
  effective_damage_element?: string | null;
  luminance_source_elements?: string[];
  anomaly_source_elements?: string[];
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
    rule_item_id?: string | null;
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
    rule_item_id?: string | null;
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
    rule_item_id?: string | null;
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

type AnomalyStrengthFactorView = {
  factor: string;
  value: number | null;
  source_id: string | null;
  source_label: string | null;
  owner_character_id: string | null;
  unresolved: string | null;
};

type AnomalyEffectStrengthTraceView = {
  character_id: string;
  level: number | null;
  level_coefficient: number | null;
  anomaly_proficiency: number | null;
  anomaly_proficiency_factor: number | null;
  attack: number | null;
  element_bonus: number | null;
  normal_bonus: number | null;
  mutation: number | null;
  final_strength: number | null;
  element: string | null;
  factors: AnomalyStrengthFactorView[];
  unresolved: string | null;
  contributor_traces: { contributor_character_id: string; actual_written_buildup: number; trace: AnomalyEffectStrengthTraceView }[];
};

type CalculationDiagnostic = {
  diagnostic_id?: string;
  kind?: string;
  message: string;
  blocking: boolean;
  original_text?: string | null;
  candidates?: string[];
  details_only?: boolean;
};

type CalculationEventMode = {
  value: number | null;
  known_value: number | null;
  status: string;
  diagnostics: CalculationDiagnostic[];
  calculation_breakdown: { node: string; value: number | null; read_rule: string }[];
  anomaly_effect_strength_trace?: AnomalyEffectStrengthTraceView | null;
  anomaly_record_id?: string | null;
};

type CalculationEvent = {
  semantic_id: string;
  label: string;
  damage_type: string;
  damage_subtype: string | null;
  element?: string | null;
  repeat_count: number;
  crit_capability?: string;
  display_modes?: string[];
  modes: Record<string, CalculationEventMode>;
  common_application_trace: EventTraceEnvelope | null;
};

type CalculationView = {
  move_entry_id: string;
  display_modes?: string[];
  events: CalculationEvent[];
  totals: Record<string, { value: number | null; complete: boolean; diagnostics: { message: string }[] }>;
  diagnostics: CalculationDiagnostic[];
  resolved_character_snapshots: { character_id: string; stats: Record<string, number | null | Record<string, number | null>> }[];
  panel_traces: { recipient_character_id: string; effect_id: string; source_label: string | null; source_type: string | null; resolved_value: number; modifier_path: string }[];
  build_provenance: { character_id: string; contribution_id: string; source_id: string; source_type: string; source_label: string; stat: string; layer: string; value: number | null; element: string | null; unresolved: string | null }[];
  panel_source_results?: {
    source_character_id: string;
    source_character_name: string;
    element: string;
    events: CalculationEvent[];
    totals: CalculationView["totals"];
    diagnostics: CalculationDiagnostic[];
  }[];
};

const VIVIAN_ID = "character:1331";
const VIVIAN_DISCHARGE_ENTRY_ID = "move-entry:character:1331:discharge-current-panel";
const VIVIAN_PROPHECY_TICK_ENTRY_ID = "move-entry:character:1331:core-prophecy-tick";
const VIVIAN_PROPHECY_TICK_PARAMETER_ID = "parameter:vivian:prophecy-tick-count";
const ENEMY_RESISTANCE_FIELDS = [
  { element: "physical", label: "物理抗性" },
  { element: "fire", label: "火抗性" },
  { element: "ice", label: "冰抗性" },
  { element: "electric", label: "电抗性" },
  { element: "ether", label: "以太抗性" },
  { element: "wind", label: "风抗性" },
  { element: "luminance", label: "流明抗性" },
] as const;
type EnemyResistanceElement = typeof ENEMY_RESISTANCE_FIELDS[number]["element"];
const INITIAL_ENEMY_RESISTANCES: Record<EnemyResistanceElement, number> = {
  physical: 0,
  fire: 0,
  ice: 0,
  electric: 0,
  ether: 0,
  wind: 0,
  luminance: 0,
};

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
  const [teamState, dispatchTeam] = useReducer(teamReducer, createTeamState([]));
  const { teamCharacterIds, currentOperatorId } = teamState;
  const [editorViews, setEditorViews] = useState<Record<string, EditorView | null>>({});
  const [wengineViews, setWengineViews] = useState<Record<string, WEngineEditorView | null>>({});
  const [driveDiscViews, setDriveDiscViews] = useState<Record<string, DriveDiscEditorView | null>>({});
  const [moveEntryId, setMoveEntryId] = useState("");
  const [configs, setConfigs] = useState<Record<string, Record<string, unknown>>>({});
  const [remielleSourceSlotOverrides, setRemielleSourceSlotOverrides] = useState<string[] | null>(null);
  const [yanagiPolarSourceKey, setYanagiPolarSourceKey] = useState<string | null>(null);
  const [conditionValues, setConditionValues] = useState<Record<string, boolean | null>>({});
  const [parameterValues, setParameterValues] = useState<Record<string, number | null>>({});
  const conditionValuesRef = useRef<Record<string, boolean | null>>({});
  const explicitConditionValuesRef = useRef<Record<string, boolean | null>>({});
  const [enabledRules, setEnabledRules] = useState<Set<string>>(new Set());
  const [disabledRules, setDisabledRules] = useState<Set<string>>(new Set());
  const [triggerActors, setTriggerActors] = useState<Record<string, string>>({});
  const [stacks, setStacks] = useState<Record<string, number>>({});
  const [characterLevels, setCharacterLevels] = useState<Record<string, number>>({});
  const [wengineSelections, setWengineSelections] = useState<Record<string, { id: string; level: number; refinement: number }>>({});
  const [driveDiscSelections, setDriveDiscSelections] = useState<Record<string, DriveDiscConfig[]>>({});
  const [buildPreviews, setBuildPreviews] = useState<Record<string, BuildPreview | null>>({});
  const [enemyLevel, setEnemyLevel] = useState(70);
  const [enemyDamageReduction, setEnemyDamageReduction] = useState(0);
  const [enemyIsStunned, setEnemyIsStunned] = useState(false);
  const [enemyDefense, setEnemyDefense] = useState(857);
  const [enemyResistances, setEnemyResistances] = useState(INITIAL_ENEMY_RESISTANCES);
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
  const dragSourceTeamSlot = useRef<number | null>(null);
  const [draggingTeamSlot, setDraggingTeamSlot] = useState<number | null>(null);
  const calculationGeneration = useRef(0);

  const commitConditionValues = (next: Record<string, boolean | null>) => {
    conditionValuesRef.current = next;
    setConditionValues(next);
  };

  const teamIds = teamCharacterIds;
  const remielleId = "character:1581";
  const activeRemielleCinema = Number(configs[remielleId]?.cinema_level ?? 0);
  const remielleOrdinarySourceOptions = buildRemielleOrdinarySourceOptions(
    teamIds,
    characters,
    editorViews,
    remielleId,
  );
  const defaultRemielleSourceSlots = remielleDefaultSourceSlots(
    teamIds,
    remielleOrdinarySourceOptions,
  );
  const validRemielleSourceOptions = new Set([
    "",
    ...remielleOrdinarySourceOptions.map((item) => item.key),
    ...(activeRemielleCinema >= 1 ? ["special-entry"] : []),
    ...(activeRemielleCinema >= 4 ? ["special-refill"] : []),
    ...(activeRemielleCinema >= 6 ? ["special-basic4"] : []),
  ]);
  const effectiveRemielleSourceSlots = (
    remielleSourceSlotOverrides ?? defaultRemielleSourceSlots
  ).slice(0, 3).map((value) => validRemielleSourceOptions.has(value) ? value : "");
  const yanagiAnomalySources = yanagiAnomalySourceOptions(teamIds, editorViews);
  const effectiveYanagiAnomalySource = selectedYanagiAnomalySource(
    yanagiAnomalySources,
    yanagiPolarSourceKey,
  );
  const yanagiPolarMoveEntries = new Set([
    "move-entry:character:1221:ex-special-moonlit-flow-thrust",
    "move-entry:character:1221:ex-special-moonlit-flow-downfall",
    "move-entry:character:1221:ultimate-thunder-shadow",
  ]);
  const showYanagiPolarSource = currentOperatorId === "character:1221"
    && yanagiPolarMoveEntries.has(moveEntryId)
    && yanagiAnomalySources.length > 0;
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
  const moveSelectionIssue = teamIds.length === 0
    ? "请先添加至少一名角色"
    : !selectedMove
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
    driveDiscSource = driveDiscSelections,
    characterLevelsSource = characterLevels,
  ) => {
    const generation = editorGeneration.current + 1;
    editorGeneration.current = generation;
    editorAbortController.current?.abort();
    const abortController = new AbortController();
    editorAbortController.current = abortController;
    setLoading(true);
    const normalizedTeam = [...new Set(nextTeam)].slice(0, 3);
    const normalizedOperator = normalizedTeam.includes(nextOperator)
      ? nextOperator
      : normalizedTeam[0] ?? "";
    if (normalizedTeam.length === 0) {
      // Keep the app shell/catalog available, but issue no character-scoped
      // editor, equipment, or build-preview requests until a role is selected.
      calculationGeneration.current += 1;
      setCalculating(false);
      setEditorViews({});
      setWengineViews({});
      setDriveDiscViews({});
      setBuildPreviews({});
      setMoveEntryId("");
      setCalculation(null);
      commitConditionValues({});
      explicitConditionValuesRef.current = {};
      setParameterValues({});
      setEnabledRules(new Set());
      setDisabledRules(new Set());
      setTriggerActors({});
      setStacks({});
      setDiagnostics([]);
      setLoading(false);
      return;
    }
    try {
      const frostbiteConditionId = `condition:enemy:frostbite-crit-damage-active:primary:${normalizedOperator}`;
      const previewConditionSource = refreshConditionDefault(
        conditionSource,
        frostbiteConditionId,
        explicitConditionValuesRef.current,
      );
      const nextEditorViews = await Promise.all(
        normalizedTeam.map((owner) => jsonRequest<EditorView>("/api/v1/definitions/preview", {
          method: "POST",
          body: JSON.stringify({
            character_id: owner,
            team_character_ids: normalizedTeam,
            primary_character_id: normalizedOperator,
            condition_values: previewConditionSource,
            compile_config: owner === "character:1581"
              ? { ...(configSource[owner] ?? {}), formation_character_ids: normalizedTeam }
              : configSource[owner] ?? {},
          }),
          signal: abortController.signal,
        })),
      );
      const authoritativeConditionContext = resolveAuthoritativeConditionContext(
        previewConditionSource,
        nextEditorViews.flatMap((view) => view.scenario_conditions),
      );
      const nextWengineViews = await Promise.all(
        normalizedTeam.map((owner) => {
          const selection = wengineSource[owner];
          if (!selection?.id) {
            return Promise.resolve(null);
          }
          return jsonRequest<WEngineEditorView>("/api/v1/wengines/preview", {
            method: "POST",
            body: JSON.stringify({
              wengine_id: selection.id,
              equipped_character_id: owner,
              team_character_ids: normalizedTeam,
              formation_character_ids: normalizedTeam,
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
          return jsonRequest<DriveDiscEditorView>("/api/v1/drive-discs/preview", {
            method: "POST",
            body: JSON.stringify({
              equipped_character_id: owner,
              team_character_ids: normalizedTeam,
              formation_character_ids: normalizedTeam,
              discs: driveDiscSource[owner] ?? [],
              condition_context: authoritativeConditionContext,
            }),
            signal: abortController.signal,
          });
        }),
      );
      const nextBuildPreviews = await Promise.all(
        normalizedTeam.map((owner) => {
          const selection = wengineSource[owner];
          return jsonRequest<BuildPreview>("/api/v1/builds/preview", {
            method: "POST",
            body: JSON.stringify({
              character_id: owner,
              team_character_ids: normalizedTeam,
              formation_character_ids: normalizedTeam,
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
    calculationGeneration.current += 1;
    setCalculating(false);
    setCalculation(null);
    void loadEditors(
      next.teamCharacterIds,
      next.currentOperatorId,
      configs,
      conditionValuesRef.current,
      {},
      wengineSelections,
      driveDiscSelections,
      characterLevels,
    );
  };

  const beginTeamSlotDrag = (slotIndex: number, event: ReactPointerEvent<HTMLElement>) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    if (event.target instanceof Element && event.target.closest("button, input, select")) return;
    if (event.pointerType !== "mouse" && !(event.target instanceof Element && event.target.closest(".team-slot-art"))) return;
    dragSourceTeamSlot.current = slotIndex;
    setDraggingTeamSlot(slotIndex);
    event.currentTarget.setPointerCapture(event.pointerId);
    event.preventDefault();
  };

  const finishTeamSlotDrag = (event: ReactPointerEvent<HTMLElement>) => {
    const sourceSlot = dragSourceTeamSlot.current;
    dragSourceTeamSlot.current = null;
    setDraggingTeamSlot(null);
    if (sourceSlot === null) return;
    const target = document
      .elementFromPoint(event.clientX, event.clientY)
      ?.closest<HTMLElement>("[data-team-slot-index]");
    const targetSlot = Number(target?.dataset.teamSlotIndex);
    if (!Number.isInteger(targetSlot) || targetSlot === sourceSlot) return;
    applyTeamAction({ type: "swap-slots", firstSlot: sourceSlot, secondSlot: targetSlot });
  };

  const cancelTeamSlotDrag = () => {
    dragSourceTeamSlot.current = null;
    setDraggingTeamSlot(null);
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
        return loadEditors(teamIds, currentOperatorId, configs, conditionValuesRef.current, {}, wengineSelections);
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

  const updateCharacterLevel = (characterId: string, value: number) => {
    const nextLevels = { ...characterLevels, [characterId]: value };
    setCharacterLevels(nextLevels);
    void loadEditors(
      teamIds,
      currentOperatorId,
      configs,
      conditionValuesRef.current,
      {},
      wengineSelections,
      driveDiscSelections,
      nextLevels,
    );
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
    calculationGeneration.current += 1;
    setCalculating(false);
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
    calculationGeneration.current += 1;
    setCalculating(false);
    setCalculation(null);
    if (option.entryId === VIVIAN_PROPHECY_TICK_ENTRY_ID) {
      setParameterValues((current) => (
        current[VIVIAN_PROPHECY_TICK_PARAMETER_ID] === undefined
        || current[VIVIAN_PROPHECY_TICK_PARAMETER_ID] === null
          ? { ...current, [VIVIAN_PROPHECY_TICK_PARAMETER_ID]: 1 }
          : current
      ));
    }
    if (option.entryId === "move-entry:character:1331:discharge-current-panel") {
      const conditionId = "condition:vivian:mutation-triggered";
      const nextConditionValues = {
        ...conditionValuesRef.current,
        [conditionId]: true,
      };
      const coreRuleIds = allRules
        .filter((rule) => (
          rule.rule_id.startsWith("rule:character:1331:core:anomaly-mutation:")
          && rule.eligibility !== "ineligible"
          && !disabledRules.has(rule.rule_id)
        ))
        .map((rule) => rule.rule_id);
      const nextEnabledRules = new Set([...enabledRules, ...coreRuleIds]);
      const nextDisabledRules = new Set(
        [...disabledRules].filter((ruleId) => !coreRuleIds.includes(ruleId)),
      );
      commitConditionValues(nextConditionValues);
      setEnabledRules(nextEnabledRules);
      setDisabledRules(nextDisabledRules);
      void loadEditors(
        teamIds,
        currentOperatorId,
        configs,
        nextConditionValues,
        {
          conditionValues: nextConditionValues,
          enabledRules: nextEnabledRules,
          disabledRules: nextDisabledRules,
        },
      );
    }
  };

  const updateWengineSelection = (
    owner: string,
    selection: { id: string; level: number; refinement: number },
  ) => {
    const nextSelections = { ...wengineSelections, [owner]: selection };
    setWengineSelections(nextSelections);
    void loadEditors(teamIds, currentOperatorId, configs, conditionValuesRef.current, {}, nextSelections);
  };

  const selectWengine = (owner: string, wengineId: string | null) => {
    if (wengineId === null) {
      const nextSelections = { ...wengineSelections };
      delete nextSelections[owner];
      setWengineSelections(nextSelections);
      void loadEditors(teamIds, currentOperatorId, configs, conditionValuesRef.current, {}, nextSelections);
      return;
    }
    updateWengineSelection(owner, {
      ...(wengineSelections[owner] ?? { level: 60, refinement: 1 }),
      id: wengineId,
    });
  };

  const updateEnemyResistance = (element: EnemyResistanceElement, value: number) => {
    setEnemyResistances((current) => ({ ...current, [element]: value }));
  };

  const exportEquipmentConfig = (owner: string) => {
    const selection = wengineSelections[owner];
    const currentCompileConfig = configs[owner] ?? {};
    const compileConfig: Record<string, unknown> = {
      core_level: currentCompileConfig.core_level ?? 7,
      cinema_level: currentCompileConfig.cinema_level ?? 0,
      ...(currentCompileConfig.skill_levels ? { skill_levels: currentCompileConfig.skill_levels } : {}),
      ...(typeof currentCompileConfig.mingxin_active === "boolean" ? { mingxin_active: currentCompileConfig.mingxin_active } : {}),
      ...(typeof currentCompileConfig.entry_move_uses_linren === "boolean" ? { entry_move_uses_linren: currentCompileConfig.entry_move_uses_linren } : {}),
    };
    const config = createCharacterConfig(
      owner,
      characterLevels[owner] ?? 60,
      "equipment-build",
      compileConfig,
      selection?.id
        ? { id: selection.id, level: selection.level, refinement: selection.refinement }
        : null,
      driveDiscSelections[owner] ?? [],
      null,
    );
    const blob = new Blob([serializeCharacterConfig(config)], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const character = characters.find((item) => item.character_id === owner);
    anchor.href = url;
    anchor.download = characterConfigFilename(character?.code_name, owner);
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    setEquipmentFeedback((current) => ({
      ...current,
      [owner]: { kind: "success", message: "角色完整配置已导出为 JSON，可随时重新导入。" },
    }));
  };

  const importEquipmentConfig = async (owner: string, file: File) => {
    try {
      const result = parseCharacterConfig(
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
      if (result.wengineProvided && result.equipment.wengine) {
        nextWengineSelections[owner] = { ...result.equipment.wengine };
      } else if (result.wengineProvided) {
        // A v1/v2 explicit null means clear.  Drive-only legacy files omit
        // the weapon field and therefore deliberately retain the current one.
        delete nextWengineSelections[owner];
      }
      const nextDriveDiscSelections = {
        ...driveDiscSelections,
        [owner]: result.config.drive_discs,
      };
      const nextCharacterLevels = {
        ...characterLevels,
        ...(result.source === "v2" ? { [owner]: result.config.character_level } : {}),
      };
      const nextConfigs = {
        ...configs,
        ...(result.source === "v2" ? { [owner]: { ...result.config.compile_config } } : {}),
      };
      // Commit all imported values together, then issue one authoritative
      // editor/build refresh using the complete next state.
      setWengineSelections(nextWengineSelections);
      setDriveDiscSelections(nextDriveDiscSelections);
      setCharacterLevels(nextCharacterLevels);
      setConfigs(nextConfigs);
      setEquipmentFeedback((current) => ({
        ...current,
        [owner]: { kind: "success", message: `已导入 ${result.config.drive_discs.length} 个驱动盘${result.equipment.wengine ? "与 1 把音擎" : ""}及角色进度。` },
      }));
      setDiagnostics([]);
      void loadEditors(
        teamIds,
        currentOperatorId,
        nextConfigs,
        conditionValuesRef.current,
        {},
        nextWengineSelections,
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
    const selection = wengineSelections[id];
    return [id, {
      level: characterLevels[id] ?? 60,
      build_mode: "equipment-build",
      ...(selection?.id ? { wengine_id: selection.id, wengine_level: selection.level, wengine_refinement: selection.refinement } : {}),
      drive_discs: driveDiscSelections[id] ?? [],
    }];
  }));

  const calculate = async () => {
    if (teamIds.length === 0 || !currentOperatorId || !moveEntryId || moveSelectionIssue) {
      if (moveSelectionIssue) setDiagnostics([moveSelectionIssue]);
      return;
    }
    const calculationRequestGeneration: CalculationGeneration = {
      calculation: ++calculationGeneration.current,
      editor: editorGeneration.current,
    };
    setCalculating(true);
    setDiagnostics([]);
    try {
      const scenarioConditionValues = conditionValuesForViews(
        conditionValuesRef.current,
        allConditions,
      );
      const luminanceSourceSlots = serializeRemielleSourceSlots(
        effectiveRemielleSourceSlots,
        remielleOrdinarySourceOptions,
        remielleId,
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
          // Keep the player's fixed 1-2-3 lineup for effects that reference a slot.
          formation_character_ids: requestTeam.formationCharacterIds,
          move_entry_id: moveEntryId,
          ...(currentOperatorId === remielleId
            ? { luminance_source_slots: luminanceSourceSlots }
            : {}),
          ...(showYanagiPolarSource && effectiveYanagiAnomalySource ? {
            polarity_anomaly_source: {
              source_character_id: effectiveYanagiAnomalySource.characterId,
              element: effectiveYanagiAnomalySource.element,
            },
          } : {}),
          compile_configs: Object.fromEntries(teamIds.map((id) => [id, {
            core_level: 7,
            cinema_level: 0,
            ...(configs[id] ?? {}),
          }])),
          condition_values: scenarioConditionValues,
          parameter_values: parameterValues,
          character_builds: buildPayloads(),
          enemy: { enemy_id: "enemy:ui", level: enemyLevel, initial_defense: enemyDefense, damage_resistance: enemyResistances, damage_reduction: enemyDamageReduction, stun_vulnerability_bonus: stunVulnerability, is_stunned: enemyIsStunned },
          enabled_rule_item_ids: [...enabledRules],
          selected_trigger_inputs: Object.entries(triggerActors).filter(([, actor_id]) => actor_id).map(([input_id, actor_id]) => ({ input_id, actor_id })),
          rule_stack_counts: stacks,
        }),
      });
      if (!isCurrentCalculationResponse(calculationRequestGeneration, {
        calculation: calculationGeneration.current,
        editor: editorGeneration.current,
      })) return;
      setCalculation(result);
    } catch (error) {
      if (isCurrentCalculationResponse(calculationRequestGeneration, {
        calculation: calculationGeneration.current,
        editor: editorGeneration.current,
      })) setDiagnostics([(error as Error).message]);
    } finally {
      if (calculationRequestGeneration.calculation === calculationGeneration.current) {
        setCalculating(false);
      }
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

  const renderCompileField = (owner: string, field: CompileField) => {
    const fieldValue = configFieldValue(owner, field);
    const unit = field.field_id.includes("level") ? "级" : field.field_id.includes("stack") ? "层" : undefined;
    if (field.field_type === "boolean") {
      return <label className="check-field" key={`${owner}-${field.field_id}`}><span><strong>{field.label}</strong><small>{field.help_text ?? "编译期配置"}</small></span><input disabled={!field.editable} type="checkbox" checked={Boolean(fieldValue)} onChange={(event) => updateConfigField(owner, field, event.target.checked)} /></label>;
    }
    if (field.field_type === "select") {
      return <label className="select-field" key={`${owner}-${field.field_id}`}><span>{field.label}</span><select disabled={!field.editable} value={String(fieldValue)} onChange={(event) => updateConfigField(owner, field, Number(event.target.value))}>{field.options.map((option) => <option key={option} value={option}>{option}</option>)}</select></label>;
    }
    if (field.field_type === "slider") {
      return <label className="slider-field" key={`${owner}-${field.field_id}`}>
        <span><strong>{field.label}</strong><output>{Number(fieldValue)}</output></span>
        <input
          aria-label={field.label}
          disabled={!field.editable}
          type="range"
          min={field.minimum ?? 0}
          max={field.maximum ?? 6}
          step={1}
          value={Number(fieldValue)}
          onChange={(event) => updateConfigField(owner, field, Number(event.target.value))}
        />
        {field.help_text && <small>{field.help_text}</small>}
      </label>;
    }
    return <NumberField key={`${owner}-${field.field_id}`} label={field.label} value={Number(fieldValue)} integer min={field.minimum ?? undefined} max={field.maximum ?? undefined} unit={unit} helper={field.help_text ?? "整数配置"} disabled={!field.editable} onCommit={(value) => updateConfigField(owner, field, value)} />;
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
          <div className="team-slot-grid" onPointerCancel={cancelTeamSlotDrag} onPointerUp={finishTeamSlotDrag}>
            {Array.from({ length: 3 }, (_, slotIndex) => {
              const id = teamIds[slotIndex];
              const character = characters.find((item) => item.character_id === id);
              if (!id || !character) {
                return <button className="team-slot team-slot-empty" data-team-slot-index={slotIndex} disabled={!canAddToTeamSlot(slotIndex, teamIds.length)} key={`empty-${slotIndex}`} onClick={() => openCharacterLibrary(slotIndex)} type="button">
                  <span className="team-slot-plus" aria-hidden="true">＋</span>
                  <strong>添加角色</strong>
                  <small>第 {slotIndex + 1} 个队伍槽位</small>
                </button>;
              }
              const isOperator = id === currentOperatorId;
              return <article
                aria-grabbed={draggingTeamSlot === slotIndex}
                className={`team-slot team-slot-filled ${isOperator ? "team-slot-operator" : ""} ${draggingTeamSlot === slotIndex ? "team-slot-dragging" : ""}`}
                data-team-slot-index={slotIndex}
                key={id}
                onPointerDown={(event) => beginTeamSlotDrag(slotIndex, event)}
              >
                <div className="team-slot-art">
                  <img alt={character.display_name} draggable={false} src={character.image_path} style={{ objectPosition: character.image_object_position }} />
                  <span className="rarity">{character.rarity}</span>
                  {isOperator && <span className="operator-badge">当前操作</span>}
                  <span className="team-slot-drag-hint" aria-hidden="true">⠿ 拖动交换</span>
                </div>
                <div className="team-slot-copy"><strong>{character.display_name}</strong><small>{specialtyLabel(character.specialty)} · {elementLabel(character.element)}</small></div>
                <div className="team-slot-actions">
                  <button className="secondary-button" disabled={isOperator} onClick={() => applyTeamAction({ type: "set-current-operator", characterId: id })} type="button">设为当前操作</button>
                  <button className="secondary-button" onClick={() => openCharacterLibrary(slotIndex)} type="button">替换</button>
                  <button className="secondary-button team-slot-remove" onClick={() => applyTeamAction({ type: "remove-character", characterId: id })} type="button">移除</button>
                </div>
              </article>;
            })}
          </div>
          {selectedCurrent && <div className="selection-summary"><span className="eyebrow">CURRENT OPERATOR</span><strong>{selectedCurrent.display_name}</strong><span className="muted">{selectedCurrent.character_id} · {supportingIds.length} 名支援角色</span></div>}
          <LivePanel
            teamIds={teamIds}
            characters={characters}
            editorViews={editorViews}
            previews={buildPreviews}
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
            {teamIds.length === 0
              ? <div className="empty-team-hint">先从上方角色库添加角色，再配置音擎和驱动盘。</div>
              : teamIds.map((id, teamIndex) => {
              const driveView = driveDiscViews[id];
              const selectedDiscs = driveDiscSelections[id] ?? [];
              const preview = buildPreviews[id];
              const character = characters.find((item) => item.character_id === id);
              const selectedWengine = wengines.find((item) => item.wengine_id === wengineSelections[id]?.id);
              const feedback = equipmentFeedback[id];
              const roleLabel = teamIndex === 0 ? "主控角色" : "支援角色";
              const progressFields = editorViews[id]?.compile_config_fields.filter(isCharacterProgressField) ?? [];
              return (
                <article className="build-character build-character-equipment" key={id}>
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
                      <span className="equipment-schema-note">JSON · 角色配置 v2</span>
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
                  <div className="equipment-schema-copy">导入或导出当前角色的等级、核心/影画、技能、音擎与驱动盘；文件会完整校验输入。</div>
                  {feedback && <p className={`equipment-feedback ${feedback.kind}`}>{feedback.kind === "success" ? "✓" : "!"} {feedback.message}</p>}

                  <div className="build-level-strip">
                    <NumberField
                      label="角色等级"
                      value={characterLevels[id] ?? 60}
                      integer
                      min={1}
                      max={60}
                      unit="级"
                      helper="可编辑范围 1–60"
                      onCommit={(value) => updateCharacterLevel(id, value)}
                    />
                  </div>

                  {progressFields.length > 0 && <div className="character-progress-config">
                    <div className="subsection-heading"><div><span className="eyebrow">CHARACTER CONFIG</span><h3>角色技能配置</h3></div><span className="subsection-badge">核心 · 影画 · 技能</span></div>
                    <div className="character-progress-grid">{progressFields.map((field) => renderCompileField(id, field))}</div>
                  </div>}

                  <div className="equipment-build-details">
                    <div className="subsection-heading"><div><span className="eyebrow">W-ENGINE</span><h3>音擎</h3></div><span className="subsection-badge">音擎构筑</span></div>
                    <div className="wengine-fields">
                      <div className="wengine-selection-field"><div className="select-field wengine-select"><span>音擎</span><WEnginePicker engines={wengines} characterId={id} specialty={character?.specialty} selectedId={wengineSelections[id]?.id} specialtyLabel={specialtyLabel} onSelect={(wengineId) => selectWengine(id, wengineId)} /></div>{selectedWengine && selectedWengine.specialty !== character?.specialty && <small className="wengine-specialty-warning">职业与音擎专精不匹配，仅基础攻击力和主词条生效。</small>}</div>
                      <NumberField label="音擎等级" value={wengineSelections[id]?.level ?? 60} integer min={60} max={60} unit="级" helper="当前构筑等级上限" readOnly />
                      <NumberField label="精炼" value={wengineSelections[id]?.refinement ?? 1} integer min={1} max={5} unit="阶" helper="范围 1–5 阶" onCommit={(value) => updateWengineSelection(id, { ...(wengineSelections[id] ?? { id: "", level: 60 }), refinement: value })} />
                    </div>
                  </div>

                  <div className="drive-disc-section-wrap">
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
                  </div>
                </article>
              );
            })}
          </div>
          {calculation && calculation.build_provenance.length > 0 && <details className="trace-list provenance-details"><summary><span><span className="eyebrow">BUILD PROVENANCE</span><strong>构筑来源明细</strong></span><small>{calculation.build_provenance.length} 项</small></summary>{teamIds.map((owner) => { const traces = calculation.build_provenance.filter((trace) => trace.character_id === owner); return traces.length > 0 && <div className="provenance-character-group" key={owner}><h4>{characters.find((item) => item.character_id === owner)?.display_name ?? owner}</h4>{traces.map((trace) => <div className="trace-row" key={trace.contribution_id}><span>{trace.source_label}</span><strong>{trace.value === null ? "?" : `+${formatNumber(trace.value)}`}</strong><small>{trace.stat} · {trace.layer}</small></div>)}</div>; })}</details>}
          <div className="section-heading compact"><div><p className="eyebrow">TARGET</p><h2>敌人</h2></div></div>
          <div className="target-fields">
            <NumberField label="等级" value={enemyLevel} integer min={1} max={80} unit="级" helper="敌人等级 1–80" onCommit={setEnemyLevel} />
            <NumberField label="防御力" value={enemyDefense} min={0} helper="敌方初始防御力" onCommit={setEnemyDefense} />
            {ENEMY_RESISTANCE_FIELDS.map(({ element, label }) => <NumberField key={element} label={label} value={enemyResistances[element]} unit="%" displayAsPercent helper="底层 ratio 值按百分比编辑" onCommit={(value) => updateEnemyResistance(element, value)} />)}
            <NumberField label="失衡易伤" value={stunVulnerability} unit="×" helper="伤害倍率，例如 1.5×" onCommit={setStunVulnerability} />
            <NumberField label="减易伤" value={enemyDamageReduction} unit="%" displayAsPercent helper="底层 ratio 值按百分比编辑" onCommit={setEnemyDamageReduction} />
            <label className="check-field"><span>当前处于失衡</span><input type="checkbox" checked={enemyIsStunned} onChange={(event) => setEnemyIsStunned(event.target.checked)} /></label>
          </div>
          <p className="target-resistance-note">烈霜、玄墨、凛刃分别沿用冰、以太、物理抗性。</p>
        </section>
      </section>

      <section className="workspace-grid">
        <section className="glass-card controls-panel">
          <div className="section-heading"><div><p className="eyebrow">SCENARIO</p><h2>场景与规则</h2></div>{loading && <span className="muted">读取中…</span>}</div>
          <div className="config-field-grid">{allConfigFields.filter(({ field }) => !isCharacterProgressField(field)).map(({ owner, field }) => renderCompileField(owner, field))}</div>
          {visibleScenarioConditions.length > 0 && <div className="control-list"><div className="section-heading compact"><div><p className="eyebrow">CHARACTER STATES</p><h2>角色状态</h2><p className="control-section-hint">只显示可直接理解的独立状态；招式倍率在右侧招式下拉框中选择。</p></div></div>{visibleScenarioConditions.map((condition) => <label className="toggle-row" key={condition.condition_id}><span><strong>{condition.label}</strong><small>{condition.resolution} · 影响相关规则</small></span><input type="checkbox" checked={conditionCheckboxChecked(condition.condition_id, condition.value, conditionValues)} onChange={(event) => { explicitConditionValuesRef.current[condition.condition_id] = event.target.checked; const next = { ...conditionValuesRef.current, [condition.condition_id]: event.target.checked }; commitConditionValues(next); void loadEditors(teamIds, currentOperatorId, configs, next, { conditionValues: next }); }} /></label>)}</div>}
          {currentOperatorId === remielleId && <div className="control-list remielle-source-slots">
            <div className="section-heading compact"><div><p className="eyebrow">VIRTUAL VOID SOURCES</p><h2>虚曜来源槽</h2><p className="control-section-hint">最多选择三个来源；普通来源读取队友当前面板，特殊来源使用蕾米埃尔自身快照。留空表示没有该来源。</p></div></div>
            {effectiveRemielleSourceSlots.map((value, index) => <label className="select-field" key={`remielle-source-slot-${index}`}>
              <span>来源 {index + 1}</span>
              <select value={value} onChange={(event) => setRemielleSourceSlotOverrides((current) => {
                const next = [...(current ?? defaultRemielleSourceSlots)];
                next[index] = event.target.value;
                return next;
              })}>
                <option value="">空槽</option>
                {remielleOrdinarySourceOptions.map((item) => <option key={item.key} value={item.key}>
                  普通虚曜 · {item.characterName} · {elementLabel(item.element)}
                </option>)}
                {activeRemielleCinema >= 1 && <option value="special-entry">特殊虚曜 · 入场来源</option>}
                {activeRemielleCinema >= 4 && <option value="special-refill">特殊虚曜 · 影画4补充</option>}
                {activeRemielleCinema >= 6 && <option value="special-basic4">特殊虚曜 · 普攻第四段来源（25%）</option>}
              </select>
            </label>)}
          </div>}
          {showYanagiPolarSource && <div className="control-list yanagi-polar-source">
            <div className="section-heading compact"><div><p className="eyebrow">POLAR DISORDER SOURCE</p><h2>本次极性紊乱来源</h2><p className="control-section-hint">选择一条当前属性异常记录；默认使用柳的感电记录。</p></div></div>
            <label className="select-field"><span>异常来源</span><select value={effectiveYanagiAnomalySource?.key ?? ""} onChange={(event) => setYanagiPolarSourceKey(event.target.value || null)}>
              {yanagiAnomalySources.map((option) => <option key={option.key} value={option.key}>
                {characters.find((character) => character.character_id === option.characterId)?.display_name ?? option.characterId} · {elementLabel(option.element)}
              </option>)}
            </select></label>
          </div>}
          {allParameters.length > 0 && <div className="parameter-list"><div className="section-heading compact"><div><p className="eyebrow">SCENARIO PARAMETERS</p><h2>次数与数值输入</h2></div></div><div className="parameter-field-grid">{allParameters.map((parameter) => { const currentValue = parameterValues[parameter.parameter_id] !== undefined ? parameterValues[parameter.parameter_id] : parameter.value; return <NumberField key={parameter.parameter_id} label={parameter.label} value={currentValue} integer min={parameter.minimum} max={parameter.maximum ?? undefined} unit={parameter.parameter_id.includes("count") || parameter.parameter_id.includes("repeat") ? "次" : undefined} helper={parameter.resolution} placeholder={currentValue === null ? "未指定" : undefined} onCommit={(value) => setParameterValues((current) => ({ ...current, [parameter.parameter_id]: value }))} />; })}</div></div>}
          <div className="rule-list">{allRules.map((rule) => <div className={`rule-row ${rule.availability !== "available" ? "disabled" : ""}`} key={rule.rule_id}><span><strong>{rule.label}</strong><small>{rule.source_label} · {rule.eligibility === "ineligible" ? "适用条件未满足" : rule.availability}</small></span><input disabled={!rule.toggleable} type="checkbox" checked={enabledRules.has(rule.rule_id)} onChange={(event) => { const checked = event.target.checked; setEnabledRules((current) => { const next = new Set(current); if (checked) next.add(rule.rule_id); else next.delete(rule.rule_id); return next; }); setDisabledRules((current) => { const next = new Set(current); if (checked) next.delete(rule.rule_id); else next.add(rule.rule_id); return next; }); }} />{rule.stack.minimum !== null && <NumberField className="stack-field" label="层数" unit="层" integer min={rule.stack.minimum} max={rule.stack.maximum ?? undefined} value={stackValueForDisplay(stacks[rule.rule_id], rule.stack.default, rule.stack.minimum)} helper={`范围 ${rule.stack.minimum}–${rule.stack.maximum ?? "∞"}`} onCommit={(value) => setStacks((current) => ({ ...current, [rule.rule_id]: value }))} />}</div>)}</div>
          {allTriggers.length > 0 && <><div className="section-heading compact"><div><p className="eyebrow">TRIGGER FACTS</p><h2>场景触发</h2><p className="control-section-hint">需要明确入场角色的 Effect 会在这里显示；留空时计算 trace 会标记为 blocked。</p></div></div><div className="trigger-field-grid">{allTriggers.map((trigger) => { const selectedActor = triggerActors[trigger.input_id]; return <label className={`trigger-field ${selectedActor ? "trigger-field-selected" : "trigger-field-missing"}`} key={trigger.input_id}><span>{trigger.label}</span><select value={selectedActor ?? ""} onChange={(event) => setTriggerActors((current) => { const next = { ...current }; if (event.target.value) next[trigger.input_id] = event.target.value; else delete next[trigger.input_id]; return next; })}><option value="">未指定</option>{trigger.actor_options.map((actor) => <option key={actor} value={actor}>{characters.find((item) => item.character_id === actor)?.display_name ?? actor}</option>)}</select><small>{selectedActor ? `已指定：${characters.find((item) => item.character_id === selectedActor)?.display_name ?? selectedActor}` : "⚠ 需要指定入场角色"}</small></label>; })}</div></>}
        </section>

        <section className="glass-card result-panel">
          <div className="section-heading"><div><p className="eyebrow">MOVE CALCULATION</p><h2>招式结算</h2></div><button className="primary-button" disabled={teamIds.length === 0 || calculating || loading || !moveEntryId || Boolean(moveSelectionIssue)} onClick={calculate} type="button">{calculating ? "计算中…" : "计算"}</button></div>
          <label className="move-select">招式<select disabled={teamIds.length === 0} value={selectedMoveOption?.optionKey ?? ""} onChange={(event) => selectMoveOption(event.target.value)}><option value="" disabled>{moveSelectionIssue ?? "请选择招式"}</option>{moveOptions.map((option) => <option key={option.optionKey} value={option.optionKey}>{option.label}</option>)}</select></label>
          {moveSelectionIssue && <p className="control-section-hint">⚠ {moveSelectionIssue}；未发送计算请求。</p>}
          {calculation ? (
            <div className="calculation-output">
              <div className="totals-grid">
                {(calculation.display_modes ?? ["non-crit", "expected", "full-crit"]).map((mode) => (
                  <div className="total-card" key={mode}>
                    <small>{mode}</small>
                    <strong>{formatNumber(calculation.totals[mode]?.value)}</strong>
                    <span className={calculation.totals[mode]?.complete ? "complete" : "incomplete"}>
                      {calculation.totals[mode]?.complete ? "complete" : "partial"}
                    </span>
                  </div>
                ))}
              </div>
              <div className="event-list">
                {calculation.events.map((event) => {
                  const dischargeSummary = dischargeMultiplierSummary(event);
                  const periodicAnomaly = event.damage_type === "anomaly"
                    && event.damage_subtype === "attribute-anomaly"
                    && event.repeat_count > 1;
                  return <article className="event-card" key={event.semantic_id}>
                    <div>
                      <strong>{event.label}</strong>
                      <small>{event.semantic_id} · {event.element ? elementLabel(event.element) : "属性未标注"} · ×{event.repeat_count}</small>
                      {dischargeSummary && <p className="discharge-multiplier-summary">{dischargeSummary}</p>}
                    </div>
                    <div className="event-values">
                      {(event.display_modes ?? ["non-crit", "expected", "full-crit"]).map((mode) => {
                        const modeResult = event.modes[mode];
                        return <span key={mode}>
                          <small>{mode} · {modeResult?.status}{event.repeat_count > 1 ? " · 合计" : ""}</small>
                          <b>{formatNumber(modeResult?.known_value)}</b>
                          {periodicAnomaly && modeResult?.value !== null && modeResult?.value !== undefined
                            && <small className="event-per-tick">每跳 {formatNumber(modeResult.value)}</small>}
                        </span>;
                      })}
                    </div>
                    <details className="event-details">
                      <summary>查看 breakdown</summary>
                      <div className="breakdown-list">
                        {(event.modes.expected?.calculation_breakdown ?? []).map((node) => (
                          <div key={node.node}><span>{calculationNodeLabel(node.node)}</span><b>{formatNumber(node.value)}</b><small>{node.read_rule}</small></div>
                        ))}
                      </div>
                      <AnomalyStrengthDetails event={event} />
                      {event.common_application_trace && <EventTraceDetails
                        trace={event.common_application_trace}
                        rules={allRules}
                        conditions={allConditions}
                        conditionValues={conditionValuesRef.current}
                        enabledRuleIds={enabledRules}
                        formatNumber={formatNumber}
                        isEquipmentSource={isEquipmentSource}
                      />}
                      {Object.entries(event.modes).flatMap(([mode, item]) => item.diagnostics.map((diagnostic, index) => (
                        <p className="inline-diagnostic" key={`${mode}-${index}`}>{mode}: {diagnostic.message}</p>
                      )))}
                    </details>
                  </article>;
                })}
              </div>
              <VivianPanelSourceResults results={(calculation.panel_source_results ?? []).filter(
                (source) => calculation.move_entry_id !== VIVIAN_DISCHARGE_ENTRY_ID || source.source_character_id !== VIVIAN_ID,
              )} />
              {calculation.panel_traces.length > 0 && <details className="trace-list provenance-details">
                <summary><span><span className="eyebrow">PANEL PROVENANCE</span><strong>面板来源明细</strong></span><small>{calculation.panel_traces.length} 项</small></summary>
                {calculation.panel_traces.map((trace) => <div className="trace-row" key={`${trace.effect_id}-${trace.recipient_character_id}`}>
                  <span>{trace.recipient_character_id}</span><strong>+{formatNumber(trace.resolved_value)}</strong>
                  <small>{trace.source_label ?? trace.effect_id} · {trace.modifier_path}</small>
                </div>)}
              </details>}
              {calculation.resolved_character_snapshots.length > 0 && <details className="trace-list provenance-details">
                <summary><span><span className="eyebrow">RESOLVED PANELS</span><strong>结算面板快照</strong></span><small>{calculation.resolved_character_snapshots.length} 名</small></summary>
                {calculation.resolved_character_snapshots.map((snapshot) => <div className="snapshot-row" key={snapshot.character_id}>
                  <strong>{snapshot.character_id}</strong>
                  <span>攻击力 {formatNumber(typeof snapshot.stats.attack === "number" ? snapshot.stats.attack : null)}</span>
                  <span>暴击率 {formatNumber(typeof snapshot.stats.crit_rate === "number" ? snapshot.stats.crit_rate : null)}</span>
                  <span>属性增伤 {formatElementBonus(snapshot.stats.element_damage_bonus, editorViews[snapshot.character_id]?.effective_damage_element ?? characters.find((character) => character.character_id === snapshot.character_id)?.element)}</span>
                </div>)}
              </details>}
              <CalculationDiagnosticList diagnostics={calculation.diagnostics} />
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon">◈</span>
              <strong>{teamIds.length === 0 ? "先配置队伍角色" : "选择招式后开始结算"}</strong>
              <p className="muted">{teamIds.length === 0 ? "请从左侧角色槽位添加至少一名角色。" : "结果、派生事件和白盒说明将由计算内核返回。"}</p>
            </div>
          )}
        </section>
      </section>

      {diagnostics.length > 0 && <section className="diagnostics glass-card"><p className="eyebrow">DIAGNOSTICS</p>{diagnostics.map((message) => <div className="diagnostic" key={message}><strong>API</strong><span>{message}</span></div>)}</section>}
    </main>
  );
}

function dischargeMultiplierSummary(event: CalculationEvent): string | null {
  if (event.damage_subtype !== "discharge") return null;
  const breakdown = event.modes.expected?.calculation_breakdown ?? [];
  const valueFor = (node: string) => breakdown.find((item) => item.node === node)?.value;
  const sourceTickMultiplier = valueFor("anomaly.discharge.original-anomaly-multiplier");
  const dischargeMultiplier = valueFor("discharge.proficiency-multiplier");
  const totalMultiplier = valueFor("anomaly.discharge.total-multiplier");
  if (typeof sourceTickMultiplier !== "number"
    || typeof dischargeMultiplier !== "number"
    || typeof totalMultiplier !== "number"
    || !Number.isFinite(sourceTickMultiplier)
    || !Number.isFinite(dischargeMultiplier)
    || !Number.isFinite(totalMultiplier)) return null;
  return `原异常每跳 ${formatMultiplierPercent(sourceTickMultiplier)} × 异放倍率 ${formatMultiplierPercent(dischargeMultiplier)} = 结算倍率 ${formatMultiplierPercent(totalMultiplier)}`;
}

function CalculationDiagnosticList({
  diagnostics,
}: {
  diagnostics: CalculationDiagnostic[];
}) {
  const unique = [...new Map(
    diagnostics.map((item) => [
      `${item.diagnostic_id ?? ""}:${item.message}:${item.blocking}`,
      item,
    ]),
  ).values()];
  const detailsOnly = unique.filter((item) => !item.blocking && item.details_only === true);
  const visible = unique.filter((item) => !detailsOnly.includes(item));
  if (visible.length === 0 && detailsOnly.length === 0) return null;
  return <>
    {visible.length > 0 && <div className="diagnostic-list">{visible.map((item, index) => <div className="diagnostic" key={`${item.diagnostic_id ?? item.message}-${index}`}><strong>{item.blocking ? "BLOCKED" : "NOTE"}</strong><span>{item.message}</span></div>)}</div>}
    {detailsOnly.length > 0 && <details className="calculation-notes">
      <summary><strong>计算说明</strong><small>{detailsOnly.length} 条</small></summary>
      <div className="calculation-note-list">{detailsOnly.map((item, index) => <article className="calculation-note" key={`${item.diagnostic_id ?? item.message}-${index}`}>
        <strong>{calculationNoteTitle(item.diagnostic_id)}</strong>
        <p>{item.message}</p>
        {item.original_text && <small>来源原文：{item.original_text}</small>}
        {item.candidates && item.candidates.length > 0 && <small>候选：{item.candidates.join("；")}</small>}
      </article>)}</div>
    </details>}
  </>;
}

function calculationNoteTitle(diagnosticId: string | undefined): string {
  return ({
    "unsupported:character:1331:core:prophecy-timing": "预言跳数",
    "unsupported:character:1331:core:feather-resource-sequence": "当前飞羽与护羽状态",
    "wengine:wengine:14133:result-scope": "专武异常精通层数",
  } as Record<string, string>)[diagnosticId ?? ""] ?? "静态计算说明";
}

function VivianPanelSourceResults({ results }: { results: NonNullable<CalculationView["panel_source_results"]> }) {
  if (results.length === 0) return null;
  return <section className="trace-list vivian-panel-source-results">
    <div className="section-heading compact"><div><p className="eyebrow">VIVIAN ANOMALY MUTATION</p><h3>薇薇安异放 · 来源角色面板</h3><p className="control-section-hint">按每名当前上场角色的面板分别结算，不并入上方招式总计。</p></div></div>
    <div className="vivian-panel-source-grid">{results.map((source) => <article className="vivian-panel-source-card" key={`${source.source_character_id}-${source.element}`}>
      <div className="vivian-panel-source-heading"><strong>薇薇安异放 · {source.source_character_name}/{elementLabel(source.element)}</strong><span className={source.totals.expected?.complete ? "complete" : "incomplete"}>{source.totals.expected?.complete ? "complete" : "partial"}</span></div>
      <div className="vivian-panel-source-total"><span>异放合计</span><strong>{formatNumber(source.totals.expected?.value)}</strong></div>
      {source.events.map((event) => <div className="vivian-panel-source-event" key={event.semantic_id}>
        <div className="vivian-panel-source-row"><span>{event.label}</span><strong>{formatNumber(event.modes.expected?.known_value)}</strong></div>
        {dischargeMultiplierSummary(event) && <small className="discharge-multiplier-summary">{dischargeMultiplierSummary(event)}</small>}
      </div>)}
      <CalculationDiagnosticList diagnostics={[
        ...source.diagnostics,
        ...source.events.flatMap((event) => Object.values(event.modes).flatMap((mode) => mode.diagnostics)),
      ]} />
    </article>)}</div>
  </section>;
}

function formatNumber(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 2 }).format(value);
}

function elementLabel(element: string) {
  return ({ physical: "物理", ether: "以太", electric: "电", ice: "冰", fire: "火", wind: "风", "ice:lieshuang": "烈霜", "ether:xuanmo": "玄墨", "physical:linren": "凛刃", luminance: "流明" } as Record<string, string>)[element] ?? element;
}

function specialtyLabel(specialty: string) {
  return ({ attack: "强攻", anomaly: "异常", support: "支援", stun: "击破", rupture: "命破" } as Record<string, string>)[specialty] ?? specialty;
}

function isCharacterProgressField(field: CompileField) {
  return field.field_id === "core_level"
    || field.field_id === "cinema_level"
    || field.field_id.startsWith("skill_level:");
}

type LivePanelProps = {
  teamIds: string[];
  characters: Character[];
  editorViews: Record<string, EditorView | null>;
  previews: Record<string, BuildPreview | null>;
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
  { key: "penetration_force", label: "贯穿力" },
  { key: "energy_regen", label: "能量自动回复" },
];

function LivePanel({ teamIds, characters, editorViews, previews, loading }: LivePanelProps) {
  return <section className="live-panel" aria-label="实时局外面板">
    <div className="section-heading compact live-panel-heading">
      <div><p className="eyebrow">LIVE OUT-OF-COMBAT PANEL</p><h2>实时局外面板</h2><p className="live-panel-subtitle">当前队伍的最终局外属性与来源</p></div>
      <span className={`live-update-status ${loading ? "updating" : "synced"}`} aria-live="polite">{teamIds.length === 0 ? "待配置" : loading ? "更新中…" : "已同步"}</span>
    </div>
    <div className="live-panel-list">
      {teamIds.length === 0
        ? <div className="empty-team-hint">添加角色后显示其局外面板与属性来源。</div>
        : teamIds.map((id, teamIndex) => {
        const preview = previews[id];
        const stats = preview?.out_of_combat_stats;
        const character = characters.find((item) => item.character_id === id);
        const damageElement = editorViews[id]?.effective_damage_element ?? character?.element;
        const status = preview
          ? (preview.complete ? "已解析" : "配置未完成")
          : "等待解析";
        const statusClass = preview?.complete === false ? "incomplete" : preview ? "complete" : "neutral";
        const readStat = (key: string, ratio = false) => {
          const value = numericPreviewStat(stats?.[key]);
          return formatPanelValue(value, ratio);
        };
        const elementValue = stats?.element_damage_bonus;
        return <article className={`live-panel-card live-panel-card-${teamIndex} ${preview?.complete === false ? "live-panel-card-incomplete" : ""}`} key={id}>
          <div className="live-panel-card-heading">
            <div className="live-panel-character">
              {character ? <img alt="" src={character.image_path} style={{ objectPosition: character.image_object_position }} /> : <span className="live-panel-avatar">?</span>}
              <div><strong>{character?.display_name ?? id}</strong><small>{teamIndex === 0 ? "主控角色" : "支援角色"}{damageElement ? ` · ${damageElement}` : ""}</small></div>
            </div>
            <span className={`live-panel-status ${statusClass}`}>{status}</span>
          </div>
          <div className="live-panel-featured-grid">
            <div className="live-panel-stat live-panel-featured-stat"><span>攻击力</span><strong>{readStat("attack")}</strong><small>ATK</small></div>
            <div className="live-panel-stat live-panel-featured-stat"><span>暴击率</span><strong>{readStat("crit_rate", true)}</strong><small>CRIT RATE</small></div>
            <div className="live-panel-stat live-panel-featured-stat"><span>暴击伤害</span><strong>{readStat("crit_damage", true)}</strong><small>CRIT DMG</small></div>
            <div className="live-panel-stat live-panel-featured-stat live-panel-element-bonuses"><span>属性增伤</span><strong>{formatElementBonus(elementValue as Record<string, number | null> | null, damageElement)}</strong><small>ELEMENT BONUS</small></div>
          </div>
          <div className="live-panel-secondary-grid">
            {LIVE_PANEL_STATS.filter(({ key }) => !["attack", "crit_rate", "crit_damage"].includes(key)
              && (key !== "penetration_force" || character?.specialty === "rupture"))
              .map(({ key, label, ratio }) => <div className="live-panel-stat" key={key}><span>{label}</span><strong>{readStat(key, ratio)}</strong></div>)}
          </div>
          <details className="live-panel-provenance">
            <summary><span>来源明细</span><small>{preview ? `${preview.provenance.length} 项装备/基础贡献` : "等待装备构筑解析"}</small></summary>
            <div className="provenance-list">
              {preview ? preview.provenance.map((item) => <div className="provenance-row" key={item.contribution_id}>
                <span>{item.source_label}</span><strong>{formatBuildContributionValue(item)}</strong><small>{item.stat}{item.element ? ` · ${item.element}` : ""}</small>
              </div>) : <div className="provenance-row"><span>角色基础属性</span><strong>等待解析</strong><small>由角色等级与装备构筑生成</small></div>}
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

function formatPanelValue(value: number | "" | undefined, ratio = false) {
  if (value === "" || value === undefined) return "—";
  return ratio ? formatPreviewRatio(value) : formatNumber(value);
}

function formatDriveValue(stat: string, value: number) {
  return formatDriveStatValue(stat, value);
}

function formatElementBonus(value: number | Record<string, number | null> | null, element?: string) {
  if (!value || typeof value !== "object" || !element) return "—";
  const amount = value[element];
  return typeof amount === "number" ? `${formatNumber(amount * 100)}%` : "—";
}

function isEquipmentSource(sourceType: string | null | undefined) {
  return sourceType === "weapon" || sourceType === "drive-disc";
}

function AnomalyStrengthDetails({ event }: { event: CalculationView["events"][number] }) {
  const trace = event.modes.expected?.anomaly_effect_strength_trace;
  const isAnomaly = event.damage_subtype === "attribute-anomaly" || event.damage_type === "disorder";
  if (!isAnomaly) return null;
  if (!trace) {
    return <div className="anomaly-strength-details anomaly-strength-missing"><strong>异常强度来源</strong><span>读取异常记录「{event.modes.expected?.anomaly_record_id ?? event.semantic_id}」，原始因子未提供；当前仅展示记录保存的异常强度数字。</span></div>;
  }
  return <div className="anomaly-strength-details">
    <div className="anomaly-strength-heading"><strong>异常效果强度来源</strong><span>{trace.unresolved ?? "来自实际结算来源"}</span></div>
    {trace.contributor_traces.length > 0
      ? <div className="anomaly-strength-contributors">{trace.contributor_traces.map((item) => <div className="anomaly-strength-contributor" key={`${item.contributor_character_id}-${item.actual_written_buildup}`}><strong>{item.contributor_character_id}</strong><small>实际写入 {formatNumber(item.actual_written_buildup)}</small><AnomalyStrengthFormula trace={item.trace} /></div>)}</div>
      : <AnomalyStrengthFormula trace={trace} />}
  </div>;
}

function AnomalyStrengthFormula({ trace }: { trace: AnomalyEffectStrengthTraceView }) {
  return <div className="anomaly-strength-formula">
    <p>公式：等级系数 × 异常精通/100 × (1 + 对应属性增伤 + 适用普通增伤) × 攻击力 × 异化系数</p>
    <div className="anomaly-strength-values">
      <span><small>角色等级</small><b>{trace.level === null ? "未提供" : `${trace.level}级`}</b></span>
      <span><small>等级系数</small><b>{formatNumber(trace.level_coefficient)}</b></span>
      <span><small>有效异常精通</small><b>{formatNumber(trace.anomaly_proficiency)}</b></span>
      <span><small>精通区</small><b>{formatNumber(trace.anomaly_proficiency_factor)}</b></span>
      <span><small>有效攻击力</small><b>{formatNumber(trace.attack)}</b></span>
      <span><small>对应属性增伤</small><b>{formatRatioOrMissing(trace.element_bonus)}</b></span>
      <span><small>普通增伤区</small><b>{formatRatioOrMissing(trace.normal_bonus)}</b></span>
      <span><small>异化系数</small><b>{formatNumber(trace.mutation)}</b></span>
      <span><small>最终强度</small><b>{formatNumber(trace.final_strength)}</b></span>
    </div>
    {trace.factors.length > 0 && <div className="anomaly-strength-sources">{trace.factors.map((factor, index) => <div className="anomaly-strength-source" key={`${factor.factor}-${factor.source_id ?? index}`}><span>{factor.source_label ?? factor.factor}</span><strong>{factor.value === null ? "未提供" : formatNumber(factor.value)}</strong><small>{factor.owner_character_id ?? factor.source_id ?? "来源未标注"}{factor.unresolved ? ` · ${factor.unresolved}` : ""}</small></div>)}</div>}
  </div>;
}

function formatRatioOrMissing(value: number | null) {
  return value === null ? "未提供" : `${formatNumber(value * 100)}%`;
}

export default App;
