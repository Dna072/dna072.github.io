"use client";

import { ExternalLink } from "lucide-react";
import { productProjects } from "@/lib/product-projects";
import { FadeIn } from "@/components/motion/fade-in";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ProductProjectsSection() {
  return (
    <section id="products" className="scroll-mt-24 px-4 py-16 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <FadeIn>
          <p className="text-sm font-medium text-brand">Product & platforms</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Live systems I&apos;ve built
          </h2>
          <p className="mt-3 max-w-2xl text-muted">
            Backend and frontend development since 2017—shipping production web
            platforms with TypeScript, JavaScript, Node.js, Next.js, and Python.
          </p>
        </FadeIn>

        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {productProjects.map((project, index) => (
            <FadeIn key={project.id} delay={index * 0.05}>
              <Card className="h-full transition-colors hover:border-brand/30">
                <CardHeader>
                  <p className="text-xs text-brand">{project.highlight}</p>
                  <CardTitle className="text-xl">{project.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm leading-relaxed text-muted">
                    {project.description}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {project.stack.map((tech) => (
                      <Badge key={tech} variant="secondary">
                        {tech}
                      </Badge>
                    ))}
                  </div>
                  <Button asChild size="sm" variant="outline">
                    <a href={project.url} target="_blank" rel="noreferrer">
                      <ExternalLink className="h-3.5 w-3.5" /> Visit site
                    </a>
                  </Button>
                </CardContent>
              </Card>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
