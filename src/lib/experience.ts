export type TimelineItem = {
  id: string;
  type: "work" | "education" | "award" | "publication";
  organization: string;
  role: string;
  location?: string;
  start: string;
  end: string;
  summary: string;
  highlights: string[];
};

export const timeline: TimelineItem[] = [
  {
    id: "kpmg",
    type: "work",
    organization: "KPMG Sweden",
    role: "System Specialist – Data & Process Automation",
    location: "Stockholm, Sweden",
    start: "2023",
    end: "Present",
    summary:
      "Enterprise Power Platform solutions that digitize workflows and improve operational reporting.",
    highlights: [
      "Built apps, automations, and Power BI dashboards for risk and operations.",
      "Reduced manual work by automating recurring business processes.",
    ],
  },
  {
    id: "ntc",
    type: "work",
    organization: "National Teaching Council",
    role: "Data Engineer (Contract)",
    location: "Greater Accra, Ghana",
    start: "2022",
    end: "2025",
    summary:
      "Production ELT pipelines and a Redshift warehouse for nationwide education analytics (500,000+ users).",
    highlights: [
      "AWS Glue ELT from PostgreSQL into a star-schema Redshift model.",
      "Cut query times by up to 50% with sort/dist keys and data quality checks.",
      "Shipped production web work on TPG (tpg.ntc.gov.gh).",
    ],
  },
  {
    id: "msc",
    type: "education",
    organization: "Uppsala University",
    role: "MSc Data Science",
    location: "Uppsala, Sweden",
    start: "2022",
    end: "2024",
    summary:
      "Graduate focus on machine learning, with a thesis on deep RL for job shop scheduling.",
    highlights: [
      "Thesis: Deep RL for Job Shop Scheduling (github.com/Dna072/drl-jss).",
      "Strengthened RL, supervised learning, and reproducible experiment workflows.",
    ],
  },
  {
    id: "bsc",
    type: "education",
    organization: "University of Ghana",
    role: "BSc Computer Engineering",
    location: "Accra, Ghana",
    start: "2013",
    end: "2017",
    summary:
      "Computer engineering foundation; continuous backend and frontend practice since 2017.",
    highlights: [
      "Core training in programming, systems, and software engineering.",
    ],
  },
  {
    id: "award-hashcode",
    type: "award",
    organization: "Google Hash Code",
    role: "Participant — Practice & Contests",
    start: "2016",
    end: "2016",
    summary:
      "Google Hash Code practice rounds focused on constrained optimization problems.",
    highlights: [
      "Team problem-solving on algorithmic engineering challenges.",
    ],
  },
  {
    id: "pub-ml",
    type: "publication",
    organization: "Applied Data Engineering Projects",
    role: "Technical Write-ups & Repositories",
    start: "Ongoing",
    end: "Present",
    summary:
      "Public docs and repos on data pipelines, warehouse modeling, and lakehouse analytics.",
    highlights: [
      "Sparkify Redshift + Airflow patterns; STEDI lakehouse on Glue / Athena / S3.",
    ],
  },
];
