export const siteConfig = {
  name: "Derrick Adjei",
  title: "Derrick Adjei | Full-Stack & Data Engineer in Stockholm",
  description:
    "Derrick Adjei is a full-stack and data engineer in Stockholm. Builds Python/FastAPI backends, React/TypeScript apps, media/video SaaS systems, and AWS data platforms.",
  url: "https://dna072.github.io",
  locale: "en_US",
  author: {
    name: "Derrick Adjei",
    email: "derrick.adjei.eng@gmail.com",
    location: "Stockholm, Sweden",
    role: "Full-Stack Engineer · Data Engineer",
    headshot: "/images/headshot.png",
    headline:
      "Building media/video SaaS backends, scalable APIs, and data platforms that turn complex systems into trusted products.",
    shortBio:
      "Full-stack and data engineer with backend & frontend experience since 2017—shipping Python APIs, React/TypeScript apps, cloud data platforms, and production-style media/video SaaS projects.",
    bio: `Full-stack and data engineer with 4+ years building cloud data platforms and ELT pipelines on AWS, plus backend and frontend work since 2017.

I ship trusted datasets for reporting and ML, and production web apps with TypeScript, React, Node.js, Next.js, and Python. Live platforms include MedLink, Arctiq, and TPG (National Teaching Council).

Recent portfolio work covers the video content lifecycle through ClipForge, MediaVault, StreamPulse, and RenderFlow. MSc Data Science (Uppsala); thesis on deep RL for job shop scheduling (github.com/Dna072/drl-jss). BSc Computer Engineering (University of Ghana).`,
    goals:
      "I want to join teams building high-quality backend services, full-stack products, data platforms, or media technology systems—where reliability, observability, and strong engineering craft matter.",
  },
  links: {
    github: "https://github.com/Dna072",
    linkedin: "https://www.linkedin.com/in/derrick-adjei-5421289a/",
    email: "mailto:derrick.adjei.eng@gmail.com",
    resume: "/resume/Derrick_Adjei_Resume.pdf",
    thesis: "https://github.com/Dna072/drl-jss",
  },
  github: {
    username: "Dna072",
    featuredRepos: [
      "clipforge",
      "mediavault",
      "streampulse",
      "renderflow",
      "drl-jss",
      "airflow-pipelines",
      "sparkify_dwh_aws_redshift",
      "stedi-human-balance-analytics",
    ],
    featuredTopic: "featured",
  },
  stats: {
    yearsExperience: 8,
    yearsDataEngineering: 4,
    projects: 15,
    githubRepos: 26,
    technologies: 30,
  },
  /** Primary header links — keep to 4–5 high-signal destinations. */
  navigation: [
    { label: "Projects", href: "/projects/" },
    { label: "Experience", href: "/#experience" },
    { label: "Skills", href: "/#skills" },
    { label: "Resume", href: "/resume/" },
    { label: "Contact", href: "/contact/" },
  ],
  /** Secondary destinations shown in the footer. */
  footerNavigation: [
    { label: "About", href: "/#about" },
    { label: "Articles", href: "/articles/" },
    { label: "GitHub", href: "/github/" },
    { label: "Architecture", href: "/architecture/" },
    { label: "Projects", href: "/projects/" },
    { label: "Resume", href: "/resume/" },
    { label: "Contact", href: "/contact/" },
  ],
} as const;

export type NavItem = (typeof siteConfig.navigation)[number];
export type FooterNavItem = (typeof siteConfig.footerNavigation)[number];
