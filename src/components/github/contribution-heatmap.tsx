"use client";

import type { ContributionDay } from "@/lib/github";
import { cn } from "@/lib/utils";

export function ContributionHeatmap({ days }: { days: ContributionDay[] }) {
  const weeks: ContributionDay[][] = [];
  for (let i = 0; i < days.length; i += 7) {
    weeks.push(days.slice(i, i + 7));
  }

  return (
    <div className="overflow-x-auto">
      <div className="inline-flex min-w-full gap-[3px] pb-2">
        {weeks.map((week, weekIndex) => (
          <div key={weekIndex} className="flex flex-col gap-[3px]">
            {week.map((day) => (
              <div
                key={day.date}
                title={`${day.date}: ${day.count} contributions`}
                className={cn("heatmap-cell", `heatmap-${day.level}`)}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center gap-2 text-xs text-muted">
        <span>Less</span>
        {[0, 1, 2, 3, 4].map((level) => (
          <span key={level} className={cn("heatmap-cell", `heatmap-${level}`)} />
        ))}
        <span>More</span>
      </div>
    </div>
  );
}
