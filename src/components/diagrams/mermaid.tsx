"use client";

import { useEffect, useId, useState } from "react";
import mermaid from "mermaid";

let mermaidReady = false;

function ensureMermaid() {
  if (mermaidReady) return;
  mermaid.initialize({
    startOnLoad: false,
    theme: "dark",
    securityLevel: "loose",
    fontFamily: "inherit",
  });
  mermaidReady = true;
}

export function MermaidDiagram({
  chart,
  className,
}: {
  chart: string;
  className?: string;
}) {
  const id = useId().replace(/:/g, "");
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    ensureMermaid();
    mermaid
      .render(`mermaid-${id}`, chart)
      .then(({ svg: rendered }) => {
        if (active) {
          setSvg(rendered);
          setError(null);
        }
      })
      .catch((err: Error) => {
        if (active) setError(err.message);
      });
    return () => {
      active = false;
    };
  }, [chart, id]);

  if (error) {
    return (
      <pre className="overflow-auto rounded-xl border border-white/10 bg-white/[0.03] p-4 text-xs text-muted">
        {chart}
      </pre>
    );
  }

  return (
    <div
      className={className}
      dangerouslySetInnerHTML={svg ? { __html: svg } : undefined}
      aria-label="Architecture diagram"
    />
  );
}
