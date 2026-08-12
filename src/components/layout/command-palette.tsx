"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  BookOpen,
  Briefcase,
  FolderGit2,
  Github,
  Home,
  Mail,
  Network,
  FileText,
} from "lucide-react";
import { siteConfig } from "@/lib/site";
import { withBasePath } from "@/lib/utils";

const links = [
  { label: "Home", href: "/", icon: Home },
  { label: "About", href: "/#about", icon: Briefcase },
  { label: "Projects", href: "/projects/", icon: FolderGit2 },
  { label: "Experience", href: "/#experience", icon: Briefcase },
  { label: "Skills", href: "/#skills", icon: Network },
  { label: "Articles", href: "/articles/", icon: BookOpen },
  { label: "Architecture", href: "/architecture/", icon: Network },
  { label: "GitHub", href: "/github/", icon: Github },
  { label: "Contact", href: "/contact/", icon: Mail },
  {
    label: "Download Resume",
    href: withBasePath(siteConfig.links.resume),
    icon: FileText,
    external: true,
  },
];

type ProjectOption = { name: string; href: string };

export function CommandPalette({
  open,
  onOpenChange,
  projects = [],
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projects?: ProjectOption[];
}) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        onOpenChange(!open);
      }
      if (event.key === "Escape") onOpenChange(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onOpenChange]);

  const filteredProjects = useMemo(() => {
    if (!query) return projects;
    return projects.filter((project) =>
      project.name.toLowerCase().includes(query.toLowerCase()),
    );
  }, [projects, query]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-start justify-center bg-black/60 px-4 pt-[12vh] backdrop-blur-sm">
      <button
        type="button"
        className="absolute inset-0 cursor-default"
        aria-label="Close command palette"
        onClick={() => onOpenChange(false)}
      />
      <Command
        className="relative z-10 w-full max-w-xl overflow-hidden rounded-2xl border border-white/10 bg-background-elevated shadow-2xl"
        label="Global command palette"
      >
        <div className="border-b border-white/10 px-4">
          <Command.Input
            value={query}
            onValueChange={setQuery}
            placeholder="Search pages and projects..."
            className="h-14 w-full bg-transparent text-sm outline-none placeholder:text-muted"
          />
        </div>
        <Command.List className="max-h-[360px] overflow-auto p-2">
          <Command.Empty className="px-3 py-8 text-center text-sm text-muted">
            No results found.
          </Command.Empty>

          <Command.Group heading="Navigate" className="px-2 py-2 text-xs text-muted">
            {links.map((link) => (
              <Command.Item
                key={link.href}
                value={link.label}
                onSelect={() => {
                  onOpenChange(false);
                  if (link.external) {
                    window.open(link.href, "_blank");
                  } else {
                    router.push(link.href);
                  }
                }}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-foreground aria-selected:bg-white/5"
              >
                <link.icon className="h-4 w-4 text-brand" />
                {link.label}
              </Command.Item>
            ))}
          </Command.Group>

          {filteredProjects.length > 0 ? (
            <Command.Group
              heading="Projects"
              className="px-2 py-2 text-xs text-muted"
            >
              {filteredProjects.map((project) => (
                <Command.Item
                  key={project.href}
                  value={project.name}
                  onSelect={() => {
                    onOpenChange(false);
                    router.push(project.href);
                  }}
                  className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-foreground aria-selected:bg-white/5"
                >
                  <FolderGit2 className="h-4 w-4 text-brand" />
                  {project.name}
                </Command.Item>
              ))}
            </Command.Group>
          ) : null}
        </Command.List>
      </Command>
    </div>
  );
}
