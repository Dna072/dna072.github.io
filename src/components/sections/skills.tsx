"use client";

import { motion } from "framer-motion";
import { skillCategories, technologyRadar } from "@/lib/skills";
import { FadeIn } from "@/components/motion/fade-in";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { SkillGraph } from "@/components/sections/skill-graph";

export function SkillsSection() {
  return (
    <section id="skills" className="scroll-mt-24 px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <FadeIn>
          <p className="text-sm font-medium text-brand">Skills</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Strongest technologies
          </h2>
          <p className="mt-3 max-w-2xl text-muted">
            Categorized strengths across programming, data engineering, cloud,
            and software delivery.
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
                <CardContent className="space-y-4">
                  {category.skills.map((skill) => (
                    <div key={skill.name}>
                      <div className="mb-1.5 flex items-center justify-between text-sm">
                        <span>{skill.name}</span>
                        <span className="text-muted">{skill.level}%</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                        <motion.div
                          className="h-full rounded-full bg-brand"
                          initial={{ width: 0 }}
                          whileInView={{ width: `${skill.level}%` }}
                          viewport={{ once: true }}
                          transition={{ duration: 0.8, ease: "easeOut" }}
                        />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </FadeIn>
          ))}
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <FadeIn>
            <Card className="h-full">
              <CardHeader>
                <CardTitle>Animated skill graph</CardTitle>
                <CardDescription>
                  Relative proficiency across core platform capabilities.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <SkillGraph />
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.08}>
            <Card className="h-full">
              <CardHeader>
                <CardTitle>Technology radar</CardTitle>
                <CardDescription>
                  What I adopt, trial, assess, and intentionally avoid.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
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
