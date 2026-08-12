"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu, Search, X } from "lucide-react";
import { siteConfig } from "@/lib/site";
import { cn, withBasePath } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export function SiteHeader({ onOpenCommand }: { onOpenCommand: () => void }) {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <header
      className={cn(
        "sticky top-0 z-50 border-b transition-colors",
        scrolled
          ? "glass border-white/10"
          : "border-transparent bg-transparent",
      )}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="group flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand/15 text-sm font-bold text-brand ring-1 ring-brand/30">
            DA
          </span>
          <span className="text-sm font-semibold tracking-tight sm:text-base">
            {siteConfig.name}
          </span>
        </Link>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary">
          {siteConfig.navigation.map((item) => {
            const external = "external" in item && item.external;
            const href = external ? withBasePath(item.href) : item.href;
            const Comp = external ? "a" : Link;
            return (
              <Comp
                key={item.label}
                href={href}
                className="rounded-md px-3 py-2 text-sm text-muted transition-colors hover:text-foreground"
                {...(external
                  ? { download: true, target: "_blank", rel: "noreferrer" }
                  : {})}
              >
                {item.label}
              </Comp>
            );
          })}
        </nav>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="hidden gap-2 text-muted md:inline-flex"
            onClick={onOpenCommand}
            aria-label="Open command palette"
          >
            <Search className="h-4 w-4" />
            <span className="text-xs">Search</span>
            <kbd className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px]">
              ⌘K
            </kbd>
          </Button>
          <ThemeToggle />
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setOpen((value) => !value)}
            aria-label="Toggle menu"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {open ? (
        <div className="border-t border-white/10 bg-background/95 px-4 py-4 lg:hidden">
          <nav className="flex flex-col gap-1" aria-label="Mobile">
            {siteConfig.navigation.map((item) => {
              const external = "external" in item && item.external;
              const href = external ? withBasePath(item.href) : item.href;
              const Comp = external ? "a" : Link;
              return (
                <Comp
                  key={item.label}
                  href={href}
                  className="rounded-lg px-3 py-3 text-sm text-foreground hover:bg-white/5"
                  {...(external
                    ? { download: true, target: "_blank", rel: "noreferrer" }
                    : {})}
                >
                  {item.label}
                </Comp>
              );
            })}
            <button
              type="button"
              className="rounded-lg px-3 py-3 text-left text-sm text-muted hover:bg-white/5"
              onClick={onOpenCommand}
            >
              Search / Command palette
            </button>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
