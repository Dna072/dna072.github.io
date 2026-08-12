"use client";

import { useMemo, useState } from "react";
import type { GitHubRepo } from "@/lib/github";
import { ProjectCard } from "@/components/projects/project-card";
import { Input } from "@/components/ui/input";
import { projectDetails } from "@/lib/projects";

export function ProjectSearch({ repos }: { repos: GitHubRepo[] }) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return repos;
    return repos.filter((repo) => {
      const haystack = [
        repo.name,
        repo.description ?? "",
        repo.language ?? "",
        ...(repo.topics ?? []),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [query, repos]);

  return (
    <div>
      <div className="mb-8 max-w-md">
        <label htmlFor="project-search" className="sr-only">
          Search projects
        </label>
        <Input
          id="project-search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search projects, languages, topics..."
        />
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-muted">No projects match your search.</p>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {filtered.map((repo, index) => (
            <ProjectCard
              key={repo.id}
              repo={repo}
              delay={index * 0.04}
              coverSrc={projectDetails[repo.name]?.screenshots[0]?.src}
            />
          ))}
        </div>
      )}
    </div>
  );
}
