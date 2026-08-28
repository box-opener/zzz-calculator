export type TeamState = {
  primaryId: string;
  supportId: string;
};

export type TeamAction =
  | { type: "select-primary"; characterId: string }
  | { type: "select-support"; characterId: string };

export function teamReducer(state: TeamState, action: TeamAction): TeamState {
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
