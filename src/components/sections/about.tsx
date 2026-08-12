"use client";

import { motion, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { siteConfig } from "@/lib/site";
import { FadeIn } from "@/components/motion/fade-in";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function AnimatedStat({
  label,
  value,
  suffix = "",
}: {
  label: string;
  value: number;
  suffix?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!inView) return;
    let frame = 0;
    const totalFrames = 36;
    const id = window.setInterval(() => {
      frame += 1;
      setCount(Math.round((value * frame) / totalFrames));
      if (frame >= totalFrames) window.clearInterval(id);
    }, 24);
    return () => window.clearInterval(id);
  }, [inView, value]);

  return (
    <div ref={ref} className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <p className="text-3xl font-semibold tracking-tight text-foreground">
        {count}
        {suffix}
      </p>
      <p className="mt-1 text-sm text-muted">{label}</p>
    </div>
  );
}

export function AboutSection() {
  return (
    <section id="about" className="scroll-mt-24 px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <FadeIn>
          <p className="text-sm font-medium text-brand">About</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Who I am
          </h2>
          <p className="mt-3 max-w-2xl text-muted">
            A recruiter-friendly snapshot of my background, education, and the
            platforms I aim to build next.
          </p>
        </FadeIn>

        <div className="mt-10 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <FadeIn delay={0.05}>
            <Card className="h-full">
              <CardHeader>
                <CardTitle>Professional biography</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm leading-relaxed text-muted">
                {siteConfig.author.bio.split("\n\n").map((paragraph) => (
                  <p key={paragraph.slice(0, 24)}>{paragraph}</p>
                ))}
                <p className="text-foreground/90">{siteConfig.author.goals}</p>
              </CardContent>
            </Card>
          </FadeIn>

          <div className="space-y-6">
            <FadeIn delay={0.1}>
              <Card>
                <CardHeader>
                  <CardTitle>Education</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="font-medium">MSc Data Science</p>
                  <p className="text-sm text-muted">Uppsala University</p>
                  <p className="mt-3 font-medium">BSc Computer Engineering</p>
                  <p className="text-sm text-muted">University of Ghana</p>
                </CardContent>
              </Card>
            </FadeIn>
            <FadeIn delay={0.15}>
              <Card>
                <CardHeader>
                  <CardTitle>Current focus</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-muted">
                  <p>
                    Cloud data platforms with Airflow, Spark, and AWS—plus
                    full-stack delivery with TypeScript, Node.js, and Next.js.
                  </p>
                  <p>
                    Machine learning with a focus on{" "}
                    <span className="text-foreground">reinforcement learning</span>
                    . Thesis:{" "}
                    <a
                      href={siteConfig.links.thesis}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand hover:underline"
                    >
                      Deep RL for Job Shop Scheduling
                    </a>
                    .
                  </p>
                </CardContent>
              </Card>
            </FadeIn>
          </div>
        </div>

        <motion.div
          className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
        >
          <AnimatedStat
            label="Years software (since 2017)"
            value={siteConfig.stats.yearsExperience}
            suffix="+"
          />
          <AnimatedStat
            label="Years data engineering"
            value={siteConfig.stats.yearsDataEngineering}
            suffix="+"
          />
          <AnimatedStat
            label="GitHub repositories"
            value={siteConfig.stats.githubRepos}
          />
          <AnimatedStat
            label="Core technologies"
            value={siteConfig.stats.technologies}
            suffix="+"
          />
        </motion.div>
      </div>
    </section>
  );
}
