export const meta = {
  name: "code-reviewer",
  description:
    "Multi-agent PR review: scout → parallel reviewers (7 categories + git-history + CLAUDE.md-compliance) → adversarial refute-verify. Report-only.",
  phases: [
    { title: "Scout", detail: "map files, languages, change-type, alignment" },
    { title: "Review", detail: "9 parallel reviewers, one criterion each" },
    { title: "Verify", detail: "adversarial refute of each CRITICAL/HIGH finding" },
  ],
};

// ── args (from SKILL.md Step 4b) ────────────────────────────────────────────
// The harness may deliver args as a JSON string; normalize to an object.
const a = typeof args === "string" ? JSON.parse(args || "{}") : (args ?? {});
const prNumber = a?.pr_number ?? null;
const base = a?.base ?? "origin/main";
const title = a?.title ?? "(untitled)";
const body = a?.body ?? "";
const isDraft = a?.is_draft ?? false;
const diff = a?.diff ?? "";
const diffPath = a?.diff_path ?? "";

if (!diff.trim() && !diffPath.trim()) {
  return { summary_hint: "No diff provided; nothing to review.", findings: [] };
}

const diffBlock = diff.trim()
  ? `DIFF:\n${diff}`
  : `The full unified diff is saved at: ${diffPath}\nRead it with the Read tool before reviewing (it is large — page through the whole file with offset/limit). Then read the actual repo source files it touches for surrounding context.`;

const draftNote = isDraft
  ? "This is a DRAFT PR — only flag blocking bugs and structural issues; skip missing docs/tests/cleanup."
  : "";

// ── schemas ─────────────────────────────────────────────────────────────────
const SCOUT_SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["languages", "change_type", "alignment", "claude_md_present", "notes"],
  properties: {
    languages: { type: "array", items: { type: "string" } },
    change_type: {
      type: "string",
      description: "feature | fix | refactor | docs | config | mixed",
    },
    alignment: {
      type: "string",
      description: "does the diff match the stated intent? note scope creep / missing pieces",
    },
    claude_md_present: { type: "boolean" },
    notes: {
      type: "string",
      description: "anything reviewers should know (hotspots, risky files)",
    },
  },
};

const FINDINGS_SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["findings"],
  properties: {
    findings: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["file", "line", "severity", "category", "problem", "fix"],
        properties: {
          file: { type: "string" },
          line: { type: "integer" },
          severity: { type: "string", enum: ["CRITICAL", "HIGH", "MEDIUM", "LOW"] },
          category: { type: "string" },
          problem: { type: "string", description: "one sentence: what is wrong" },
          fix: { type: "string", description: "one sentence: how to fix" },
        },
      },
    },
  },
};

const VERDICT_SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["refuted", "reason"],
  properties: {
    refuted: {
      type: "boolean",
      description: "true if the finding is a false positive / already handled / intentional",
    },
    reason: { type: "string" },
  },
};

// ── the 9 review lenses ─────────────────────────────────────────────────────
const LENSES = [
  {
    key: "correctness",
    prompt:
      "Logic errors, off-by-one, nil/None deref, edge cases, races, resource leaks, error handling (swallowed/wrong-type/should-propagate). Follow calls into unchanged code to check call-boundary compatibility.",
  },
  {
    key: "type-safety",
    prompt:
      "Type mismatches, unsafe casts, `any` usage, missing generics, call-boundary type compatibility.",
  },
  {
    key: "pattern-compliance",
    prompt:
      "Naming/structure/idioms diverging from surrounding code; new dependencies duplicating existing ones. Compare against neighbor files.",
  },
  {
    key: "security",
    prompt:
      "At trust boundaries only: input validation, injection, secret exposure, SSRF, path traversal, XSS, unsafe deserialization.",
  },
  {
    key: "performance",
    prompt:
      "N+1 queries, unbounded loops/growth, missing indexes/timeouts, memory leaks, large payloads, over-engineering.",
  },
  {
    key: "completeness",
    prompt:
      "Missing tests, missing error handling, incomplete migrations, missing docs for public APIs.",
  },
  {
    key: "maintainability",
    prompt:
      "Dead code, magic numbers, deep nesting (>4), functions >50 lines mixing abstraction levels, unclear naming, DRY violations, misleading/outdated comments.",
  },
  {
    key: "git-history",
    prompt:
      "Use `git log` and `git blame` on the changed files to detect regressions: does this change revert a prior fix, reintroduce a known bug, or contradict a recent intentional decision? Cite the commit.",
  },
  {
    key: "claude-md-compliance",
    prompt:
      "Read CLAUDE.md, .claude/CLAUDE.md, and .claude/rules/ in the repo. Flag any changed line that violates a project-specific rule (naming, structure, immutability, error handling, testing, commit conventions). Project rules override general principles.",
  },
];

