import { useId, useState, type InputHTMLAttributes } from "react";
import DraftNumberInput from "./DraftNumberInput";

export type NumberFieldProps = {
  label: string;
  value: number | null | undefined | "";
  onCommit?: (value: number) => void;
  unit?: string;
  helper?: string;
  error?: string;
  min?: number;
  max?: number;
  integer?: boolean;
  disabled?: boolean;
  readOnly?: boolean;
  /** Display a ratio such as 0.5 as 50%, while continuing to commit 0.5. */
  displayAsPercent?: boolean;
  /** A formatted value for read-only preview fields (for example, "50%"). */
  displayValue?: string;
  className?: string;
  id?: string;
  placeholder?: string;
  inputMode?: InputHTMLAttributes<HTMLInputElement>["inputMode"];
  "aria-label"?: string;
};

function joinClassNames(...names: Array<string | undefined | false>) {
  return names.filter(Boolean).join(" ");
}

/**
 * Shared numeric field chrome for the calculator.
 *
 * The actual editable control stays DraftNumberInput, so clearing a value or
 * typing a decimal intermediate never mutates the authoritative number until
 * blur/Enter. NumberField owns the visual contract: label, unit, helper/error,
 * focus state, read-only state, and a consistent value surface.
 */
export function NumberField({
  label,
  value,
  onCommit,
  unit,
  helper,
  error: externalError,
  min,
  max,
  integer = false,
  disabled = false,
  readOnly = false,
  displayAsPercent = false,
  displayValue,
  className,
  id,
  placeholder,
  inputMode,
  "aria-label": ariaLabel,
}: NumberFieldProps) {
  const generatedId = useId();
  const inputId = id ?? `number-field-${generatedId}`;
  const [focused, setFocused] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const hasError = Boolean(externalError || validationError);
  const isDisplayOnly = disabled || readOnly || displayValue !== undefined;
  const normalizedValue = value === "" ? null : value;
  const scaledValue = displayAsPercent && typeof normalizedValue === "number" ? normalizedValue * 100 : normalizedValue;
  const scaledMin = displayAsPercent && typeof min === "number" ? min * 100 : min;
  const scaledMax = displayAsPercent && typeof max === "number" ? max * 100 : max;
  const describedBy = helper || validationError || externalError
    ? `${inputId}-hint`
    : undefined;

  return (
    <div className={joinClassNames(
      "number-field",
      focused && "number-field-focused",
      hasError && "number-field-invalid",
      disabled && "number-field-disabled",
      readOnly && "number-field-readonly",
      className,
    )}>
      <div className="number-field-heading">
        <label htmlFor={inputId}>{label}</label>
        {unit && <span className="number-field-unit">{unit}</span>}
      </div>
      <div className="number-field-control">
        {isDisplayOnly ? (
          <input
            id={inputId}
            className="number-field-input"
            type="text"
            readOnly
            disabled={disabled}
            value={displayValue ?? (scaledValue === null || scaledValue === undefined ? "" : String(scaledValue))}
            aria-label={ariaLabel ?? label}
            aria-invalid={hasError || undefined}
            aria-describedby={describedBy}
            placeholder={placeholder}
          />
        ) : (
          <DraftNumberInput
            id={inputId}
            className="number-field-input"
            value={scaledValue}
            onCommit={(nextValue) => onCommit?.(displayAsPercent ? nextValue / 100 : nextValue)}
            integer={integer}
            min={scaledMin}
            max={scaledMax}
            disabled={disabled}
            placeholder={placeholder}
            inputMode={inputMode}
            aria-label={ariaLabel ?? label}
            aria-invalid={hasError || undefined}
            aria-describedby={describedBy}
            onFocusChange={setFocused}
            onValidationChange={setValidationError}
          />
        )}
        {!displayValue && unit && <span className="number-field-suffix" aria-hidden="true">{unit}</span>}
      </div>
      {(helper || hasError) && (
        <small id={describedBy} className={joinClassNames("number-field-hint", hasError && "number-field-error-text")}>
          {externalError ?? validationError ?? helper}
        </small>
      )}
    </div>
  );
}

export default NumberField;
