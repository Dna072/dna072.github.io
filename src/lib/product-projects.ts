export type ProductProject = {
  id: string;
  name: string;
  url: string;
  description: string;
  stack: string[];
  highlight: string;
};

/** Live product / platform work beyond GitHub data-engineering repos. */
export const productProjects: ProductProject[] = [
  {
    id: "medlink",
    name: "MedLink",
    url: "https://medlink.nexdev.tech",
    description:
      "Full-stack product experience spanning frontend UX and backend services for a modern web platform.",
    stack: ["TypeScript", "React", "Next.js", "Vite", "Node.js", "Tailwind CSS"],
    highlight: "Frontend + backend product delivery",
  },
  {
    id: "arctiq",
    name: "Arctiq",
    url: "https://arctiq.nexdev.tech",
    description:
      "Web application built with modern JavaScript/TypeScript tooling, emphasizing responsive UI and API-backed workflows.",
    stack: ["TypeScript", "JavaScript", "React", "Vite", "Next.js", "Express", "Tailwind CSS"],
    highlight: "End-to-end web application",
  },
  {
    id: "tpg-ntc",
    name: "TPG — National Teaching Council",
    url: "https://tpg.ntc.gov.gh",
    description:
      "Public-sector web platform supporting teaching profession workflows for the National Teaching Council of Ghana.",
    stack: ["JavaScript", "Node.js", "Python", "PostgreSQL"],
    highlight: "Production government platform",
  },
];
