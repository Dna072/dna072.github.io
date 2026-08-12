export type SkillCategory = {
  id: string;
  title: string;
  description: string;
  skills: { name: string; level: number }[];
};

export const skillCategories: SkillCategory[] = [
  {
    id: "programming",
    title: "Programming",
    description: "Core languages for data platforms, APIs, and web products.",
    skills: [
      { name: "Python", level: 95 },
      { name: "SQL", level: 95 },
      { name: "TypeScript", level: 88 },
      { name: "JavaScript", level: 90 },
    ],
  },
  {
    id: "fullstack",
    title: "Backend & Frontend (since 2017)",
    description:
      "Full-stack product engineering—APIs, services, and modern UI delivery.",
    skills: [
      { name: "React / ReactJS", level: 90 },
      { name: "Vite", level: 86 },
      { name: "Next.js", level: 88 },
      { name: "Node.js", level: 88 },
      { name: "Express.js", level: 85 },
      { name: "Tailwind CSS", level: 88 },
      { name: "REST APIs", level: 90 },
    ],
  },
  {
    id: "data-engineering",
    title: "Data Engineering",
    description: "Orchestration, processing, and warehouse tooling.",
    skills: [
      { name: "Airflow", level: 90 },
      { name: "Spark", level: 85 },
      { name: "AWS Glue", level: 85 },
      { name: "Redshift", level: 88 },
      { name: "Athena", level: 82 },
      { name: "PostgreSQL", level: 90 },
    ],
  },
  {
    id: "ml",
    title: "Machine Learning & RL",
    description:
      "Applied ML with a strong focus on reinforcement learning research.",
    skills: [
      { name: "Reinforcement Learning", level: 88 },
      { name: "Deep RL", level: 86 },
      { name: "Supervised Learning", level: 82 },
      { name: "Feature Engineering", level: 84 },
    ],
  },
  {
    id: "cloud",
    title: "Cloud & DevOps",
    description: "Cloud platforms and delivery automation.",
    skills: [
      { name: "AWS", level: 88 },
      { name: "Docker", level: 82 },
      { name: "GitHub Actions", level: 85 },
      { name: "CI/CD", level: 84 },
    ],
  },
];

/** Technology radar rings for the skills visualization. */
export const technologyRadar = [
  {
    ring: "Adopt",
    items: [
      "Python",
      "SQL",
      "TypeScript",
      "Node.js",
      "Next.js",
      "Airflow",
      "AWS",
      "PostgreSQL",
    ],
  },
  {
    ring: "Trial",
    items: [
      "Spark",
      "AWS Glue",
      "Deep RL",
      "React",
      "Vite",
      "Express",
      "Tailwind CSS",
      "Redshift",
    ],
  },
  {
    ring: "Assess",
    items: ["Kafka", "Snowflake", "Databricks", "Iceberg", "Multi-agent RL"],
  },
  {
    ring: "Hold",
    items: ["Legacy cron ETL", "Unversioned SQL scripts"],
  },
] as const;
