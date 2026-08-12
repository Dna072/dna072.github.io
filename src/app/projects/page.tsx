import type { Metadata } from "next";
import { ProjectSearch } from "@/components/projects/project-search";
import { ProductProjectsSection } from "@/components/sections/product-projects";
import { getAllRepos, getFeaturedRepos } from "@/lib/github";

export const metadata: Metadata = {
  title: "Projects",
  description:
    "Full-stack products, data platforms, and ML research—including MedLink, Arctiq, TPG, Airflow, Redshift, and deep RL thesis work.",
};

export default async function ProjectsPage() {
  const [featured, all] = await Promise.all([
    getFeaturedRepos(),
    getAllRepos(),
  ]);

  const featuredIds = new Set(featured.map((repo) => repo.id));
  const repos = [
    ...featured,
    ...all.filter((repo) => !featuredIds.has(repo.id)).slice(0, 9),
  ];

  return (
    <div className="py-8">
      <div className="px-4 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <p className="text-sm font-medium text-brand">Projects</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">
            Products, data platforms & research
          </h1>
          <p className="mt-3 max-w-2xl text-muted">
            Live full-stack systems since 2017, cloud data engineering projects,
            and machine learning research—including a deep RL master&apos;s
            thesis.
          </p>
        </div>
      </div>

      <ProductProjectsSection />

      <div className="px-4 pb-16 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-2xl font-semibold tracking-tight">
            GitHub repositories
          </h2>
          <div className="mt-8">
            <ProjectSearch repos={repos} />
          </div>
        </div>
      </div>
    </div>
  );
}
