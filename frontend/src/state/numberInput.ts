/**
 * Pure state helpers for numeric inputs.
 *
 * HTML number inputs expose a numeric value on every key press.  That makes
 * intermediate edits such as `""`, `"-"`, and `"1."` impossible to represent
 * without accidentally committing zero or another parsed value.  The editor
 * keeps those strings as a draft and only parses them at commit time.
 */

export type NumberDraftState = {
  draft: string;
  committed: number | null;
};

export type NumberDraftOptions = {
  integer?: boolean;
  min?: number;
  max?: number;
};

export type NumberDraftCommit = {
  state: NumberDraftState;
  value: number | null;
  changed: boolean;
};

export function formatNumberDraft(value: number | null | undefined): string {
  return value === null || value === undefined ? "" : String(value);
}

export function createNumberDraftState(value: number | null | undefined): NumberDraftState {
  const committed = value === null || value === undefined ? null : value;
  return { draft: formatNumberDraft(committed), committed };
}

export function updateNumberDraft(
  state: NumberDraftState,
  draft: string,
): NumberDraftState {
  return { ...state, draft };
}

export function syncExternalNumberValue(
  value: number | null | undefined,
): NumberDraftState {
  return createNumberDraftState(value);
}

function isNumericDraft(value: string): boolean {
  // Keep incomplete negative/decimal forms as drafts.  They are intentionally
  // not accepted by commitNumberDraft, but must remain typeable while editing.
  return /^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(value.trim());
}

export function commitNumberDraft(
  state: NumberDraftState,
  options: NumberDraftOptions = {},
): NumberDraftCommit {
  const raw = state.draft.trim();
  if (!raw || !isNumericDraft(raw)) {
    return {
      state: { draft: formatNumberDraft(state.committed), committed: state.committed },
      value: state.committed,
      changed: false,
    };
  }

  const parsed = Number(raw);
  const valid = Number.isFinite(parsed)
    && (!options.integer || Number.isInteger(parsed))
    && (options.min === undefined || parsed >= options.min)
    && (options.max === undefined || parsed <= options.max);
  if (!valid) {
    return {
      state: { draft: formatNumberDraft(state.committed), committed: state.committed },
      value: state.committed,
      changed: false,
    };
  }

  return {
    state: { draft: formatNumberDraft(parsed), committed: parsed },
    value: parsed,
    changed: state.committed !== parsed,
  };
}

export function cancelNumberDraft(state: NumberDraftState): NumberDraftState {
  return { draft: formatNumberDraft(state.committed), committed: state.committed };
}
