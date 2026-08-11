import type { ReferrerBreakdown } from "../types";
import "./ReferrerList.css";

const REFERRER_LABELS: Record<string, string> = {
  search: "Search",
  social: "Social",
  direct: "Direct",
  email: "Email",
  embed: "Embed",
  recommendation: "Recommended",
};

export default function ReferrerList({ referrers }: { referrers: ReferrerBreakdown[] }) {
  const max = Math.max(...referrers.map((r) => r.share_percent), 1);
  return (
    <ul className="referrer-list">
      {referrers.map((r) => (
        <li key={r.referrer_source} className="referrer-list__row">
          <span className="referrer-list__label">{REFERRER_LABELS[r.referrer_source] ?? r.referrer_source}</span>
          <div className="referrer-list__track">
            <div className="referrer-list__fill" style={{ width: `${(r.share_percent / max) * 100}%` }} />
          </div>
          <span className="referrer-list__value">{r.share_percent.toFixed(1)}%</span>
        </li>
      ))}
    </ul>
  );
}
