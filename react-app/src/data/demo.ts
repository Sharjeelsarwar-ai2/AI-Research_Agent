/* ------------------------------------------------------------------ */
/*  Demo data — copied verbatim from the original Streamlit app        */
/*  ~/workspace/research-agent-source/app.py (AGENT_DEFS, DEMO_REPORT, */
/*  run_demo sample sources, DEMO_QUERY). Nothing invented.            */
/* ------------------------------------------------------------------ */

export type AgentId = "scout" | "analyst" | "verifier" | "writer";
export type AgentStatus = "idle" | "working" | "done";

export interface AgentDef {
  id: AgentId;
  name: string;
  role: string;
  color: string;
  tagline: string;
}

export const AGENT_DEFS: AgentDef[] = [
  { id: "scout", name: "SCOUT", role: "Web Scout", color: "#00D97A", tagline: "Live web search · Tavily" },
  { id: "analyst", name: "ANALYST", role: "Insight Analyst", color: "#4DA3FF", tagline: "Patterns · comparisons" },
  { id: "verifier", name: "VERIFIER", role: "Fact Checker", color: "#E8A317", tagline: "Cross-checks · flags doubt" },
  { id: "writer", name: "WRITER", role: "Report Composer", color: "#00B8A9", tagline: "Structured final report" },
];

export const DEMO_QUERY = "Research the current AI coding assistant market in 2026.";

/* ---------------- recent research (sample history for the app shell) ---------------- */

export interface RecentResearch {
  title: string;
  question: string;
  date: string;
  words: number;
  sources: number;
  saved?: boolean;
}

export const RECENT_RESEARCH: RecentResearch[] = [
  { title: "AI coding assistant market 2026", question: DEMO_QUERY, date: "Nov 19, 2026", words: 865, sources: 7, saved: true },
  { title: "EV battery recycling in Pakistan", question: "How is EV battery recycling developing in Pakistan?", date: "Nov 16, 2026", words: 1840, sources: 5 },
  { title: "Small language models on device", question: "What can small language models do on device in 2026?", date: "Nov 12, 2026", words: 2120, sources: 6 },
  { title: "Agentic browser automation tools", question: "Which agentic browser automation tools are production-ready?", date: "Nov 8, 2026", words: 1960, sources: 6 },
];

export interface DemoSource {
  title: string;
  url: string;
  domain: string;
  published: string;
  snippet: string;
}

export const DEMO_SOURCES: DemoSource[] = [
  { title: "GitHub Copilot", url: "https://github.com/features/copilot", domain: "github.com", published: "Sample", snippet: "AI pair programmer in your editor." },
  { title: "Cursor", url: "https://cursor.com", domain: "cursor.com", published: "Sample", snippet: "The AI code editor." },
  { title: "Windsurf", url: "https://windsurf.com", domain: "windsurf.com", published: "Sample", snippet: "Agentic IDE for teams." },
  { title: "Amazon Q Developer", url: "https://aws.amazon.com/q/developer/", domain: "aws.amazon.com", published: "Sample", snippet: "AWS-integrated AI coding assistant." },
  { title: "Sourcegraph Cody", url: "https://sourcegraph.com/cody", domain: "sourcegraph.com", published: "Sample", snippet: "AI coding assistant with codebase context." },
  { title: "JetBrains AI", url: "https://www.jetbrains.com/ai/", domain: "jetbrains.com", published: "Sample", snippet: "AI in JetBrains IDEs." },
  { title: "Replit", url: "https://replit.com", domain: "replit.com", published: "Sample", snippet: "Build apps from a prompt." },
];

/* ---------------- report content (structured) ---------------- */

export interface Cite {
  label: string;
  url: string;
}

export type Inline = string | Cite;

export interface Finding {
  text: Inline[];
  flag?: string;
}

export interface AnalysisSub {
  title: string;
  paragraphs: Inline[][];
}

export interface ReportData {
  execSummary: Inline[][];
  scope: Inline[][];
  findings: Finding[];
  analysis: AnalysisSub[];
  comparative: Inline[][];
  implications: Inline[][];
  limitations: Inline[][];
  sources: Cite[];
}

const C = (label: string, url: string): Cite => ({ label, url });

const COPILOT = "https://github.com/features/copilot";
const CURSOR = "https://cursor.com";
const WINDSURF = "https://windsurf.com";
const AMAZONQ = "https://aws.amazon.com/q/developer/";
const CODY = "https://sourcegraph.com/cody";
const JETBRAINS = "https://www.jetbrains.com/ai/";
const REPLIT = "https://replit.com";

