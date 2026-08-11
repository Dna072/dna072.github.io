interface Props {
  value: number;
}

export function ProgressBar({ value }: Props) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="progress" role="progressbar" aria-valuenow={clamped}>
      <div className="progress__bar" style={{ width: `${clamped}%` }} />
    </div>
  );
}
