interface Props {
  status: string;
  kind?: string;
}

export function StatusBadge({ status, kind }: Props) {
  return (
    <span className={`badge badge-${status}`} title={kind}>
      <span className="dot" />
      {status}
    </span>
  );
}