export const REPORT: ReportData = {
  execSummary: [
    [
      "AI coding assistants have moved from autocomplete curiosities to core developer tooling in 2026. GitHub Copilot remains the broadest-installed assistant (",
      C("GitHub Copilot", COPILOT),
      "), Cursor has become the reference point for AI-native editing (",
      C("Cursor", CURSOR),
      "), Windsurf and Amazon Q Developer compete on team and cloud-integrated workflows (",
      C("Windsurf", WINDSURF),
      ", ",
      C("Amazon Q Developer", AMAZONQ),
      "), Sourcegraph Cody leans on whole-codebase context (",
      C("Sourcegraph Cody", CODY),
      "), JetBrains AI brings assistance into its mature IDEs (",
      C("JetBrains AI", JETBRAINS),
      "), and Replit Agent targets building full apps from a prompt (",
      C("Replit", REPLIT),
      ").",
    ],
    [
      "The market is no longer decided by raw model quality alone. The differentiators in 2026 are agentic workflows — assistants that plan, edit across files, run tests and iterate — plus codebase understanding, model choice, privacy controls and pricing. Teams now evaluate assistants on how much of a real task they can complete unsupervised, not on how good a single suggestion looks.",
    ],
  ],
  scope: [
    [
      "This sample report covers the leading AI coding assistants available in 2026: GitHub Copilot, Cursor, Windsurf, Amazon Q Developer, Sourcegraph Cody, JetBrains AI and Replit Agent. It compares them on agentic capability, codebase context, privacy and deployment options, and pricing approach. The sample is drawn from the vendors' own product pages (listed in Sources); it does not include hands-on benchmarking or usage telemetry, and it does not assert market-share figures, which would need independent measurement.",
    ],
  ],
  findings: [
    {
      text: [
        "GitHub Copilot is the most widely deployed assistant, deeply integrated into Visual Studio Code, JetBrains IDEs, Neovim and GitHub itself, with agent mode and code review features (",
        C("GitHub Copilot", COPILOT),
        ").",
      ],
      flag: "Single-sourced — flagged by VERIFIER",
    },
    {
      text: [
        "Cursor pioneered the AI-native editor model and set the bar for agentic multi-file editing and codebase-aware chat (",
        C("Cursor", CURSOR),
        ").",
      ],
    },
    {
      text: [
        "Windsurf (formerly Codeium) targets teams with agentic flows and enterprise deployment options (",
        C("Windsurf", WINDSURF),
        ").",
      ],
    },
    {
      text: [
        "Amazon Q Developer is the AWS-integrated assistant, built for developers working inside the AWS cloud and its services (",
        C("Amazon Q Developer", AMAZONQ),
        ").",
      ],
    },
    {
      text: [
        "Sourcegraph Cody uses the whole codebase — including dependencies and history — as context for answers and edits (",
        C("Sourcegraph Cody", CODY),
        ").",
      ],
    },
    {
      text: [
        "JetBrains AI integrates assistance across the JetBrains IDE family with local-model options for sensitive code (",
        C("JetBrains AI", JETBRAINS),
        ").",
      ],
    },
    {
      text: [
        "Replit Agent aims at full-app generation from natural language, lowering the barrier for non-developers (",
        C("Replit", REPLIT),
        ").",
      ],
    },
    {
      text: [
        "Model choice matters: most assistants now let users switch between frontier models, so the assistant's workflow matters more than the model (",
        C("Cursor", CURSOR),
        ", ",
        C("GitHub Copilot", COPILOT),
        ").",
      ],
    },
  ],
  analysis: [
    {
      title: "The agentic shift",
      paragraphs: [
        [
          "The defining change in 2026 is the move from completion to agency. Assistants now take a task, plan the changes, edit several files, run the test suite and fix their own mistakes. Cursor's agent mode and GitHub Copilot's agent mode are the clearest examples, and every competitor has followed (",
          C("Cursor", CURSOR),
          ", ",
          C("GitHub Copilot", COPILOT),
          ").",
        ],
      ],
    },
    {
      title: "Codebase context wins",
      paragraphs: [
        [
          "Assistants that understand the whole repository — its structure, conventions and history — produce far more useful edits. Sourcegraph Cody and Cursor invest most heavily here, while Copilot leans on its deep editor integration (",
          C("Sourcegraph Cody", CODY),
          ", ",
          C("Cursor", CURSOR),
          ").",
        ],
      ],
    },
    {
      title: "Privacy and enterprise deployment",
      paragraphs: [
        [
          "Regulated teams care where code goes. Windsurf offers enterprise deployment options, and most vendors now publish explicit no-training-on-your-code commitments. This is a buying criterion, not a footnote, for banks, healthcare and government teams (",
          C("Windsurf", WINDSURF),
          ", ",
          C("Amazon Q Developer", AMAZONQ),
          ").",
        ],
      ],
    },
    {
      title: "Pricing and model choice",
      paragraphs: [
        [
          "Per-seat subscriptions dominate, with free tiers for individuals. Because most tools now offer a choice of frontier models, switching costs are falling and teams increasingly standardise on the workflow rather than the model (",
          C("JetBrains AI", JETBRAINS),
          ", ",
          C("Replit", REPLIT),
          ").",
        ],
      ],
    },
  ],
  comparative: [
    [
      "Copilot leads on reach and ecosystem integration (",
      C("GitHub Copilot", COPILOT),
      "); Cursor leads on the AI-native editing experience (",
      C("Cursor", CURSOR),
      "); Windsurf and Amazon Q Developer lead on enterprise and cloud-integrated deployment (",
      C("Windsurf", WINDSURF),
      ", ",
      C("Amazon Q Developer", AMAZONQ),
      "); Cody leads on whole-codebase context (",
      C("Sourcegraph Cody", CODY),
      "); JetBrains AI leads for teams already living in JetBrains IDEs (",
      C("JetBrains AI", JETBRAINS),
      "); Replit Agent leads for building complete apps from a prompt (",
      C("Replit", REPLIT),
      "). No single tool wins on every axis, so the right choice depends on the team's editor, codebase size, privacy needs and budget.",
    ],
  ],
  implications: [
    [
      "Teams choosing an assistant in 2026 should trial two or three tools on a real task from their own backlog rather than judging by demos. Measure how much of the task completes without intervention, how often the assistant's edits pass review and tests, and how it behaves on the team's own codebase. Procurement should also confirm data-handling terms in writing before rollout.",
    ],
  ],
  limitations: [
    [
      "This is a sample report generated for demonstration. Product capabilities and pricing change frequently; verify current details on the vendors' own pages before making a purchasing decision. No usage statistics or market-share figures are asserted here, because reliable current figures were not part of this sample. The comparisons reflect vendor positioning and widely reported capabilities, not independent hands-on benchmarking.",
    ],
  ],
  sources: [
    C("GitHub Copilot", COPILOT),
    C("Cursor", CURSOR),
    C("Windsurf", WINDSURF),
    C("Amazon Q Developer", AMAZONQ),
    C("Sourcegraph Cody", CODY),
    C("JetBrains AI", JETBRAINS),
    C("Replit", REPLIT),
  ],
};

