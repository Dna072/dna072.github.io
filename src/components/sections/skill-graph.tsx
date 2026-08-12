"use client";

import { motion } from "framer-motion";

const nodes = [
  { label: "Python", x: 50, y: 16, r: 28 },
  { label: "TypeScript", x: 78, y: 32, r: 24 },
  { label: "SQL", x: 22, y: 34, r: 24 },
  { label: "React", x: 12, y: 58, r: 20 },
  { label: "Vite", x: 30, y: 78, r: 18 },
  { label: "Airflow", x: 48, y: 70, r: 20 },
  { label: "Deep RL", x: 70, y: 74, r: 20 },
  { label: "Node.js", x: 88, y: 56, r: 20 },
];

export function SkillGraph() {
  return (
    <div className="relative aspect-[16/11] w-full overflow-hidden rounded-xl border border-white/10 bg-gradient-to-b from-brand/10 to-transparent">
      <svg viewBox="0 0 100 100" className="h-full w-full" role="img" aria-label="Skill graph">
        <motion.path
          d="M50 16 L78 32 L88 56 L70 74 L48 70 L30 78 L12 58 L22 34 Z"
          fill="rgba(29,185,84,0.08)"
          stroke="rgba(29,185,84,0.35)"
          strokeWidth="0.4"
          initial={{ pathLength: 0, opacity: 0 }}
          whileInView={{ pathLength: 1, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
        {nodes.map((node, index) => (
          <g key={node.label}>
            <motion.circle
              cx={node.x}
              cy={node.y}
              r={node.r / 8}
              fill="rgba(29,185,84,0.85)"
              initial={{ scale: 0, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 * index, duration: 0.4 }}
            />
            <text
              x={node.x}
              y={node.y - node.r / 6}
              textAnchor="middle"
              className="fill-foreground text-[3px]"
            >
              {node.label}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
