import type { Metadata } from "next";
import Link from "next/link";
import {
  getAllRepos,
  getContributionHeatmap,
  getGitHubUser,
  getLanguageStats,
  getRecentEvents,
} from "@/lib/github";
import { siteConfig } from "@/lib/site";
import { formatDate, formatNumber } from "@/lib/utils";
import { ContributionHeatmap } from "@/components/github/contribution-heatmap";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "GitHub",
  description:
    "GitHub statistics, contribution activity, languages, and latest repositories for Derrick Adjei.",
};

export default async function GitHubPage() {
  const [user, repos, languages, heatmap, events] = await Promise.all([
    getGitHubUser(),
    getAllRepos(),
    getLanguageStats(),
    getContributionHeatmap(),
    getRecentEvents(),
  ]);

  const stars = repos.reduce((sum, repo) => sum + repo.stargazers_count, 0);
  const pinned = repos.slice(0, 6);

  return (
    <div className="px-4 py-16 sm:px-6">
      <div className="mx-auto max-w-content space-y-10">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            {user?.avatar_url ? (
              // eslint-disable-next-line @next/next/no-img-element -- remote GitHub avatar
              <img
                src={user.avatar_url}
                alt={`${siteConfig.name} GitHub avatar`}
                width={72}
                height={72}
                className="h-[72px] w-[72px] rounded-2xl border border-white/10 object-cover"
              />
            ) : null}
            <div>
              <p className="text-sm font-medium text-brand">GitHub</p>
              <h1 className="text-4xl font-semibold tracking-tight">
                @{siteConfig.github.username}
              </h1>
              <p className="mt-1 max-w-xl text-muted">
                {user?.bio ?? siteConfig.author.shortBio}
              </p>
            </div>
          </div>
          <Button asChild>
            <a href={siteConfig.links.github} target="_blank" rel="noreferrer">
              Open GitHub profile
            </a>
          </Button>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              label: "Public repos",
              value: user?.public_repos ?? siteConfig.stats.githubRepos,
            },
            { label: "Followers", value: user?.followers ?? 0 },
            { label: "Total stars", value: stars },
            { label: "Recent events", value: events.length },
          ].map((stat) => (
            <Card key={stat.label}>
              <CardContent className="p-5">
                <p className="text-3xl font-semibold">
                  {formatNumber(stat.value)}
                </p>
                <p className="mt-1 text-sm text-muted">{stat.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Contribution activity</CardTitle>
          </CardHeader>
          <CardContent>
            <ContributionHeatmap days={heatmap} />
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Languages</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {languages.map((lang) => (
                <div key={lang.language}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span>{lang.language}</span>
                    <span className="text-muted">{lang.percentage}%</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                    <div
                      className="h-full rounded-full bg-brand"
                      style={{ width: `${lang.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Commit / event activity</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {events.slice(0, 8).map((event) => (
                <div
                  key={event.id}
                  className="flex items-start justify-between gap-3 border-b border-white/5 pb-3 text-sm last:border-0"
                >
                  <div>
                    <p className="font-medium">{event.type.replace("Event", "")}</p>
                    <p className="text-muted">{event.repo.name}</p>
                  </div>
                  <p className="shrink-0 text-xs text-muted">
                    {formatDate(event.created_at)}
                  </p>
                </div>
              ))}
              {events.length === 0 ? (
                <p className="text-sm text-muted">
                  No recent public events available.
                </p>
              ) : null}
            </CardContent>
          </Card>
        </div>

        <section>
          <h2 className="text-2xl font-semibold tracking-tight">
            Latest repositories
          </h2>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {pinned.map((repo) => (
              <Card key={repo.id}>
                <CardHeader>
                  <CardTitle className="text-lg">
                    <Link
                      href={`/projects/${repo.name}/`}
                      className="hover:text-brand"
                    >
                      {repo.name}
                    </Link>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted">
                    {repo.description ?? "No description provided."}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {repo.language ? <Badge>{repo.language}</Badge> : null}
                    <Badge variant="secondary">★ {repo.stargazers_count}</Badge>
                    <Badge variant="outline">
                      Updated {formatDate(repo.pushed_at)}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
