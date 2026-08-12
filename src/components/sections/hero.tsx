"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Github, Linkedin, ArrowRight, Download } from "lucide-react";
import { siteConfig } from "@/lib/site";
import { withBasePath } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { TypingText } from "@/components/sections/typing-text";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden px-4 pb-20 pt-16 sm:px-6 sm:pt-24">
      <div className="pointer-events-none absolute inset-0 grid-fade opacity-60" />
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -left-24 top-10 h-72 w-72 rounded-full bg-brand/20 blur-3xl"
        animate={{ opacity: [0.25, 0.45, 0.25], scale: [1, 1.08, 1] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -right-16 bottom-0 h-80 w-80 rounded-full bg-white/10 blur-3xl"
        animate={{ opacity: [0.15, 0.3, 0.15], y: [0, -18, 0] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="relative mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-[1.15fr_0.85fr]">
        <div>
          <p className="mb-4 text-sm font-medium tracking-wide text-brand">
            {siteConfig.author.role}
          </p>
          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            {siteConfig.name}
          </h1>
          <div className="mt-5 min-h-[4.5rem] max-w-2xl text-lg leading-relaxed text-muted sm:text-xl">
            <TypingText text={siteConfig.author.headline} />
          </div>
          <p className="mt-4 max-w-xl text-base text-muted">
            {siteConfig.author.shortBio}
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link href="/projects/">
                View Projects <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="secondary">
              <a href={withBasePath(siteConfig.links.resume)} download>
                <Download className="h-4 w-4" /> Download Resume
              </a>
            </Button>
            <Button asChild size="lg" variant="outline">
              <a
                href={siteConfig.links.github}
                target="_blank"
                rel="noreferrer"
              >
                <Github className="h-4 w-4" /> GitHub
              </a>
            </Button>
            <Button asChild size="lg" variant="outline">
              <a
                href={siteConfig.links.linkedin}
                target="_blank"
                rel="noreferrer"
              >
                <Linkedin className="h-4 w-4" /> LinkedIn
              </a>
            </Button>
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15 }}
          className="relative mx-auto w-full max-w-md"
        >
          <div className="absolute -inset-4 rounded-[2rem] bg-gradient-to-br from-brand/25 via-transparent to-white/10 blur-xl" />
          <div className="relative overflow-hidden rounded-[1.75rem] border border-white/10 bg-white/[0.03] p-3 shadow-2xl">
            <div className="relative aspect-[4/5] overflow-hidden rounded-[1.25rem] bg-gradient-to-b from-white/10 to-transparent">
              {/* eslint-disable-next-line @next/next/no-img-element -- static export + GH Pages basePath */}
              <img
                src={withBasePath(siteConfig.author.headshot)}
                alt={`${siteConfig.name} — professional portrait`}
                className="h-full w-full object-cover object-top"
                width={920}
                height={1150}
                decoding="async"
                fetchPriority="high"
              />
            </div>
            <div className="mt-3 flex items-center justify-between px-2 pb-1 text-xs text-muted">
              <span>Open to fullstack &amp; data roles</span>
              <span className="rounded-full bg-brand/15 px-2 py-1 text-brand">
                Available
              </span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
