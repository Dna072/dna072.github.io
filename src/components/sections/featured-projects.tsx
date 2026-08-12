import Link from "next/link";
import type { GitHubRepo } from "@/lib/github";
import { ProjectCard } from "@/components/projects/project-card";
import { Button } from "@/components/ui/button";
import { FadeIn } from "@/components/motion/fade-in";
import { projectDetails } from "@/lib/projects";

export function FeaturedProjectsSection({ repos }: { repos: GitHubRepo[] }) {
  return (
    <section id="projects" className="scroll-mt-24 px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-content">
        <FadeIn>
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-brand">Projects</p>
              <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
                Featured projects
              </h2>
              <p className="mt-3 max-w-2xl text-muted">
                Media/video SaaS systems, data platforms, pipelines, and ML
                research from my GitHub—built as production-style portfolio
                work.
              </p>
            </div>
            <Button asChild variant="outline">
              <Link href="/projects/">View all projects</Link>
            </Button>
          </div>
        </FadeIn>

        <div className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {repos.map((repo, index) => (
            <ProjectCard
              key={repo.id}
              repo={repo}
              delay={index * 0.05}
              coverSrc={projectDetails[repo.name]?.screenshots[0]?.src}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