const NOT_FLAG = `Do NOT flag: pure style preferences (unless inconsistent within the PR itself), generated code, test verbosity/DRY-in-tests, pre-existing issues in unchanged lines (mention as "pre-existing", do not count), obvious future work with a TODO, or linter/formatter territory. Only review CHANGED code. Every finding MUST carry an exact file and line; flag ambiguity rather than guessing.`;

const context = `PR: ${title}\nBase: ${base}${prNumber ? `\nPR #${prNumber}` : ""}\nDescription:\n${body || "(none)"}\n${draftNote}\n\n${diffBlock}`;

// ── Phase 1: Scout ──────────────────────────────────────────────────────────
phase("Scout");
const scout = await agent(
  `You are the scout for a code review. Map this change so reviewers can focus.\n\n${context}\n\nReport languages, change_type, whether the diff aligns with the stated intent (note scope creep or missing pieces), whether CLAUDE.md exists in the repo, and any hotspots reviewers should know.`,
  { label: "scout", phase: "Scout", schema: SCOUT_SCHEMA },
);

const scoutNote = scout
  ? `Scout notes: change_type=${scout.change_type}; languages=${(scout.languages || []).join(", ")}; alignment="${scout.alignment}"; ${scout.notes}`
  : "";

// If the diff clearly doesn't match intent, seed a CRITICAL scope-mismatch finding.
const seeded = [];
if (
  scout &&
  /scope creep|missing|unrelated|does not match|doesn't match|mismatch/i.test(scout.alignment || "")
) {
  seeded.push({
    file: "(scope)",
    line: 0,
    severity: "CRITICAL",
    category: "scope-mismatch",
    problem: `Diff may not match stated intent: ${scout.alignment}`,
    fix: "Reconcile the change with the PR description, or split unrelated changes out.",
  });
}

// ── Phase 2: Review (parallel) → Phase 3: Verify (pipeline per lens) ─────────
// pipeline: each lens's findings go straight to refute-verify as soon as that
// lens returns — no barrier between Review and Verify.
const perLens = await pipeline(
  LENSES,
  (lens) =>
    agent(
      `You are the "${lens.key}" reviewer. Review ONLY this criterion:\n${lens.prompt}\n\n${NOT_FLAG}\n\n${scoutNote}\n\n${context}`,
      { label: `review:${lens.key}`, phase: "Review", schema: FINDINGS_SCHEMA },
    ),
  (review, lens) => {
    const found = (review?.findings || []).filter(Boolean);
    // Only CRITICAL/HIGH get adversarially refuted; MEDIUM/LOW pass through.
    const toVerify = found.filter((f) => f.severity === "CRITICAL" || f.severity === "HIGH");
    const passThrough = found.filter((f) => f.severity === "MEDIUM" || f.severity === "LOW");
    return parallel(
      toVerify.map(
        (f) => () =>
          agent(
            `Adversarially REFUTE this ${f.severity} finding from the "${lens.key}" review. Default to refuted=true if uncertain — the bar is "is this a real, actionable problem in the CHANGED code?". A finding survives only if you cannot refute it.\n\nFinding: ${f.problem} (${f.file}:L${f.line})\nProposed fix: ${f.fix}\n\n${context}`,
            { label: `verify:${lens.key}:${f.file}`, phase: "Verify", schema: VERDICT_SCHEMA },
          ).then((v) => ({ finding: f, verdict: v })),
      ),
    ).then((verdicts) => {
      const survived = verdicts
        .filter(Boolean)
        .filter((x) => x.verdict && !x.verdict.refuted)
        .map((x) => x.finding);
      return [...survived, ...passThrough];
    });
  },
);

// ── Collect + rank ──────────────────────────────────────────────────────────
const RANK = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
const all = [...seeded, ...perLens.filter(Boolean).flat()];
all.sort((a, b) => (RANK[a.severity] ?? 9) - (RANK[b.severity] ?? 9));

const counts = all.reduce((m, f) => ((m[f.severity] = (m[f.severity] || 0) + 1), m), {});
const summary_hint = all.length
  ? `${title}: ${counts.CRITICAL || 0} critical, ${counts.HIGH || 0} high, ${counts.MEDIUM || 0} medium, ${counts.LOW || 0} low after refute-verify.`
  : `${title}: no blocking issues after refute-verify.`;

log(summary_hint);
return { summary_hint, findings: all };
