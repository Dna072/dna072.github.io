import Link from "next/link";
import { siteConfig } from "@/lib/site";
import { withBasePath } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { FadeIn } from "@/components/motion/fade-in";

export function CtaSection() {
  return (
    <section className="px-4 py-20 sm:px-6">
      <FadeIn>
        <div className="mx-auto max-w-6xl overflow-hidden rounded-[2rem] border border-brand/20 bg-gradient-to-br from-brand/15 via-white/[0.03] to-transparent px-6 py-12 sm:px-10">
          <h2 className="max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl">
            Looking for a data engineer who ships trusted platforms?
          </h2>
          <p className="mt-3 max-w-2xl text-muted">
            I&apos;m open to Data Engineer, Analytics Engineer, and Software
            Engineer roles focused on scalable pipelines and analytics systems.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link href="/contact/">Contact me</Link>
            </Button>
            <Button asChild size="lg" variant="secondary">
              <a href={withBasePath(siteConfig.links.resume)} download>
                Download resume
              </a>
            </Button>
            <Button asChild size="lg" variant="outline">
              <a href={siteConfig.links.linkedin} target="_blank" rel="noreferrer">
                LinkedIn
              </a>
            </Button>
          </div>
        </div>
      </FadeIn>
    </section>
  );
}
