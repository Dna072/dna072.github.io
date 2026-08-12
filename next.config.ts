import type { NextConfig } from "next";

/**
 * GitHub Pages project sites require a basePath matching the repository name.
 * - CI sets BASE_PATH=/Portfolio explicitly in the workflow.
 * - Local production preview: BASE_PATH=/Portfolio npm run build
 * - User site / custom domain: BASE_PATH="" npm run build
 */
function resolveBasePath() {
  if (process.env.BASE_PATH !== undefined) {
    const value = process.env.BASE_PATH.trim();
    if (value === "" || value === "/") return "";
    return value.startsWith("/") ? value.replace(/\/$/, "") : `/${value.replace(/\/$/, "")}`;
  }

  const repoName = process.env.GITHUB_REPOSITORY?.split("/")[1];
  const isUserSite = Boolean(repoName?.endsWith(".github.io"));
  if (
    (process.env.GITHUB_ACTIONS === "true" || process.env.NODE_ENV === "production") &&
    repoName &&
    !isUserSite
  ) {
    return `/${repoName}`;
  }

  return "";
}

const basePath = resolveBasePath();

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  basePath,
  // Keep assetPrefix aligned with basePath (no trailing slash) for static export.
  assetPrefix: basePath || undefined,
  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
  },
};

export default nextConfig;
