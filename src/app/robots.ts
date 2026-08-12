import type { MetadataRoute } from "next";
import { siteConfig } from "@/lib/site";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
    },
    // Real XML sitemap lives at /sitemap-index.xml because /sitemap.xml/ is
    // reserved for Google Search Console HTML verification.
    sitemap: `${siteConfig.url}/sitemap-index.xml`,
  };
}
