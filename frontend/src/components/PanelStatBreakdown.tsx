import { formatPreviewNumber } from "../state/buildPreview";

export type PanelStatBreakdownValue = {
  white_value: number | null;
  additional_value: number | null;
};

export default function PanelStatBreakdown({ value }: { value: PanelStatBreakdownValue | undefined }) {
  if (!value) return null;
  const additional = value.additional_value;
  return <small className="live-panel-breakdown">
    <span>白值 {formatPreviewNumber(value.white_value)}</span>
    <span className="live-panel-additional">附加 {additional !== null && additional >= 0 ? "+" : ""}{formatPreviewNumber(additional)}</span>
  </small>;
}
