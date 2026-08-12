export type ArchitectureDiagram = {
  id: string;
  title: string;
  description: string;
  mermaid: string;
};

export const architectureDiagrams: ArchitectureDiagram[] = [
  {
    id: "etl",
    title: "Classic ETL Pipeline",
    description:
      "Extract from operational sources, transform with quality gates, and load curated tables for analytics.",
    mermaid: `flowchart LR
  SRC[(Operational DBs / APIs / Files)] --> EXT[Extract]
  EXT --> STG[(Staging)]
  STG --> TR[Transform + Data Quality]
  TR --> DWH[(Analytics Warehouse)]
  DWH --> CONS[BI / Data Science / Products]`,
  },
  {
    id: "lakehouse",
    title: "Lakehouse Medallion Architecture",
    description:
      "Landing, trusted, and curated zones on object storage with a metastore for governed analytics.",
    mermaid: `flowchart TB
  RAW[Raw Events] --> BRONZE[(Landing / Bronze)]
  BRONZE --> SILVER[(Trusted / Silver)]
  SILVER --> GOLD[(Curated / Gold)]
  GOLD --> ML[Feature / ML Tables]
  GOLD --> BI[Semantic Layer & BI]
  CAT[(Glue / Unity Catalog)] --- BRONZE
  CAT --- SILVER
  CAT --- GOLD`,
  },
  {
    id: "warehouse",
    title: "Cloud Data Warehouse",
    description:
      "ELТ into a cloud warehouse with dimensional models optimized for analytical queries.",
    mermaid: `flowchart LR
  S3[(Object Storage)] --> COPY[COPY / LOAD]
  COPY --> STAGING[(Staging Schemas)]
  STAGING --> DIMS[(Dimensions)]
  STAGING --> FACTS[(Facts)]
  DIMS --> MARTS[(Data Marts)]
  FACTS --> MARTS
  MARTS --> DASH[Dashboards & Ad-hoc SQL]`,
  },
  {
    id: "streaming",
    title: "Streaming Pipeline",
    description:
      "Near-real-time ingestion with stream processing and dual publish to serving and analytical stores.",
    mermaid: `flowchart LR
  EV[Producers] --> BUS[(Kafka / Kinesis)]
  BUS --> PROC[Stream Processor]
  PROC --> SERV[(Serving Store)]
  PROC --> LAKE[(Analytical Lake/Warehouse)]
  SERV --> APP[Real-time Apps]
  LAKE --> ANALYTICS[Batch Analytics]`,
  },
  {
    id: "airflow-dag",
    title: "Airflow DAG Pattern",
    description:
      "A dependable DAG shape: extract → validate → transform → load → quality checks.",
    mermaid: `flowchart TD
  T([Schedule / Trigger]) --> E[Extract]
  E --> V[Validate]
  V --> X[Transform]
  X --> L[Load]
  L --> Q[Quality Checks]
  Q -->|success| P([Publish])
  Q -->|failure| A[Alert & Stop]`,
  },
];
