import type { Metadata } from "next";
import Link from "next/link";
import { getAllArticles } from "@/lib/articles";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Articles",
  description:
    "Articles on modern data pipelines, warehousing, analytics engineering, Airflow, and AWS Glue.",
};

export default function ArticlesPage() {
  const articles = getAllArticles();

  return (
    <div className="px-4 py-16 sm:px-6">
      <div className="mx-auto max-w-content">
        <p className="text-sm font-medium text-brand">Articles</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">
          Writing on data platforms
        </h1>
        <p className="mt-3 max-w-2xl text-muted">
          Markdown-powered articles. Drop a new{" "}
          <code className="text-brand">.md</code> file into{" "}
          <code className="text-brand">content/articles</code> and it appears
          automatically on the next build.
        </p>

        <div className="mt-10 grid gap-5 md:grid-cols-2">
          {articles.map((article) => (
            <Card key={article.slug} className="transition-colors hover:border-brand/30">
              <CardHeader>
                <p className="text-xs text-muted">
                  {formatDate(article.date)} · {article.readingTime}
                </p>
                <CardTitle className="text-xl">
                  <Link
                    href={`/articles/${article.slug}/`}
                    className="hover:text-brand"
                  >
                    {article.title}
                  </Link>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted">{article.description}</p>
                <div className="flex flex-wrap gap-2">
                  {article.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
