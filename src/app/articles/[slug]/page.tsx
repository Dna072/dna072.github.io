import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getAllArticles, getArticle, getArticleSlugs } from "@/lib/articles";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { ReadingProgress } from "@/components/layout/reading-progress";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return getArticleSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const article = await getArticle(slug);
  if (!article) return { title: "Article" };
  return {
    title: article.title,
    description: article.description,
    openGraph: {
      title: article.title,
      description: article.description,
      type: "article",
      publishedTime: article.date,
    },
  };
}

export default async function ArticlePage({ params }: Props) {
  const { slug } = await params;
  const article = await getArticle(slug);
  if (!article) notFound();

  const related = getAllArticles()
    .filter((item) => item.slug !== slug)
    .slice(0, 3);

  return (
    <>
      <ReadingProgress targetId="article-body" />
      <article className="px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-3xl">
          <p className="text-sm text-muted">
            {formatDate(article.date)} · {article.readingTime}
          </p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight">
            {article.title}
          </h1>
          <p className="mt-4 text-lg text-muted">{article.description}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {article.tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>

          <div
            id="article-body"
            className="prose prose-invert prose-portfolio mt-10 max-w-none"
            dangerouslySetInnerHTML={{ __html: article.contentHtml }}
          />

          <div className="mt-16 border-t border-white/10 pt-8">
            <h2 className="text-xl font-semibold">More articles</h2>
            <ul className="mt-4 space-y-3">
              {related.map((item) => (
                <li key={item.slug}>
                  <Link
                    href={`/articles/${item.slug}/`}
                    className="text-muted hover:text-brand"
                  >
                    {item.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </article>
    </>
  );
}
