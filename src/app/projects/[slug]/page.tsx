import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Github, ExternalLink } from "lucide-react";
import { remark } from "remark";
import remarkGfm from "remark-gfm";
import html from "remark-html";
import {
  getAllRepos,
  getFeaturedRepos,
  getRepo,
  getRepoOpenGraphImage,
  getRepoReadme,
} from "@/lib/github";
import { getProjectDetail, projectDetails } from "@/lib/projects";
import { siteConfig } from "@/lib/site";
import { formatDate, withBasePath } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MermaidDiagram } from "@/components/diagrams/mermaid";
import { ReadingProgress } from "@/components/layout/reading-progress";

type Props = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  const [featured, all] = await Promise.all([
    getFeaturedRepos(),
    getAllRepos(),
  ]);
  const slugs = new Set<string>([
    ...Object.keys(projectDetails),
    ...featured.map((repo) => repo.name),
    ...all.slice(0, 12).map((repo) => repo.name),
  ]);
  return Array.from(slugs).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const detail = getProjectDetail(slug);
  const repo = await getRepo(slug);
  const title = detail?.title ?? repo?.name ?? slug;
  const description =
    detail?.tagline ??
    repo?.description ??
    "Project case study from Derrick Adjei.";
  return { title, description };
}

export default async function ProjectDetailPage({ params }: Props) {
  const { slug } = await params;
  const repo = await getRepo(slug);
  if (!repo) notFound();

  const detail = getProjectDetail(slug);
  const readme = await getRepoReadme(slug);
  const readmeHtml = readme
    ? String(await remark().use(remarkGfm).use(html).process(readme))
    : null;

  const cover = detail?.screenshots[0]?.src
    ? withBasePath(detail.screenshots[0].src)
    : getRepoOpenGraphImage(repo);

  return (
    <>
      <ReadingProgress targetId="project-article" />
      <article id="project-article" className="px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-4xl">
          <p className="text-sm font-medium text-brand">Project case study</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">
            {detail?.title ?? repo.name}
          </h1>
          <p className="mt-3 text-lg text-muted">
            {detail?.tagline ?? repo.description}
          </p>

          <div className="mt-6 flex flex-wrap gap-2">
            {repo.language ? <Badge>{repo.language}</Badge> : null}
            {(detail?.techStack ?? repo.topics ?? []).slice(0, 8).map((item) => (
              <Badge key={item} variant="secondary">
                {item}
              </Badge>
            ))}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button asChild>
              <a href={repo.html_url} target="_blank" rel="noreferrer">
                <Github className="h-4 w-4" /> Repository
              </a>
            </Button>
            {repo.homepage || detail?.liveDemo ? (
              <Button asChild variant="secondary">
                <a
                  href={detail?.liveDemo ?? repo.homepage ?? "#"}
                  target="_blank"
                  rel="noreferrer"
                >
                  <ExternalLink className="h-4 w-4" /> Live Demo
                </a>
              </Button>
            ) : null}
            <Button asChild variant="outline">
              <Link href="/projects/">All projects</Link>
            </Button>
          </div>

          <div className="relative mt-10 aspect-[16/9] overflow-hidden rounded-2xl border border-white/10">
            {/* eslint-disable-next-line @next/next/no-img-element -- static export + GH Pages basePath */}
            <img
              src={cover}
              alt={`${repo.name} cover`}
              className="h-full w-full object-cover"
            />
          </div>

          <dl className="mt-8 grid gap-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-muted">Stars</dt>
              <dd className="mt-1 font-medium">{repo.stargazers_count}</dd>
            </div>
            <div>
              <dt className="text-muted">Language</dt>
              <dd className="mt-1 font-medium">{repo.language ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-muted">Last updated</dt>
              <dd className="mt-1 font-medium">
                {formatDate(repo.pushed_at || repo.updated_at)}
              </dd>
            </div>
          </dl>

          {detail ? (
            <div className="mt-12 space-y-12">
              <section>
                <h2 className="text-2xl font-semibold tracking-tight">
                  Business problem
                </h2>
                <p className="mt-3 leading-relaxed text-muted">
                  {detail.businessProblem}
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold tracking-tight">
                  Solution
                </h2>
                <p className="mt-3 leading-relaxed text-muted">
                  {detail.solution}
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold tracking-tight">
                  Tech stack
                </h2>
                <div className="mt-4 flex flex-wrap gap-2">
                  {detail.techStack.map((tech) => (
                    <Badge key={tech}>{tech}</Badge>
                  ))}
                </div>
              </section>

              <section>
                <h2 className="text-2xl font-semibold tracking-tight">
                  Data model
                </h2>
                <p className="mt-3 leading-relaxed text-muted">
                  {detail.dataModel}
                </p>
              </section>

              <section>
                <h2 className="mb-4 text-2xl font-semibold tracking-tight">
                  Architecture diagram
                </h2>
                <div className="overflow-auto rounded-2xl border border-white/10 bg-white/[0.02] p-4">
                  <MermaidDiagram chart={detail.architectureMermaid} />
                </div>
              </section>

              <section>
                <h2 className="mb-4 text-2xl font-semibold tracking-tight">
                  Pipeline diagram
                </h2>
                <div className="overflow-auto rounded-2xl border border-white/10 bg-white/[0.02] p-4">
                  <MermaidDiagram chart={detail.pipelineMermaid} />
                </div>
              </section>

              <section>
                <h2 className="text-2xl font-semibold tracking-tight">
                  Lessons learned
                </h2>
                <ul className="mt-4 space-y-2 text-muted">
                  {detail.lessons.map((lesson) => (
                    <li key={lesson} className="flex gap-2">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />
                      <span>{lesson}</span>
                    </li>
                  ))}
                </ul>
              </section>

              {detail.screenshots.length > 0 ? (
                <section>
                  <h2 className="mb-4 text-2xl font-semibold tracking-tight">
                    Screenshots
                  </h2>
                  <div className="grid gap-4">
                    {detail.screenshots.map((shot) => (
                      <div
                        key={shot.src}
                        className="relative aspect-[16/9] overflow-hidden rounded-2xl border border-white/10"
                      >
                        {/* eslint-disable-next-line @next/next/no-img-element -- static export + GH Pages basePath */}
                        <img
                          src={withBasePath(shot.src)}
                          alt={shot.alt}
                          className="h-full w-full object-cover"
                          loading="lazy"
                        />
                      </div>
                    ))}
                  </div>
                </section>
              ) : null}
            </div>
          ) : (
            <section className="mt-12">
              <h2 className="text-2xl font-semibold tracking-tight">Overview</h2>
              <p className="mt-3 text-muted">
                {repo.description ??
                  `Explore the ${repo.name} repository by ${siteConfig.author.name}.`}
              </p>
            </section>
          )}

          {readmeHtml ? (
            <section className="mt-12">
              <h2 className="mb-4 text-2xl font-semibold tracking-tight">
                README
              </h2>
              <div
                className="prose prose-invert prose-portfolio max-w-none rounded-2xl border border-white/10 bg-white/[0.02] p-6"
                dangerouslySetInnerHTML={{ __html: readmeHtml }}
              />
            </section>
          ) : null}
        </div>
      </article>
    </>
  );
}
