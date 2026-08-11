import type { KPIDelta } from "../types";
import "./KpiCard.css";

interface KpiCardProps {
  label: string;
  value: string;
  delta?: KPIDelta | null;
  invertDelta?: boolean;
  hint?: string;
}

export default function KpiCard({ label, value, delta, invertDelta, hint }: KpiCardProps) {
  const trend = delta && delta.percent !== null ? (delta.percent === 0 ? "flat" : delta.percent > 0 ? "up" : "down") : null;
  const isGood = trend === null ? null : invertDelta ? trend === "down" : trend === "up";

  return (
    <div className="kpi-card">
      <p className="kpi-card__label">{label}</p>
      <p className="kpi-card__value">{value}</p>
      <div className="kpi-card__footer">
        {delta && delta.percent !== null ? (
          <span
            className={`kpi-card__delta kpi-card__delta--${
              trend === "flat" ? "flat" : isGood ? "positive" : "negative"
            }`}
          >
            {trend === "up" ? "▲" : trend === "down" ? "▼" : "•"} {Math.abs(delta.percent).toFixed(1)}%
          </span>
        ) : (
          <span className="kpi-card__delta kpi-card__delta--muted">vs previous —</span>
        )}
        {hint && <span className="kpi-card__hint">{hint}</span>}
      </div>
    </div>
  );
}