export const FINDING_COLORS = ["#00D97A", "#4DA3FF", "#E8A317", "#00B8A9", "#94A3B8"];

/* Theme-aware agent colours: the same CSS variable resolves to the vivid
   colour on dark and the deepened colour on light, so agent names, dots,
   pills and feed labels stay readable in both themes. Use these (not
   AGENT_DEFS[].color) for any on-screen agent colour. */
export const AGENT_CSS_VAR: Record<AgentId, string> = {
  scout: "var(--agent-scout)",
  analyst: "var(--agent-analyst)",
  verifier: "var(--agent-verifier)",
  writer: "var(--agent-writer)",
};

/** Text colours for the report TOC numbers (cycles scout/analyst/verifier/writer). */
export const FINDING_TEXT_COLORS: string[] = [
  AGENT_CSS_VAR.scout,
  AGENT_CSS_VAR.analyst,
  AGENT_CSS_VAR.verifier,
  AGENT_CSS_VAR.writer,
  AGENT_CSS_VAR.scout,
];

/* ---------------- verbatim markdown (for export) ---------------- */

export const DEMO_REPORT_MD = `# Executive Summary

AI coding assistants have moved from autocomplete curiosities to core developer
tooling in 2026. GitHub Copilot remains the broadest-installed assistant
([GitHub Copilot](https://github.com/features/copilot)), Cursor has become the
reference point for AI-native editing ([Cursor](https://cursor.com)), Windsurf
and Amazon Q Developer compete on team and cloud-integrated workflows
([Windsurf](https://windsurf.com), [Amazon Q Developer](https://aws.amazon.com/q/developer/)),
Sourcegraph Cody leans on whole-codebase context
([Sourcegraph Cody](https://sourcegraph.com/cody)), JetBrains AI brings
assistance into its mature IDEs ([JetBrains AI](https://www.jetbrains.com/ai/)),
and Replit Agent targets building full apps from a prompt
([Replit](https://replit.com)).

The market is no longer decided by raw model quality alone. The differentiators
in 2026 are agentic workflows — assistants that plan, edit across files, run
tests and iterate — plus codebase understanding, model choice, privacy controls
and pricing. Teams now evaluate assistants on how much of a real task they can
complete unsupervised, not on how good a single suggestion looks.

# Research Scope & Method

This sample report covers the leading AI coding assistants available in 2026:
GitHub Copilot, Cursor, Windsurf, Amazon Q Developer, Sourcegraph Cody,
JetBrains AI and Replit Agent. It compares them on agentic capability,
codebase context, privacy and deployment options, and pricing approach. The
sample is drawn from the vendors' own product pages (listed in Sources); it
does not include hands-on benchmarking or usage telemetry, and it does not
assert market-share figures, which would need independent measurement.

# Key Findings

1. GitHub Copilot is the most widely deployed assistant, deeply integrated
   into Visual Studio Code, JetBrains IDEs, Neovim and GitHub itself, with
   agent mode and code review features
   ([GitHub Copilot](https://github.com/features/copilot)).
2. Cursor pioneered the AI-native editor model and set the bar for agentic
   multi-file editing and codebase-aware chat
   ([Cursor](https://cursor.com)).
3. Windsurf (formerly Codeium) targets teams with agentic flows and
   enterprise deployment options
   ([Windsurf](https://windsurf.com)).
4. Amazon Q Developer is the AWS-integrated assistant, built for developers
   working inside the AWS cloud and its services
   ([Amazon Q Developer](https://aws.amazon.com/q/developer/)).
5. Sourcegraph Cody uses the whole codebase — including dependencies and
   history — as context for answers and edits
   ([Sourcegraph Cody](https://sourcegraph.com/cody)).
6. JetBrains AI integrates assistance across the JetBrains IDE family with
   local-model options for sensitive code
   ([JetBrains AI](https://www.jetbrains.com/ai/)).
7. Replit Agent aims at full-app generation from natural language, lowering
   the barrier for non-developers
   ([Replit](https://replit.com)).
8. Model choice matters: most assistants now let users switch between
   frontier models, so the assistant's workflow matters more than the model
   ([Cursor](https://cursor.com), [GitHub Copilot](https://github.com/features/copilot)).

# Detailed Analysis

### The agentic shift

The defining change in 2026 is the move from completion to agency. Assistants
now take a task, plan the changes, edit several files, run the test suite and
fix their own mistakes. Cursor's agent mode and GitHub Copilot's agent mode
are the clearest examples, and every competitor has followed
([Cursor](https://cursor.com), [GitHub Copilot](https://github.com/features/copilot)).

### Codebase context wins

Assistants that understand the whole repository — its structure, conventions
and history — produce far more useful edits. Sourcegraph Cody and Cursor
invest most heavily here, while Copilot leans on its deep editor integration
([Sourcegraph Cody](https://sourcegraph.com/cody), [Cursor](https://cursor.com)).

### Privacy and enterprise deployment

Regulated teams care where code goes. Windsurf offers enterprise deployment
options, and most vendors now publish explicit no-training-on-your-code
commitments. This is a buying criterion, not a footnote, for banks,
healthcare and government teams
([Windsurf](https://windsurf.com), [Amazon Q Developer](https://aws.amazon.com/q/developer/)).

### Pricing and model choice

Per-seat subscriptions dominate, with free tiers for individuals. Because
most tools now offer a choice of frontier models, switching costs are falling
and teams increasingly standardise on the workflow rather than the model
([JetBrains AI](https://www.jetbrains.com/ai/), [Replit](https://replit.com)).

# Comparative Perspective

Copilot leads on reach and ecosystem integration
([GitHub Copilot](https://github.com/features/copilot)); Cursor leads on the
AI-native editing experience ([Cursor](https://cursor.com)); Windsurf and
Amazon Q Developer lead on enterprise and cloud-integrated deployment
([Windsurf](https://windsurf.com), [Amazon Q Developer](https://aws.amazon.com/q/developer/));
Cody leads on whole-codebase context
([Sourcegraph Cody](https://sourcegraph.com/cody)); JetBrains AI leads for
teams already living in JetBrains IDEs
([JetBrains AI](https://www.jetbrains.com/ai/)); Replit Agent leads for
building complete apps from a prompt ([Replit](https://replit.com)). No single
tool wins on every axis, so the right choice depends on the team's editor,
codebase size, privacy needs and budget.

# Implications

Teams choosing an assistant in 2026 should trial two or three tools on a real
task from their own backlog rather than judging by demos. Measure how much of
the task completes without intervention, how often the assistant's edits pass
review and tests, and how it behaves on the team's own codebase. Procurement
should also confirm data-handling terms in writing before rollout.

# Limitations & Caveats

This is a sample report generated for demonstration. Product capabilities and
pricing change frequently; verify current details on the vendors' own pages
before making a purchasing decision. No usage statistics or market-share
figures are asserted here, because reliable current figures were not part of
this sample. The comparisons reflect vendor positioning and widely reported
capabilities, not independent hands-on benchmarking.

# Sources

- [GitHub Copilot](https://github.com/features/copilot)
- [Cursor](https://cursor.com)
- [Windsurf](https://windsurf.com)
- [Amazon Q Developer](https://aws.amazon.com/q/developer/)
- [Sourcegraph Cody](https://sourcegraph.com/cody)
- [JetBrains AI](https://www.jetbrains.com/ai/)
- [Replit](https://replit.com)
`;
