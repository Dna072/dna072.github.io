"use client";

import { useState } from "react";
import { SiteHeader } from "@/components/layout/site-header";
import { SiteFooter } from "@/components/layout/site-footer";
import { CommandPalette } from "@/components/layout/command-palette";
import { ScrollProgress } from "@/components/layout/scroll-progress";

export function AppShell({
  children,
  projects = [],
}: {
  children: React.ReactNode;
  projects?: { name: string; href: string }[];
}) {
  const [commandOpen, setCommandOpen] = useState(false);

  return (
    <>
      <ScrollProgress />
      <SiteHeader onOpenCommand={() => setCommandOpen(true)} />
      <main className="min-h-[70vh]">{children}</main>
      <SiteFooter />
      <CommandPalette
        open={commandOpen}
        onOpenChange={setCommandOpen}
        projects={projects}
      />
    </>
  );
}
