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
      "Develop enterprise solutions with Microsoft Power Platform and collaborate with stakeholders to digitize workflows and improve operational reporting.",
    highlights: [
      "Developed enterprise solutions using Microsoft Power Platform (Power Apps, Power Automate, and Power BI).",
      "Built business dashboards and reports supporting operational and risk management decisions.",
      "Automated business processes using Power Automate, reducing manual effort and improving operational efficiency.",
      "Collaborated with business stakeholders to digitize workflows and improve reporting.",
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
      "Designed and deployed production ELT pipelines and a star-schema Redshift warehouse supporting nationwide education analytics for 500,000+ users.",
    highlights: [
      "Built AWS Glue ELT from PostgreSQL into Amazon Redshift for nationwide analytics.",
      "Modeled staging and transformation layers into an analytics-optimized star schema.",
      "Improved Redshift query performance by up to 50% with distribution/sort key tuning and data quality checks.",
      "Contributed to production web platforms including TPG (tpg.ntc.gov.gh) supporting teaching profession workflows.",
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
      "Graduate training in machine learning and data science, culminating in a thesis on deep reinforcement learning for job shop scheduling.",
    highlights: [
      "Thesis: Deep Reinforcement Learning for Job Shop Scheduling (github.com/Dna072/drl-jss).",
      "Built strong foundations in RL, supervised learning, and reproducible experimental workflows.",
      "Combined ML research with practical data engineering and software engineering skills.",
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
      "Undergraduate foundation in computer engineering—beginning continuous backend and frontend software development practice from 2017 onward.",
    highlights: [
      "Built foundations in programming, systems thinking, and software engineering.",
      "Started shipping backend and frontend applications professionally and personally since 2017.",
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
      "Competed in Google Hash Code practice problems, strengthening algorithmic problem-solving under constraints.",
    highlights: [
      "Collaborated on optimization-style engineering challenges.",
      "Published practice repository documenting approaches and learnings.",
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
      "Published project documentation and repositories covering data pipelines, warehouse modeling, and lakehouse analytics.",
    highlights: [
      "Documented Sparkify Redshift warehouse and Airflow orchestration patterns.",
      "Published STEDI lakehouse analytics architecture on AWS Glue / Athena / S3.",
    ],
  },
];
