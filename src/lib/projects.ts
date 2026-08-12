export type ProjectDetail = {
  slug: string;
  title: string;
  tagline: string;
  businessProblem: string;
  solution: string;
  techStack: string[];
  dataModel: string;
  lessons: string[];
  architectureMermaid: string;
  pipelineMermaid: string;
  screenshots: { src: string; alt: string }[];
  liveDemo?: string;
};

/**
 * Enrichment content for featured repositories.
 * Future repos tagged with the "featured" GitHub topic still appear in listings;
 * add a matching entry here for a full case-study page.
 */
export const projectDetails: Record<string, ProjectDetail> = {
  clipforge: {
    slug: "clipforge",
    title: "ClipForge",
    tagline:
      "AI video processing & content intelligence — production-style media/video SaaS portfolio project.",
    businessProblem:
      "Creative teams need more than raw file storage: after upload, videos should be processed asynchronously—thumbnails, audio, transcripts, and AI-derived summaries/chapters/tags—without blocking API requests or the UI.",
    solution:
      "ClipForge accepts uploads, persists metadata, enqueues processing jobs on Redis, and runs workers that orchestrate FFmpeg plus an AI provider abstraction (OpenAI + MockAI). The React dashboard shows library state, job progress, transcripts, and AI outputs.",
    techStack: [
      "Python",
      "FastAPI",
      "React",
      "TypeScript",
      "PostgreSQL",
      "Redis",
      "FFmpeg",
      "Docker",
      "AI / OpenAI",
    ],
    dataModel:
      "Workspaces and users own video assets with processing job state. Pipeline stages persist thumbnails, audio extracts, transcripts, and AI outputs (summary, chapters, tags) against each video record.",
    lessons: [
      "Media products live or die on queue design, observable workers, and honest UI states—not on wrapping a single model call.",
      "Abstraction boundaries around AI and FFmpeg keep the system testable and demoable without API keys.",
      "Idempotent processing steps and clear job status transitions matter as much as the model quality.",
    ],
    architectureMermaid: `flowchart LR
  UI[React Dashboard] --> API[FastAPI]
  API --> DB[(PostgreSQL)]
  API --> Q[(Redis Queue)]
  Q --> W[Workers]
  W --> FF[FFmpeg]
  W --> AI[AIProvider]
  AI --> OAI[OpenAI]
  AI --> MOCK[MockAI]
  W --> DB
  API --> OBJ[(Object Storage)]`,
    pipelineMermaid: `flowchart TD
  upload[Upload video] --> meta[Store metadata + object]
  meta --> enqueue[Enqueue Redis job]
  enqueue --> probe[ffprobe]
  probe --> thumbs[Thumbnails]
  thumbs --> audio[Audio extract]
  audio --> transcript[Transcript]
  transcript --> ai[AI summary / chapters / tags]
  ai --> persist[Persist results]
  persist --> ui[Dashboard status updates]`,
    screenshots: [
      {
        src: "/images/projects/clipforge-cover.svg",
        alt: "ClipForge AI video pipeline architecture illustration",
      },
    ],
  },
  mediavault: {
    slug: "mediavault",
    title: "MediaVault",
    tagline:
      "Video asset management SaaS with RBAC, FTS, and signed downloads — portfolio DAM.",
    businessProblem:
      "Teams accumulate media quickly. Without workspaces, folders, tags, and permissions, assets become unsearchable and unsafe to share.",
    solution:
      "Versioned FastAPI (/api/v1) with JWT auth, workspace membership roles (ADMIN / MEMBER / VIEWER), folder trees, tagged assets, full-text search, pagination, and signed download URLs—backed by a React DAM-style UI.",
    techStack: [
      "Python",
      "FastAPI",
      "React",
      "TypeScript",
      "PostgreSQL",
      "JWT",
      "Docker",
    ],
    dataModel:
      "Workspaces with membership RBAC; folder trees; tagged assets; indexes and PostgreSQL full-text search for library query patterns; object storage abstraction with signed URLs.",
    lessons: [
      "Asset products are permission products—RBAC must be consistent across list, detail, and share endpoints.",
      "Clean schema and index choices matter as much as UI polish when libraries grow.",
      "Signed URLs beat forever-public object paths for controlled sharing.",
    ],
    architectureMermaid: `flowchart LR
  SPA[React SPA] --> API[FastAPI /api/v1]
  API --> AUTH[JWT Auth + RBAC]
  API --> PG[(PostgreSQL + FTS)]
  API --> STORE[Object storage]
  STORE --> SIGN[Signed URLs]`,
    pipelineMermaid: `flowchart TD
  login[Authenticate] --> ws[Select workspace]
  ws --> upload[Upload / organize assets]
  upload --> tags[Folders + tags]
  tags --> search[Search / filter / paginate]
  search --> share[Share with permission checks]
  share --> download[Signed download URL]`,
    screenshots: [
      {
        src: "/images/projects/mediavault-cover.svg",
        alt: "MediaVault DAM architecture illustration",
      },
    ],
  },
  streampulse: {
    slug: "streampulse",
    title: "StreamPulse",
    tagline:
      "SQL-backed video analytics APIs and a live React dashboard — media/video SaaS portfolio project.",
    businessProblem:
      "Product and content teams need trustworthy views of watch time, completion, audience, and device/geo mix—with filters and comparison periods that stay responsive.",
    solution:
      "FastAPI metrics endpoints over PostgreSQL event data, seeded with realistic demo history. React dashboard renders KPIs, time series, funnels, and breakdowns from those APIs, with loading/error/empty states.",
    techStack: [
      "Python",
      "FastAPI",
      "React",
      "TypeScript",
      "PostgreSQL",
      "Recharts",
      "Docker",
    ],
    dataModel:
      "Event-level watch data aggregated into KPI, time-series, funnel, and breakdown queries. Indexes support date-range and video filters used by the dashboard.",
    lessons: [
      "Analytics UX quality tracks query design—indexes and honest loading states beat decorative charts with fake numbers.",
      "Comparison periods and filters belong in the API contract, not only in chart chrome.",
      "Seeded demo data makes the product reviewable without production traffic.",
    ],
    architectureMermaid: `flowchart LR
  Dash[React + Recharts] --> API[FastAPI metrics]
  API --> PG[(PostgreSQL events)]
  Seed[Demo seed] --> PG`,
    pipelineMermaid: `flowchart TD
  seed[Seed demo events] --> agg[Aggregate metrics SQL]
  agg --> kpi[Overview KPIs]
  agg --> ts[Time series]
  agg --> funnel[Engagement funnel]
  agg --> brk[Geo / device breakdowns]
  kpi --> ui[Dashboard]
  ts --> ui
  funnel --> ui
  brk --> ui`,
    screenshots: [
      {
        src: "/images/projects/streampulse-cover.svg",
        alt: "StreamPulse analytics architecture illustration",
      },
    ],
  },
  renderflow: {
    slug: "renderflow",
    title: "RenderFlow",
    tagline:
      "Distributed render/transcode job queue with workers, retries, and Kubernetes manifests.",
    businessProblem:
      "Transcoding and related FFmpeg work must run off the request path, survive failures, and scale horizontally—with operators able to inspect and retry jobs.",
    solution:
      "FastAPI accepts jobs; Redis backs the queue; workers claim work with heartbeats, retries, and idempotency keys; results land in object storage. Ops UI lists jobs/workers; Compose + Kubernetes manifests encode the deployment shape. Mock processing when media paths are absent keeps demos reliable.",
    techStack: [
      "Python",
      "FastAPI",
      "React",
      "TypeScript",
      "PostgreSQL",
      "Redis",
      "FFmpeg",
      "Docker",
      "Kubernetes",
    ],
    dataModel:
      "Jobs with type, status, priority, retries, errors, and idempotency keys; worker heartbeats; outputs in object storage for transcode, thumbnail, audio extract, and metadata tasks.",
    lessons: [
      "Distributed media work is operations work: heartbeats, retries, and probes are product features for reliability—not afterthoughts.",
      "Idempotency keys prevent duplicate side effects when workers retry.",
      "Kubernetes probes and HPA only help if the app exposes honest health/ready signals.",
    ],
    architectureMermaid: `flowchart LR
  UI[Ops UI] --> API[FastAPI]
  API --> PG[(PostgreSQL)]
  API --> Q[(Redis)]
  Q --> W1[Worker]
  Q --> W2[Worker]
  W1 --> FF[FFmpeg / Mock]
  W2 --> FF
  W1 --> OBJ[(Object Storage)]
  W2 --> OBJ
  K8s[K8s manifests] -.-> API
  K8s -.-> W1`,
    pipelineMermaid: `flowchart TD
  enqueue[Enqueue job] --> claim[Worker claim + heartbeat]
  claim --> run[Process media step]
  run -->|success| store[Store output + complete]
  run -->|failure| retry[Retry / dead-letter]
  retry --> claim
  store --> ops[Ops UI inspect]`,
    screenshots: [
      {
        src: "/images/projects/renderflow-cover.svg",
        alt: "RenderFlow distributed job queue illustration",
      },
    ],
  },
  "airflow-pipelines": {
    slug: "airflow-pipelines",
    title: "Airflow Pipelines",
    tagline: "Production-style orchestration for repeatable data workflows.",
    businessProblem:
      "Manual and ad-hoc data jobs are fragile—hard to monitor, difficult to backfill, and risky to change. Teams need scheduled, observable pipelines with clear dependencies.",
    solution:
      "Built Apache Airflow DAGs that automate extract/transform/load stages with modular operators, retry policies, and explicit task dependencies so pipelines are testable and operable.",
    techStack: ["Apache Airflow", "Python", "SQL", "AWS", "Docker"],
    dataModel:
      "Staging → curated analytical tables with task-level ownership. Each DAG stage isolates ingestion, transformation, and quality validation.",
    lessons: [
      "Idempotent tasks and clear retry boundaries matter more than clever DAG graphs.",
      "Custom operators pay off when the same S3/warehouse patterns repeat.",
      "Observability (logs, SLAs, failure alerts) is part of the data product.",
    ],
    architectureMermaid: `flowchart LR
  A[Source Systems] --> B[Airflow Scheduler]
  B --> C[Extract Tasks]
  C --> D[Transform Tasks]
  D --> E[Load / Publish]
  E --> F[Analytics Consumers]
  B --> G[Monitoring & Alerts]`,
    pipelineMermaid: `flowchart TD
  start([DAG Trigger]) --> extract[Extract raw data]
  extract --> validate[Validate schema & volume]
  validate --> transform[Transform & enrich]
  transform --> load[Load curated tables]
  load --> dq[Data quality checks]
  dq -->|pass| done([Publish ready datasets])
  dq -->|fail| alert[Fail task & alert]`,
    screenshots: [
      {
        src: "/images/projects/airflow-pipelines-cover.svg",
        alt: "Airflow pipelines architecture illustration",
      },
    ],
  },
  sparkify_dwh_aws_redshift: {
    slug: "sparkify_dwh_aws_redshift",
    title: "Sparkify Data Warehouse on AWS Redshift",
    tagline: "S3 → Redshift ETL for music streaming analytics.",
    businessProblem:
      "Sparkify needed a warehouse that turns song play logs and song metadata into an analytical star schema so the analytics team can answer product questions quickly.",
    solution:
      "Implemented an ETL pipeline that stages JSON data from S3 into Amazon Redshift, then loads fact and dimension tables optimized for song-play analytics.",
    techStack: ["Python", "Amazon Redshift", "Amazon S3", "SQL", "ETL"],
    dataModel:
      "Star schema centered on songplays fact table with dimensions for users, songs, artists, and time—supporting common analytics queries with clean joins.",
    lessons: [
      "Staging tables simplify debugging COPY failures from S3.",
      "Careful distribution/sort key choices improve Redshift query performance.",
      "Fact/dimension separation keeps analytics SQL readable and trustworthy.",
    ],
    architectureMermaid: `flowchart LR
  S3[(Amazon S3 JSON logs)] --> ETL[Python ETL]
  ETL --> STG[(Redshift Staging)]
  STG --> DIM[(Dimension Tables)]
  STG --> FACT[(Songplays Fact)]
  FACT --> BI[Analytics Queries]
  DIM --> BI`,
    pipelineMermaid: `flowchart TD
  a[Create tables] --> b[Copy song data to staging]
  a --> c[Copy log data to staging]
  b --> d[Load artists & songs dims]
  c --> e[Load users & time dims]
  d --> f[Load songplays fact]
  e --> f
  f --> g[Run analytical validation queries]`,
    screenshots: [
      {
        src: "/images/projects/sparkify-cover.svg",
        alt: "Sparkify Redshift warehouse illustration",
      },
    ],
  },
  "stedi-human-balance-analytics": {
    slug: "stedi-human-balance-analytics",
    title: "STEDI Human Balance Analytics",
    tagline: "AWS lakehouse for privacy-aware sensor analytics.",
    businessProblem:
      "STEDI collects customer, accelerometer, and step-trainer sensor data that must be sanitized, joined, and curated into a lakehouse suitable for machine learning—while respecting privacy consent.",
    solution:
      "Built a landing → trusted → curated lakehouse on AWS using S3, Glue jobs, and Athena so only consented, high-quality records reach the ML-ready curated zone.",
    techStack: ["AWS Glue", "Amazon S3", "Athena", "Spark", "Python", "SQL"],
    dataModel:
      "Medallion-style zones: landing (raw), trusted (cleaned/consented), curated (joined ML features). Customer consent gates accelerometer and step-trainer joins.",
    lessons: [
      "Consent filters belong early in the pipeline, not at query time.",
      "Glue Data Catalog + Athena makes lakehouse datasets discoverable.",
      "Clear zone boundaries (landing/trusted/curated) improve governance.",
    ],
    architectureMermaid: `flowchart TB
  subgraph Landing
    C1[Customer Landing]
    A1[Accelerometer Landing]
    S1[Step Trainer Landing]
  end
  subgraph Trusted
    C2[Customer Trusted]
    A2[Accelerometer Trusted]
    S2[Step Trainer Trusted]
  end
  subgraph Curated
    ML[Machine Learning Curated]
  end
  C1 --> C2
  A1 --> A2
  S1 --> S2
  C2 --> A2
  C2 --> S2
  A2 --> ML
  S2 --> ML`,
    pipelineMermaid: `flowchart TD
  ingest[Ingest to S3 landing] --> glue1[Glue: sanitize & consent filter]
  glue1 --> trusted[Write trusted zone tables]
  trusted --> glue2[Glue: join sensor streams]
  glue2 --> curated[Write ML curated table]
  curated --> athena[Query with Athena]`,
    screenshots: [
      {
        src: "/images/projects/stedi-cover.svg",
        alt: "STEDI lakehouse architecture illustration",
      },
    ],
  },
  "drl-jss": {
    slug: "drl-jss",
    title: "Deep RL for Job Shop Scheduling",
    tagline:
      "Master's thesis: applying deep reinforcement learning to combinatorial scheduling.",
    businessProblem:
      "Job shop scheduling is a classic NP-hard optimization problem. Traditional heuristics struggle to generalize across dynamic shop-floor conditions, while exact solvers do not scale for many practical instances.",
    solution:
      "Developed and evaluated deep reinforcement learning agents that learn scheduling policies for job shop environments—demonstrating how DRL can produce competitive decisions for complex sequencing problems.",
    techStack: [
      "Python",
      "Deep Reinforcement Learning",
      "PyTorch / RL libraries",
      "Simulation environments",
    ],
    dataModel:
      "Environment state encodes jobs, machines, and remaining operations; actions select scheduling decisions; rewards optimize makespan and related objectives.",
    lessons: [
      "Representation of state/action space is as important as the learning algorithm.",
      "Reinforcement learning shines when policies must adapt beyond fixed heuristics.",
      "Reproducible experiments and clear baselines are essential for thesis-grade ML research.",
    ],
    architectureMermaid: `flowchart LR
  ENV[Job Shop Environment] --> AGENT[DRL Agent]
  AGENT --> ACTION[Scheduling Action]
  ACTION --> ENV
  ENV --> REWARD[Reward / Makespan Signal]
  REWARD --> AGENT
  AGENT --> POLICY[Learned Scheduling Policy]`,
    pipelineMermaid: `flowchart TD
  a[Define JSS environment] --> b[Design state & action space]
  b --> c[Train DRL policy]
  c --> d[Evaluate vs baselines]
  d --> e[Analyze generalization & makespan]
  e --> f[Document thesis findings]`,
    screenshots: [
      {
        src: "/images/projects/drl-jss-cover.png",
        alt: "Deep reinforcement learning for job shop scheduling — thesis project cover",
      },
    ],
    liveDemo: "https://github.com/Dna072/drl-jss",
  },
};

export function getProjectDetail(slug: string) {
  return projectDetails[slug] ?? null;
}
