import type { Metadata } from "next";
import Link from "next/link";
import { Download, ExternalLink, Mail, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { siteConfig } from "@/lib/site";
import { seoKeywords } from "@/lib/seo";
import { withBasePath } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Resume | Derrick Adjei — Data Engineer Stockholm",
  description:
    "Resume of Derrick Adjei, Data Engineer and Analytics Engineer in Stockholm, Sweden. Experience with AWS, Redshift, Airflow, Power Platform, and full-stack development.",
  keywords: [...seoKeywords, "Derrick Adjei resume", "CV Data Engineer Stockholm"],
  alternates: {
    canonical: `${siteConfig.url}/resume/`,
  },
  openGraph: {
    title: "Resume | Derrick Adjei — Data Engineer Stockholm",
    description:
      "Download the resume of Derrick Adjei — Data Engineer / Analytics Engineer based in Stockholm, Sweden.",
    url: `${siteConfig.url}/resume/`,
    images: [{ url: "/og.png", width: 1200, height: 630, alt: siteConfig.title }],
  },
};

const experience = [
  {
    role: "Data & Process Automation (System Specialist)",
    org: "KPMG Sweden",
    period: "2023 – Present",
    location: "Stockholm, Sweden",
    highlights: [
      "Build enterprise solutions with Microsoft Power Platform (Power Apps, Power Automate, Power BI).",
      "Automate business processes and deliver operational and risk-management dashboards.",
      "Partner with stakeholders to digitize workflows and improve reporting.",
    ],
  },
  {
    role: "Data Engineer (Contract)",
    org: "National Teaching Council",
    period: "2022 – 2025",
    location: "Greater Accra, Ghana",
    highlights: [
      "Designed and deployed production ETL with AWS Glue from PostgreSQL into Amazon Redshift.",
      "Built staging and transformation layers into a star-schema warehouse for nationwide analytics.",
      "Optimized Redshift distribution and sort keys, improving query performance up to 50%.",
      "Supported analytics across 500,000+ users with batch pipelines, quality checks, and monitoring.",
    ],
  },
] as const;

const skills = [
  "Python",
  "SQL",
  "Apache Airflow",
  "Apache Spark",
  "AWS (S3, Glue, Redshift, Athena)",
  "PostgreSQL",
  "Docker",
  "CI/CD",
  "Power Platform",
  "Power BI",
  "TypeScript",
  "React",
] as const;

export default function ResumePage() {
  const resumeHref = withBasePath(siteConfig.links.resume);

  return (
    <div className="px-4 py-16 sm:px-6">
      <div className="mx-auto max-w-4xl">
        <p className="text-sm font-medium text-brand">Resume</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">
          Derrick Adjei
        </h1>
        <p className="mt-3 max-w-2xl text-lg text-muted">
          Data Engineer / Analytics Engineer in Stockholm, Sweden — building
          cloud data platforms, analytics warehouses, and automation systems.
        </p>

        <div className="mt-6 flex flex-wrap items-center gap-3 text-sm text-muted">
          <span className="inline-flex items-center gap-1.5">
            <MapPin className="h-4 w-4 text-brand" />
            {siteConfig.author.location}
          </span>
          <a
            href={siteConfig.links.email}
            className="inline-flex items-center gap-1.5 hover:text-foreground"
          >
            <Mail className="h-4 w-4 text-brand" />
            {siteConfig.author.email}
          </a>
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild>
            <a href={resumeHref} download>
              <Download className="h-4 w-4" />
              Download PDF resume
            </a>
          </Button>
          <Button asChild variant="outline">
            <a href={resumeHref} target="_blank" rel="noreferrer">
              <ExternalLink className="h-4 w-4" />
              Open PDF
            </a>
          </Button>
          <Button asChild variant="ghost">
            <Link href="/contact/">Contact</Link>
          </Button>
        </div>

        <section className="mt-12">
          <h2 className="text-2xl font-semibold tracking-tight">Experience</h2>
          <div className="mt-6 space-y-6">
            {experience.map((item) => (
              <Card key={`${item.org}-${item.role}`}>
                <CardHeader>
                  <CardTitle className="text-lg">{item.role}</CardTitle>
                  <p className="text-sm text-brand">{item.org}</p>
                  <p className="text-sm text-muted">
                    {item.period} · {item.location}
                  </p>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-muted">
                    {item.highlights.map((point) => (
                      <li key={point} className="flex gap-2">
                        <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section className="mt-12">
          <h2 className="text-2xl font-semibold tracking-tight">
            Core skills
          </h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {skills.map((skill) => (
              <span
                key={skill}
                className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-sm text-muted"
              >
                {skill}
              </span>
            ))}
          </div>
        </section>

        <section className="mt-12">
          <h2 className="text-2xl font-semibold tracking-tight">Education</h2>
          <div className="mt-4 space-y-3 text-sm text-muted">
            <p>
              <span className="font-medium text-foreground">
                MSc Data Science
              </span>{" "}
              — Uppsala University (2022 – 2024)
            </p>
            <p>
              <span className="font-medium text-foreground">
                BSc Computer Engineering
              </span>{" "}
              — University of Ghana (2013 – 2017)
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
