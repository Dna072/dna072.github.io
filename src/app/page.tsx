import type { Metadata } from "next";
import { HeroSection } from "@/components/sections/hero";
import { AboutSection } from "@/components/sections/about";
import { SkillsSection } from "@/components/sections/skills";
import { ExperienceSection } from "@/components/sections/experience";
import { FeaturedProjectsSection } from "@/components/sections/featured-projects";
import { ProductProjectsSection } from "@/components/sections/product-projects";
import { CtaSection } from "@/components/sections/cta";
import { getFeaturedRepos } from "@/lib/github";
import { siteConfig } from "@/lib/site";

export const metadata: Metadata = {
  title: {
    absolute: siteConfig.title,
  },
  description: siteConfig.description,
  alternates: {
    canonical: siteConfig.url,
  },
  openGraph: {
    title: siteConfig.title,
    description: siteConfig.description,
    url: siteConfig.url,
  },
};

export default async function HomePage() {
  const featured = await getFeaturedRepos();

  return (
    <>
      <HeroSection />
      <AboutSection />
      <FeaturedProjectsSection repos={featured} />
      <ProductProjectsSection />
      <ExperienceSection />
      <SkillsSection />
      <CtaSection />
    </>
  );
}
