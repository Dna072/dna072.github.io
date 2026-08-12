import { siteConfig } from "@/lib/site";

export const seoKeywords = [
  "Derrick Adjei",
  "Derrick Adjei Data Engineer",
  "Data Engineer Stockholm",
  "Analytics Engineer Stockholm",
  "Data Engineer Sweden",
  "Full-Stack Engineer Stockholm",
  "Apache Airflow",
  "Amazon Redshift",
  "AWS Glue",
  "AWS Data Engineer",
  "ETL pipelines",
  "ELT pipelines",
  "Data warehousing",
  "Lakehouse",
  "Power Platform",
  "Power BI",
  "Python",
  "SQL",
  "React",
  "TypeScript",
  "Next.js",
  "Uppsala University",
  "Portfolio",
] as const;

export const personJsonLd = {
  "@type": "Person",
  "@id": `${siteConfig.url}/#person`,
  name: siteConfig.author.name,
  url: siteConfig.url,
  image: `${siteConfig.url}${siteConfig.author.headshot}`,
  jobTitle: siteConfig.author.role,
  description: siteConfig.description,
  email: siteConfig.author.email,
  telephone: "+46-76-251-7998",
  address: {
    "@type": "PostalAddress",
    addressLocality: "Stockholm",
    addressCountry: "SE",
  },
  sameAs: [siteConfig.links.github, siteConfig.links.linkedin, siteConfig.url],
  alumniOf: [
    {
      "@type": "CollegeOrUniversity",
      name: "Uppsala University",
    },
    {
      "@type": "CollegeOrUniversity",
      name: "University of Ghana",
    },
  ],
  worksFor: [
    {
      "@type": "Organization",
      name: "KPMG Sweden",
    },
  ],
  knowsAbout: [
    "Data Engineering",
    "Analytics Engineering",
    "Backend Development",
    "Frontend Development",
    "TypeScript",
    "JavaScript",
    "React",
    "Vite",
    "Node.js",
    "Next.js",
    "Reinforcement Learning",
    "Deep Reinforcement Learning",
    "Apache Airflow",
    "Amazon Redshift",
    "AWS Glue",
    "Python",
    "SQL",
    "Microsoft Power Platform",
    "Power BI",
  ],
} as const;

export const websiteJsonLd = {
  "@type": "WebSite",
  "@id": `${siteConfig.url}/#website`,
  name: siteConfig.name,
  url: siteConfig.url,
  description: siteConfig.description,
  inLanguage: "en",
  publisher: { "@id": `${siteConfig.url}/#person` },
} as const;

export const profilePageJsonLd = {
  "@type": "ProfilePage",
  "@id": `${siteConfig.url}/#profile`,
  url: siteConfig.url,
  name: siteConfig.title,
  description: siteConfig.description,
  mainEntity: { "@id": `${siteConfig.url}/#person` },
  isPartOf: { "@id": `${siteConfig.url}/#website` },
} as const;
