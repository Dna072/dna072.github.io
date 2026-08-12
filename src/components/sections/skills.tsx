"use client";

import { skillCategories, technologyRadar } from "@/lib/skills";
import { FadeIn } from "@/components/motion/fade-in";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function SkillsSection() {
  return (
    <section id="skills" className="scroll-mt-24 px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-content">
        <FadeIn>
          <p className="text-sm font-medium text-brand">Skills</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Strongest technologies
          </h2>
          <p className="mt-3 max-w-2xl text-muted">
            Tools I use across programming, data engineering, cloud, and
            software delivery—listed without fake proficiency scores.
          </p>
        </FadeIn>

        <div className="mt-10 grid gap-5 md:grid-cols-2">
          {skillCategories.map((category, index) => (
            <FadeIn key={category.id} delay={index * 0.05}>
              <Card className="h-full overflow-hidden">
                <CardHeader>
                  <CardTitle>{category.title}</CardTitle>
                  <CardDescription>{category.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="flex flex-wrap gap-2">
                    {category.skills.map((skill) => (
                      <li
                        key={skill}
                        className="rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1.5 text-sm text-foreground/90"
                      >
                        {skill}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </FadeIn>
          ))}
        </div>

        <div className="mt-10">
          <FadeIn>
            <Card>
              <CardHeader>
                <CardTitle>Technology radar</CardTitle>
                <CardDescription>
                  What I adopt, trial, assess, and intentionally avoid.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-5 sm:grid-cols-2">
                {technologyRadar.map((ring) => (
                  <div key={ring.ring}>
                    <p className="mb-2 text-sm font-medium text-brand">
                      {ring.ring}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {ring.items.map((item) => (
                        <span
                          key={item}
                          className="rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1 text-xs text-muted"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </FadeIn>
        </div>
      </div>
    </section>
  );
}
