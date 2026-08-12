import type { Metadata } from "next";
import { architectureDiagrams } from "@/lib/architecture";
import { MermaidDiagram } from "@/components/diagrams/mermaid";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Architecture Showcase",
  description:
    "Engineering diagrams for ETL, lakehouse, warehouse, streaming, and Airflow DAG patterns.",
};

export default function ArchitecturePage() {
  return (
    <div className="px-4 py-16 sm:px-6">
      <div className="mx-auto max-w-content">
        <p className="text-sm font-medium text-brand">Architecture</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">
          Engineering diagrams
        </h1>
        <p className="mt-3 max-w-2xl text-muted">
          Reference architectures I use when designing scalable data platforms.
          Diagrams render with Mermaid for clarity and maintainability.
        </p>

        <div className="mt-10 space-y-8">
          {architectureDiagrams.map((diagram) => (
            <Card key={diagram.id} id={diagram.id}>
              <CardHeader>
                <CardTitle>{diagram.title}</CardTitle>
                <CardDescription>{diagram.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-auto rounded-xl border border-white/10 bg-white/[0.02] p-4">
                  <MermaidDiagram chart={diagram.mermaid} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
