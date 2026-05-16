export type ProjectKey = "platform" | "integrations" | "mvp";
export type ServiceKey = "engineering" | "cloud" | "integrations" | "direction";

export const projectDetails: Record<
  ProjectKey,
  { tag: string; title: string; summary: string; points: string[] }
> = {
  platform: {
    tag: "Platform",
    title: "API-first modernization",
    summary:
      "A staged modernization plan that replaced fragile legacy components while keeping existing operations stable.",
    points: [
      "Progressive migration with zero-downtime cutover strategy.",
      "Contract tests around critical APIs to reduce regressions.",
      "Release metrics dashboard for product and engineering visibility.",
    ],
  },
  integrations: {
    tag: "Integrations",
    title: "Observable cross-system integrations",
    summary:
      "An integration architecture designed for resilience, transparency, and easier ownership across teams.",
    points: [
      "Idempotent sync jobs and dead-letter handling for failed events.",
      "Distributed tracing added to key data paths.",
      "Operational runbooks for faster incident response.",
    ],
  },
  mvp: {
    tag: "Product",
    title: "MVP delivered with production discipline",
    summary:
      "A launch-ready product foundation balancing speed, product clarity, and long-term maintainability.",
    points: [
      "Component system with accessibility built in from day one.",
      "Performance budget applied to keep interfaces fast.",
      "Developer onboarding docs and handover for internal teams.",
    ],
  },
};

export const serviceDetails: Record<ServiceKey, { title: string; text: string }> = {
  engineering: {
    title: "Product & platform engineering",
    text: "We design and build scalable product foundations with maintainable code, clear boundaries, and reliable release workflows so teams can ship without fear.",
  },
  cloud: {
    title: "Cloud & infrastructure",
    text: "From CI/CD to secure environment strategy, we shape infrastructure that is cost-aware, observable, and stable under growth.",
  },
  integrations: {
    title: "Integrations & data",
    text: "We connect systems with robust event and data pipelines, giving you retry safety, auditability, and confidence in cross-tool automation.",
  },
  direction: {
    title: "Technical direction",
    text: "When priorities are unclear, we bring senior decision support: architecture audits, pragmatic roadmaps, and clear trade-off guidance.",
  },
};

export const serviceCards: {
  key: ServiceKey;
  index: string;
  title: string;
  text: string;
}[] = [
  {
    key: "engineering",
    index: "01",
    title: "Product & platform engineering",
    text: "Web applications, APIs, and internal tools—architected for clarity, performance, and long-term change.",
  },
  {
    key: "cloud",
    index: "02",
    title: "Cloud & infrastructure",
    text: "Secure deployments, CI/CD, and environments that scale with you without surprise bills or fragile scripts.",
  },
  {
    key: "integrations",
    index: "03",
    title: "Integrations & data",
    text: "Connect systems, migrate legacy surfaces, and make data flows observable so operations stay boring—in the best way.",
  },
  {
    key: "direction",
    index: "04",
    title: "Technical direction",
    text: "Pragmatic audits, roadmaps, and hands-on mentorship when you need a steady senior voice in the room.",
  },
];

export const workItems: {
  key: ProjectKey;
  tag: string;
  title: string;
  bullets: string[];
  ariaLabel: string;
}[] = [
  {
    key: "platform",
    tag: "Platform",
    title: "Modernized a legacy app into a stable API-first platform",
    bullets: [
      "Improved release confidence with tests + CI",
      "Reduced operational toil with monitoring & alerts",
      "Created a roadmap that kept scope realistic",
    ],
    ariaLabel: "View project details for API-first platform",
  },
  {
    key: "integrations",
    tag: "Integrations",
    title: "Connected systems with observable data flows",
    bullets: [
      "Designed durable sync patterns and retries",
      "Added tracing to make failures obvious",
      "Documented ownership for handover",
    ],
    ariaLabel: "View project details for integration systems",
  },
  {
    key: "mvp",
    tag: "Product",
    title: "Shipped a polished MVP with a senior delivery rhythm",
    bullets: [
      "Weekly increments with clear checkpoints",
      "Performance-focused UI and accessible components",
      "Production-ready deployment from day one",
    ],
    ariaLabel: "View project details for polished MVP",
  },
];
