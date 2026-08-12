import type { MetadataRoute } from "next";
import { getAllArticles } from "@/lib/articles";
import { getFeaturedRepos } from "@/lib/github";
import { siteConfig } from "@/lib/site";

export const dynamic = "force-static";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = siteConfig.url;
  const articles = getAllArticles();
  const projects = await getFeaturedRepos();

  const staticRoutes = [
    "",
    "/projects/",
    "/articles/",
    "/architecture/",
    "/github/",
    "/contact/",
    "/resume/",
  ].map((path) => ({
    url: `${base}${path}`,
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
    priority: path === "" ? 1 : path === "/resume/" ? 0.9 : 0.8,
  }));

  const resumePdf = {
    url: `${base}/resume/Derrick_Adjei_Resume.pdf`,
    lastModified: new Date(),
    changeFrequency: "monthly" as const,
    priority: 0.85,
  };

  const articleRoutes = articles.map((article) => ({
    url: `${base}/articles/${article.slug}/`,
    lastModified: new Date(article.date),
    changeFrequency: "monthly" as const,
    priority: 0.7,
  }));

  const projectRoutes = projects.map((repo) => ({
    url: `${base}/projects/${repo.name}/`,
    lastModified: new Date(repo.pushed_at || repo.updated_at),
    changeFrequency: "weekly" as const,
    priority: 0.75,
  }));

  return [...staticRoutes, resumePdf, ...articleRoutes, ...projectRoutes];
}
