"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { timeline, type TimelineItem } from "@/lib/experience";
import { FadeIn } from "@/components/motion/fade-in";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const filters: Array<TimelineItem["type"] | "all"> = [
  "all",
  "work",
  "education",
  "award",
  "publication",
];

export function ExperienceSection() {
  const [filter, setFilter] = useState<(typeof filters)[number]>("all");
  const items =
    filter === "all" ? timeline : timeline.filter((item) => item.type === filter);

  return (
    <section id="experience" className="scroll-mt-24 px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <FadeIn>
          <p className="text-sm font-medium text-brand">Experience</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Career timeline
          </h2>
          <p className="mt-3 max-w-2xl text-muted">
            Interactive view of work, education, awards, and publications.
          </p>
        </FadeIn>

        <div className="mt-8 flex flex-wrap gap-2">
          {filters.map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setFilter(value)}
              className={cn(
                "rounded-lg border px-3 py-1.5 text-xs capitalize transition-colors",
                filter === value
                  ? "border-brand/40 bg-brand/15 text-brand"
                  : "border-white/10 text-muted hover:text-foreground",
              )}
            >
              {value}
            </button>
          ))}
        </div>

        <div className="relative mt-10 space-y-6 before:absolute before:left-[11px] before:top-2 before:h-[calc(100%-1rem)] before:w-px before:bg-white/10 md:before:left-1/2">
          <AnimatePresence mode="popLayout">
            {items.map((item, index) => (
              <motion.article
                key={item.id}
                layout
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.3 }}
                className={cn(
                  "relative grid gap-4 md:grid-cols-2",
                  index % 2 === 0 ? "" : "md:[&>*:first-child]:col-start-2",
                )}
              >
                <div
                  className={cn(
                    "absolute left-[7px] top-5 h-2.5 w-2.5 rounded-full bg-brand md:left-1/2 md:-translate-x-1/2",
                  )}
                />
                <div
                  className={cn(
                    "ml-8 rounded-2xl border border-white/10 bg-white/[0.03] p-5 md:ml-0",
                    index % 2 === 0 ? "md:mr-10" : "md:ml-10",
                  )}
                >
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <Badge variant="secondary" className="capitalize">
                      {item.type}
                    </Badge>
                    <span className="text-xs text-muted">
                      {item.start} — {item.end}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold tracking-tight">
                    {item.role}
                  </h3>
                  <p className="text-sm text-brand">{item.organization}</p>
                  {item.location ? (
                    <p className="mt-1 text-xs text-muted">{item.location}</p>
                  ) : null}
                  <p className="mt-3 text-sm leading-relaxed text-muted">
                    {item.summary}
                  </p>
                  <ul className="mt-3 space-y-1.5 text-sm text-muted">
                    {item.highlights.map((highlight) => (
                      <li key={highlight} className="flex gap-2">
                        <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-brand" />
                        <span>{highlight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </motion.article>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
