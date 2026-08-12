import type { Metadata } from "next";
import { Github, Linkedin, Mail, MapPin } from "lucide-react";
import { ContactForm } from "@/components/contact/contact-form";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { siteConfig } from "@/lib/site";

export const metadata: Metadata = {
  title: "Contact",
  description:
    "Contact Derrick Adjei for Data Engineer, Analytics Engineer, and Software Engineer opportunities.",
};

export default function ContactPage() {
  return (
    <div className="px-4 py-16 sm:px-6">
      <div className="mx-auto grid max-w-content gap-8 lg:grid-cols-[1fr_1.1fr]">
        <div>
          <p className="text-sm font-medium text-brand">Contact</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">
            Let&apos;s talk platforms
          </h1>
          <p className="mt-3 text-muted">
            Recruiters and hiring managers—reach out about data platform roles,
            analytics engineering, or technical conversations.
          </p>

          <Card className="mt-8">
            <CardHeader>
              <CardTitle>Direct channels</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <a
                href={siteConfig.links.email}
                className="flex items-center gap-3 text-muted hover:text-foreground"
              >
                <Mail className="h-4 w-4 text-brand" />
                {siteConfig.author.email}
              </a>
              <a
                href={siteConfig.links.linkedin}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-3 text-muted hover:text-foreground"
              >
                <Linkedin className="h-4 w-4 text-brand" />
                LinkedIn
              </a>
              <a
                href={siteConfig.links.github}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-3 text-muted hover:text-foreground"
              >
                <Github className="h-4 w-4 text-brand" />
                GitHub
              </a>
              <p className="flex items-center gap-3 text-muted">
                <MapPin className="h-4 w-4 text-brand" />
                {siteConfig.author.location}
              </p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Send a message</CardTitle>
          </CardHeader>
          <CardContent>
            <ContactForm />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
