"use client";

import Link from "next/link";
import { ExternalLink, Github, Network, Star } from "lucide-react";
import type { GitHubRepo } from "@/lib/github";
import { getRepoOpenGraphImage } from "@/lib/github";
import { formatDate, withBasePath } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FadeIn } from "@/components/motion/fade-in";

export function ProjectCard({
  repo,
  delay = 0,
  coverSrc,
}: {
  repo: GitHubRepo;
  delay?: number;
  coverSrc?: string;
}) {
  const image = coverSrc
    ? withBasePath(coverSrc)
    : getRepoOpenGraphImage(repo);

  return (
    <FadeIn delay={delay}>
      <Card className="group h-full overflow-hidden transition-colors hover:border-brand/30">
        <div className="relative aspect-[16/9] overflow-hidden border-b border-white/10 bg-white/[0.02]">
          {/* eslint-disable-next-line @next/next/no-img-element -- static export + GH Pages basePath */}
          <img
            src={image}
            alt={`${repo.name} repository preview`}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
            loading="lazy"
            decoding="async"
          />
        </div>
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <CardTitle className="text-xl">{repo.name}</CardTitle>
            <span className="inline-flex items-center gap-1 text-xs text-muted">
              <Star className="h-3.5 w-3.5 text-brand" />
              {repo.stargazers_count}
            </span>
          </div>
          <p className="text-sm leading-relaxed text-muted">
            {repo.description ?? "Featured data engineering project."}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {repo.language ? <Badge>{repo.language}</Badge> : null}
            {repo.topics?.slice(0, 4).map((topic) => (
              <Badge key={topic} variant="secondary">
                {topic}
              </Badge>
            ))}
          </div>
          <p className="text-xs text-muted">
            Updated {formatDate(repo.pushed_at || repo.updated_at)}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button asChild size="sm" variant="secondary">
              <Link href={`/projects/${repo.name}/`}>
                <Network className="h-3.5 w-3.5" /> Architecture
              </Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href={`/projects/${repo.name}/`}>Read More</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <a href={repo.html_url} target="_blank" rel="noreferrer">
                <Github className="h-3.5 w-3.5" /> GitHub
              </a>
            </Button>
            {repo.homepage ? (
              <Button asChild size="sm">
                <a href={repo.homepage} target="_blank" rel="noreferrer">
                  <ExternalLink className="h-3.5 w-3.5" /> Live Demo
                </a>
              </Button>
            ) : null}
          </div>
        </CardContent>
      </Card>
    </FadeIn>
  );
}
