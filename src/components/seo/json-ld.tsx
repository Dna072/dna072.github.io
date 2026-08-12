import {
  personJsonLd,
  profilePageJsonLd,
  websiteJsonLd,
} from "@/lib/seo";

export function JsonLd() {
  const graph = {
    "@context": "https://schema.org",
    "@graph": [personJsonLd, websiteJsonLd, profilePageJsonLd],
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(graph) }}
    />
  );
}
