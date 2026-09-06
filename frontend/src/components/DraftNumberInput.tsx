import { useEffect, useRef, useState, type InputHTMLAttributes } from "react";
import {
  cancelNumberDraft,
  commitNumberDraft,
  createNumberDraftState,
  syncExternalNumberValue,
  updateNumberDraft,
  type NumberDraftOptions,
  type NumberDraftState,
} from "../state/numberInput";

export type DraftNumberInputProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "value" | "defaultValue" | "onChange" | "onBlur" | "onKeyDown" | "type"
> & NumberDraftOptions & {
  value: number | null | undefined;
  onCommit: (value: number) => void;
  /** Called when the input receives or leaves focus. Useful for a visual field wrapper. */
  onFocusChange?: (focused: boolean) => void;
  /** Called after a commit attempt with a human-readable validation message. */
  onValidationChange?: (message: string | null) => void;
};

/**
 * Numeric text input with a string draft and commit-on-blur/Enter semantics.
 * Escape restores the last committed value.  Out-of-range and incomplete
 * drafts are rejected on commit and restored, so formal editor state never
 * receives a transient zero or an invalid number.
 */
export function DraftNumberInput({
  value,
  onCommit,
  integer = false,
  min,
  max,
  inputMode,
  onFocusChange,
  onValidationChange,
  ...inputProps
}: DraftNumberInputProps) {
  const normalizedExternalValue = value === null || value === undefined ? null : value;
  const [state, setState] = useState<NumberDraftState>(() => createNumberDraftState(normalizedExternalValue));
  const stateRef = useRef(state);
  const externalValueRef = useRef<number | null>(normalizedExternalValue);

  const replaceState = (next: NumberDraftState) => {
    stateRef.current = next;
    setState(next);
  };

  useEffect(() => {
    if (externalValueRef.current === normalizedExternalValue) return;
    externalValueRef.current = normalizedExternalValue;
    replaceState(syncExternalNumberValue(normalizedExternalValue));
  }, [normalizedExternalValue]);

  const commit = () => {
    const result = commitNumberDraft(stateRef.current, { integer, min, max });
    const attemptedDraft = stateRef.current.draft.trim();
    const parsedAttempt = Number(attemptedDraft);
    const validAttempt = Boolean(attemptedDraft)
      && /^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(attemptedDraft)
      && Number.isFinite(parsedAttempt)
      && (!integer || Number.isInteger(parsedAttempt))
      && (min === undefined || parsedAttempt >= min)
      && (max === undefined || parsedAttempt <= max);
    if (attemptedDraft && !validAttempt) {
      onValidationChange?.(
        integer
          ? "请输入范围内的整数"
          : "请输入范围内的数字",
      );
    } else {
      onValidationChange?.(null);
    }
    replaceState(result.state);
    if (result.changed && result.value !== null) onCommit(result.value);
  };

  const cancel = () => {
    onValidationChange?.(null);
    replaceState(cancelNumberDraft(stateRef.current));
  };

  return (
    <input
      {...inputProps}
      type="text"
      inputMode={inputMode ?? (integer ? "numeric" : "decimal")}
      min={min}
      max={max}
      value={state.draft}
      onChange={(event) => replaceState(updateNumberDraft(stateRef.current, event.target.value))}
      onFocus={() => onFocusChange?.(true)}
      onBlur={() => {
        commit();
        onFocusChange?.(false);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          commit();
          event.currentTarget.blur();
        } else if (event.key === "Escape") {
          event.preventDefault();
          cancel();
          event.currentTarget.blur();
        }
      }}
    />
  );
}

export default DraftNumberInput;
