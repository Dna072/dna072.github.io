import Link from "next/link";
import { Github, Linkedin, Mail, MapPin } from "lucide-react";
import { siteConfig } from "@/lib/site";
import { withBasePath } from "@/lib/utils";

export function SiteFooter() {
  return (
    <footer className="border-t border-white/10 bg-background-elevated/40">
      <div className="mx-auto grid max-w-content gap-8 px-4 py-12 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr]">
        <div className="space-y-3">
          <p className="text-lg font-semibold tracking-tight">{siteConfig.name}</p>
          <p className="max-w-md text-sm leading-relaxed text-muted">
            {siteConfig.author.shortBio}
          </p>
          <p className="inline-flex items-center gap-2 text-sm text-muted">
            <MapPin className="h-4 w-4 text-brand" />
            {siteConfig.author.location}
          </p>
        </div>

        <div>
          <p className="mb-3 text-sm font-medium">Explore</p>
          <ul className="space-y-2 text-sm text-muted">
            {siteConfig.footerNavigation.map((item) => (
              <li key={item.label}>
                <Link href={item.href} className="hover:text-foreground">
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <p className="mb-3 text-sm font-medium">Connect</p>
          <ul className="space-y-2 text-sm text-muted">
            <li>
              <a
                href={siteConfig.links.github}
                className="inline-flex items-center gap-2 hover:text-foreground"
                target="_blank"
                rel="noreferrer"
              >
                <Github className="h-4 w-4" /> GitHub
              </a>
            </li>
            <li>
              <a
                href={siteConfig.links.linkedin}
                className="inline-flex items-center gap-2 hover:text-foreground"
                target="_blank"
                rel="noreferrer"
              >
                <Linkedin className="h-4 w-4" /> LinkedIn
              </a>
            </li>
            <li>
              <a
                href={siteConfig.links.email}
                className="inline-flex items-center gap-2 hover:text-foreground"
              >
                <Mail className="h-4 w-4" /> Email
              </a>
            </li>
            <li>
              <a
                href={withBasePath(siteConfig.links.resume)}
                className="hover:text-foreground"
                download
              >
                Download Resume
              </a>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10 py-4 text-center text-xs text-muted">
        © {new Date().getFullYear()} {siteConfig.name}. Built with Next.js —
        static export for GitHub Pages.
      </div>
    </footer>
  );
}
