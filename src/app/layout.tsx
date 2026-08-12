import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, Manrope } from "next/font/google";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { AppShell } from "@/components/layout/app-shell";
import { JsonLd } from "@/components/seo/json-ld";
import { siteConfig } from "@/lib/site";
import { seoKeywords } from "@/lib/seo";
import { getFeaturedRepos } from "@/lib/github";
import "./globals.css";

/** Absolute asset URL under the GitHub Pages project base path. */
function assetUrl(path: string) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  // Cache-bust so browsers pick up favicon replacements.
  return `${siteConfig.url}${normalized}?v=4`;
}

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
  display: "swap",
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.url),
  title: {
    default: siteConfig.title,
    template: `%s | ${siteConfig.name}`,
  },
  description: siteConfig.description,
  keywords: [...seoKeywords],
  authors: [{ name: siteConfig.author.name, url: siteConfig.url }],
  creator: siteConfig.author.name,
  publisher: siteConfig.author.name,
  category: "technology",
  openGraph: {
    type: "website",
    locale: siteConfig.locale,
    url: siteConfig.url,
    title: siteConfig.title,
    description: siteConfig.description,
    siteName: siteConfig.name,
    images: [
      {
        url: "/og.png",
        width: 1200,
        height: 630,
        alt: siteConfig.title,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: siteConfig.title,
    description: siteConfig.description,
    creator: "@dna072",
    images: ["/og.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
  icons: {
    // Prefer ICO/PNG first — more reliable in Chromium tabs than SVG text marks.
    icon: [
      {
        url: assetUrl("/favicon.ico"),
        sizes: "16x16 32x32 48x48",
        type: "image/x-icon",
      },
      {
        url: assetUrl("/favicon-32.png"),
        sizes: "32x32",
        type: "image/png",
      },
      {
        url: assetUrl("/favicon.svg"),
        type: "image/svg+xml",
      },
    ],
    shortcut: assetUrl("/favicon.ico"),
    apple: [
      {
        url: assetUrl("/apple-touch-icon.png"),
        sizes: "180x180",
      },
    ],
  },
  alternates: {
    canonical: siteConfig.url,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#09090b" },
    { media: "(prefers-color-scheme: light)", color: "#fafafa" },
  ],
  width: "device-width",
  initialScale: 1,
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const featured = await getFeaturedRepos();
  const projectOptions = featured.map((repo) => ({
    name: repo.name,
    href: `/projects/${repo.name}/`,
  }));

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link
          rel="icon"
          href={assetUrl("/favicon.ico")}
          sizes="any"
        />
        <link
          rel="icon"
          href={assetUrl("/favicon-32.png")}
          type="image/png"
          sizes="32x32"
        />
        <link
          rel="apple-touch-icon"
          href={assetUrl("/apple-touch-icon.png")}
          sizes="180x180"
        />
      </head>
      <body
        className={`${manrope.variable} ${ibmPlexMono.variable} antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <JsonLd />
          <AppShell projects={projectOptions}>{children}</AppShell>
        </ThemeProvider>
      </body>
    </html>
  );
}
