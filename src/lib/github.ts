import { siteConfig } from "@/lib/site";

const GITHUB_API = "https://api.github.com";
const username = siteConfig.github.username;

export type GitHubRepo = {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  homepage: string | null;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  watchers_count: number;
  open_issues_count: number;
  topics: string[];
  fork: boolean;
  archived: boolean;
  created_at: string;
  updated_at: string;
  pushed_at: string;
  default_branch: string;
};

export type GitHubUser = {
  login: string;
  name: string | null;
  bio: string | null;
  avatar_url: string;
  html_url: string;
  public_repos: number;
  followers: number;
  following: number;
  location: string | null;
  blog: string | null;
  created_at: string;
};

export type LanguageStat = {
  language: string;
  bytes: number;
  percentage: number;
};

export type ContributionDay = {
  date: string;
  count: number;
  level: 0 | 1 | 2 | 3 | 4;
};

function authHeaders(): HeadersInit {
  const headers: HeadersInit = {
    Accept: "application/vnd.github+json",
    "User-Agent": `${username}-portfolio`,
  };
  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }
  return headers;
}

async function githubFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const response = await fetch(`${GITHUB_API}${path}`, {
      ...init,
      headers: { ...authHeaders(), ...init?.headers },
      // Static export: fetch once at build time
      next: { revalidate: false },
      cache: "force-cache",
    });

    if (!response.ok) {
      console.warn(`GitHub API ${path} failed: ${response.status}`);
      return null;
    }

    return (await response.json()) as T;
  } catch (error) {
    console.warn(`GitHub API ${path} error`, error);
    return null;
  }
}

export async function getGitHubUser() {
  return githubFetch<GitHubUser>(`/users/${username}`);
}

export async function getAllRepos(): Promise<GitHubRepo[]> {
  const repos =
    (await githubFetch<GitHubRepo[]>(
      `/users/${username}/repos?per_page=100&sort=updated`,
    )) ?? [];
  return repos.filter((repo) => !repo.fork && !repo.archived);
}

export async function getRepo(name: string) {
  return githubFetch<GitHubRepo>(`/repos/${username}/${name}`);
}

export async function getRepoReadme(name: string) {
  try {
    const response = await fetch(
      `${GITHUB_API}/repos/${username}/${name}/readme`,
      {
        headers: {
          ...authHeaders(),
          Accept: "application/vnd.github.raw+json",
        },
        cache: "force-cache",
      },
    );
    if (!response.ok) return null;
    return await response.text();
  } catch {
    return null;
  }
}

export async function getRepoLanguages(name: string) {
  return githubFetch<Record<string, number>>(
    `/repos/${username}/${name}/languages`,
  );
}

export async function getFeaturedRepos(allRepos?: GitHubRepo[]) {
  const repos = allRepos ?? (await getAllRepos());
  const featuredNames = new Set<string>(siteConfig.github.featuredRepos);
  const topic = siteConfig.github.featuredTopic;

  const featured = repos.filter(
    (repo) =>
      featuredNames.has(repo.name) || repo.topics?.includes(topic),
  );

  // Preserve configured order for known featured repos, then append topic-tagged ones.
  const ordered: GitHubRepo[] = [];
  for (const name of siteConfig.github.featuredRepos) {
    const match = featured.find((repo) => repo.name === name);
    if (match) ordered.push(match);
  }
  for (const repo of featured) {
    if (!ordered.some((item) => item.id === repo.id)) ordered.push(repo);
  }
  return ordered;
}

export async function getLanguageStats(
  repos?: GitHubRepo[],
): Promise<LanguageStat[]> {
  const list = repos ?? (await getAllRepos());
  const totals = new Map<string, number>();

  await Promise.all(
    list.slice(0, 20).map(async (repo) => {
      const languages = await getRepoLanguages(repo.name);
      if (!languages) return;
      for (const [language, bytes] of Object.entries(languages)) {
        totals.set(language, (totals.get(language) ?? 0) + bytes);
      }
    }),
  );

  const sum = Array.from(totals.values()).reduce((a, b) => a + b, 0) || 1;
  return Array.from(totals.entries())
    .map(([language, bytes]) => ({
      language,
      bytes,
      percentage: Math.round((bytes / sum) * 1000) / 10,
    }))
    .sort((a, b) => b.bytes - a.bytes)
    .slice(0, 8);
}

export async function getRecentEvents() {
  const events = await githubFetch<
    Array<{
      id: string;
      type: string;
      repo: { name: string; url: string };
      created_at: string;
    }>
  >(`/users/${username}/events/public?per_page=30`);
  return events ?? [];
}

/**
 * Build a contribution-style heatmap from public events as a static-friendly fallback.
 * When a richer source is available at build time, this still renders a useful activity view.
 */
export async function getContributionHeatmap(): Promise<ContributionDay[]> {
  // Prefer third-party contributions API (no auth); fall back to event-derived counts.
  try {
    const response = await fetch(
      `https://github-contributions-api.jogruber.de/v4/${username}?y=last`,
      { cache: "force-cache" },
    );
    if (response.ok) {
      const data = (await response.json()) as {
        contributions: Array<{ date: string; count: number; level: number }>;
      };
      return data.contributions.map((day) => ({
        date: day.date,
        count: day.count,
        level: Math.min(4, Math.max(0, day.level)) as ContributionDay["level"],
      }));
    }
  } catch {
    // continue to fallback
  }

  const events = await getRecentEvents();
  const counts = new Map<string, number>();
  const today = new Date();
  for (let i = 0; i < 365; i += 1) {
    const date = new Date(today);
    date.setDate(today.getDate() - i);
    counts.set(date.toISOString().slice(0, 10), 0);
  }
  for (const event of events) {
    const day = event.created_at.slice(0, 10);
    if (counts.has(day)) counts.set(day, (counts.get(day) ?? 0) + 1);
  }

  return Array.from(counts.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({
      date,
      count,
      level: (count === 0
        ? 0
        : count < 2
          ? 1
          : count < 4
            ? 2
            : count < 6
              ? 3
              : 4) as ContributionDay["level"],
    }));
}

export function getRepoOpenGraphImage(repo: GitHubRepo) {
  return `https://opengraph.githubassets.com/1/${repo.full_name}`;
}
