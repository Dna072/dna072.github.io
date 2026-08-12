export type SkillCategory = {
  id: string;
  title: string;
  description: string;
  skills: string[];
};

export const skillCategories: SkillCategory[] = [
  {
    id: "programming",
    title: "Programming",
    description: "Core languages for data platforms, APIs, and web products.",
    skills: ["Python", "SQL", "TypeScript", "JavaScript"],
  },
  {
    id: "fullstack",
    title: "Backend & Frontend (since 2017)",
    description:
      "Full-stack product engineering—APIs, services, and modern UI delivery.",
    skills: [
      "React / ReactJS",
      "Vite",
      "Next.js",
      "Node.js",
      "Express.js",
      "Tailwind CSS",
      "REST APIs",
    ],
  },
  {
    id: "data-engineering",
    title: "Data Engineering",
    description: "Orchestration, processing, and warehouse tooling.",
    skills: [
      "Airflow",
      "Spark",
      "AWS Glue",
      "Redshift",
      "Athena",
      "PostgreSQL",
    ],
  },
  {
    id: "ml",
    title: "Machine Learning & RL",
    description:
      "Applied ML with a strong focus on reinforcement learning research.",
    skills: [
      "Reinforcement Learning",
      "Deep RL",
      "Supervised Learning",
      "Feature Engineering",
    ],
  },
  {
    id: "cloud",
    title: "Cloud & DevOps",
    description: "Cloud platforms and delivery automation.",
    skills: ["AWS", "Docker", "GitHub Actions", "CI/CD"],
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
