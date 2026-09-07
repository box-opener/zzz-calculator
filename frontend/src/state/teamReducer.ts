/**
 * The browser team is intentionally kept independent from the calculation
 * request shape. `teamCharacterIds` is the stable UI order while
 * `currentOperatorId` is the character whose move is being calculated.
 */
export type TeamState = {
  teamCharacterIds: string[];
  currentOperatorId: string;
};

/**
 * The legacy shape is accepted by the reducer for one release so consumers
 * which still hydrate an old draft do not crash. App itself only uses the
 * data-driven TeamState above.
 */
type LegacyTeamState = {
  primaryId: string;
  supportId: string;
};

export type TeamAction =
  | { type: "add-character" | "add"; characterId: string }
  | { type: "replace-character" | "replace"; slotIndex?: number; slot?: number; index?: number; characterId: string }
  | { type: "remove-character" | "remove"; characterId: string }
  | { type: "set-current-operator" | "set-operator"; characterId: string }
  // Kept as a migration bridge for saved clients and the pre-library reducer.
  | { type: "select-primary"; characterId: string }
  | { type: "select-support"; characterId: string };

type LegacyAction =
  | { type: "select-primary"; characterId: string }
  | { type: "select-support"; characterId: string };

export function createTeamState(
  characterIds: readonly string[],
  currentOperatorId = characterIds[0] ?? "",
): TeamState {
  const unique = characterIds.filter((id, index) => Boolean(id) && characterIds.indexOf(id) === index).slice(0, 3);
  const ids = unique.length > 0 ? unique : [currentOperatorId].filter(Boolean);
  if (ids.length === 0) {
    throw new Error("a team must contain at least one character");
  }
  const operator = ids.includes(currentOperatorId) ? currentOperatorId : ids[0] ?? "";
  return { teamCharacterIds: ids, currentOperatorId: operator };
}

export function calculationTeamOrder(
  teamCharacterIds: readonly string[],
  currentOperatorId: string,
): {
  primaryCharacterId: string;
  supportingCharacterIds: string[];
  teamCharacterIds: string[];
} {
  if (
    teamCharacterIds.length < 1
    || teamCharacterIds.length > 3
    || new Set(teamCharacterIds).size !== teamCharacterIds.length
    || !currentOperatorId
    || !teamCharacterIds.includes(currentOperatorId)
  ) {
    throw new Error("current operator must be a team member");
  }
  const supportingCharacterIds = teamCharacterIds.filter((id) => id !== currentOperatorId);
  return {
    primaryCharacterId: currentOperatorId,
    supportingCharacterIds,
    teamCharacterIds: [currentOperatorId, ...supportingCharacterIds],
  };
}

function isLegacyState(state: TeamState | LegacyTeamState): state is LegacyTeamState {
  return "primaryId" in state;
}

function slotFromAction(action: Extract<TeamAction, { type: "replace-character" | "replace" }>) {
  const slot = action.slotIndex ?? action.slot ?? action.index;
  return typeof slot === "number" && Number.isInteger(slot) ? slot : -1;
}

function reduceTeamState(state: TeamState, action: TeamAction): TeamState {
  const ids = state.teamCharacterIds;
  switch (action.type) {
    case "add-character":
    case "add": {
      if (!action.characterId || ids.includes(action.characterId) || ids.length >= 3) return state;
      return { ...state, teamCharacterIds: [...ids, action.characterId] };
    }
    case "replace-character":
    case "replace": {
      const slot = slotFromAction(action);
      if (
        slot < 0
        || slot >= ids.length
        || !action.characterId
        || ids.includes(action.characterId)
      ) return state;
      const nextIds = [...ids];
      const replacedId = nextIds[slot];
      nextIds[slot] = action.characterId;
      return {
        teamCharacterIds: nextIds,
        // Replacing the operator slot promotes the replacement consistently;
        // replacing a support slot leaves the active operator untouched.
        currentOperatorId: state.currentOperatorId === replacedId
          ? action.characterId
          : state.currentOperatorId,
      };
    }
    case "remove-character":
    case "remove": {
      if (ids.length <= 1 || !ids.includes(action.characterId)) return state;
      const nextIds = ids.filter((id) => id !== action.characterId);
      return {
        teamCharacterIds: nextIds,
        currentOperatorId: state.currentOperatorId === action.characterId
          ? nextIds[0]
          : state.currentOperatorId,
      };
    }
    case "set-current-operator":
    case "set-operator":
      return ids.includes(action.characterId) && action.characterId !== state.currentOperatorId
        ? { ...state, currentOperatorId: action.characterId }
        : state;
    case "select-primary":
    case "select-support":
      // These actions are only meaningful for the legacy shape. Treat them
      // as no-ops when accidentally dispatched against the new state.
      return state;
    default:
      return state;
  }
}

function reduceLegacyState(state: LegacyTeamState, action: LegacyAction): LegacyTeamState {
  if (action.type === "select-primary") {
    if (action.characterId === state.supportId) {
      return { primaryId: action.characterId, supportId: state.primaryId };
    }
    return { primaryId: action.characterId, supportId: state.supportId };
  }
  if (action.characterId === state.primaryId) {
    return state;
  }
  return { ...state, supportId: action.characterId };
}

export function teamReducer(state: LegacyTeamState, action: LegacyAction): LegacyTeamState;
export function teamReducer(state: TeamState, action: TeamAction): TeamState;
export function teamReducer(
  state: TeamState | LegacyTeamState,
  action: TeamAction,
): TeamState | LegacyTeamState {
  return isLegacyState(state)
    ? reduceLegacyState(state, action as LegacyAction)
    : reduceTeamState(state, action);
}
