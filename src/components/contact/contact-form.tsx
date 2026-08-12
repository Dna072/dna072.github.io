"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { siteConfig } from "@/lib/site";

export function ContactForm() {
  const [status, setStatus] = useState<"idle" | "ready">("idle");

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        const name = String(form.get("name") ?? "");
        const email = String(form.get("email") ?? "");
        const message = String(form.get("message") ?? "");
        const subject = encodeURIComponent(`Portfolio inquiry from ${name}`);
        const body = encodeURIComponent(
          `Name: ${name}\nEmail: ${email}\n\n${message}`,
        );
        window.location.href = `mailto:${siteConfig.author.email}?subject=${subject}&body=${body}`;
        setStatus("ready");
      }}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="name" className="mb-1.5 block text-sm">
            Name
          </label>
          <Input id="name" name="name" required placeholder="Alex Recruiter" />
        </div>
        <div>
          <label htmlFor="email" className="mb-1.5 block text-sm">
            Email
          </label>
          <Input
            id="email"
            name="email"
            type="email"
            required
            placeholder="alex@company.com"
          />
        </div>
      </div>
      <div>
        <label htmlFor="message" className="mb-1.5 block text-sm">
          Message
        </label>
        <Textarea
          id="message"
          name="message"
          required
          placeholder="Tell me about the role, team, and timeline..."
        />
      </div>
      <Button type="submit" size="lg">
        Send message
      </Button>
      {status === "ready" ? (
        <p className="text-sm text-muted">
          Opening your email client… If nothing opens, email{" "}
          <a className="text-brand" href={siteConfig.links.email}>
            {siteConfig.author.email}
          </a>
          .
        </p>
      ) : null}
    </form>
  );
}
