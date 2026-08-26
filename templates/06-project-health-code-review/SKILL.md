---
name: project-health-code-review
description: Repository-level code review that evaluates a change globally across requirements, architecture, cleanliness, functionality, memory/resource usage, performance, reliability, security, operations, and tests. Use when reviewing a branch, pull request, commit range, bug fix, feature, refactor, or work-in-progress in one of the user's local projects; build repository context and change impact before judging individual lines.
---

# Project Health Code Review

## Purpose

Review a change as a maintainer responsible for the whole project, not as a local diff critic. Reconstruct the repository's purpose and dependency map first, then connect the change to requirements, callers, state transitions, tests, and runtime resources. Report only evidence-backed findings; separate confirmed defects, high-confidence risks, and hypotheses that need profiling or human confirmation.

This skill is a review skill, not an auto-fixer. Do not modify code, create tracking tasks, approve/merge PRs, or run production actions unless the user explicitly asks.

## Research-informed principles

- Diff-only review is insufficient. Include the issue/spec, surrounding function or class, repository rules, relevant callers/callees, and test context.
- A review comment is useful only when it identifies a real risk, explains why it matters in this project, and gives a verifiable next step.
- Use program analysis and deterministic checks as evidence; use the model for synthesis, prioritization, and reasoning across artifacts.
- Do not confuse faster review with better review. A human remains responsible for high-risk decisions and unresolved uncertainty.
- Review the whole change path: intent -> entry point -> state/data flow -> side effects -> failure/retry/cancel path -> observability -> tests -> rollback or compatibility.
- Use two independent reviewer roles before debate. Independent first-pass reasoning reduces anchoring; debate is for resolving evidence-backed disagreements, not for generating more opinions.
- Treat code-writing quality and Code Rot as one maintainability axis: review both what the change does now and whether it makes the repository harder to change later.

See references/research-foundations.md for the papers and design decisions derived from them.

## Required input

Identify:

1. repo_path: absolute repository path.
2. fixed_point: target branch, merge-base, commit, tag, or HEAD~N. If absent, ask for it before reviewing.
3. spec_source: issue, PRD, task, acceptance criteria, or a clear statement that no spec exists.

Pin and validate the reference before analysis:

    git -C <repo_path> rev-parse <fixed_point>
    git -C <repo_path> diff --stat <fixed_point>...HEAD
    git -C <repo_path> log --oneline <fixed_point>..HEAD

An invalid reference or empty diff is a stop condition. Preserve existing uncommitted changes and do not use destructive Git commands.

## Review workflow

### 1. Build the repository map before reading the diff

Read the smallest set of high-value context first:

- AGENTS.md, CLAUDE.md, CONTRIBUTING.md, coding standards, ADRs, architecture docs;
- package manifests and lockfiles;
- CI, Makefiles, task runners, test configuration, and deploy manifests;
- entry points, routes/controllers, workers, repositories, shared libraries, and domain boundaries;
- the project's existing test and profiling scripts.

Use codebase-memory-mcp before broad file-by-file searching when the project is indexed:

    codebase-memory-mcp cli list_projects
    codebase-memory-mcp cli get_architecture '{"project":"<name>"}'
    codebase-memory-mcp cli detect_changes '{"project":"<name>"}'

For important changed symbols, use trace_path in both directions. If the graph is stale, say so and fall back to direct code inspection; do not present stale graph results as facts.

Use scripts/collect_review_context.py to create a deterministic first-pass context bundle when useful.

### 2. Reconstruct intent and system flow

Before judging implementation, write a short internal flow map:

    user/event -> entry point -> service/agent -> state/data store -> external side effect
              -> success path / failure path / retry path / cancel path
              -> observable signal -> test or operational verification

For each changed file, classify its role: API, domain logic, orchestration, persistence, transport, shared library, UI, worker, configuration, test, migration, or deployment. Identify the nearest upstream callers and downstream consumers.

If the change has no usable spec, review functionality as “intent not verifiable” rather than inventing requirements. Still review safety, compatibility, and regressions.

### 3. Determine blast radius and risk

Mark each change with:

- direct impact: changed functions, classes, routes, schemas, configs, tests;
- indirect impact: callers, implementers, shared utilities, data models, workers, clients;
- state impact: database, cache, queue, files, sessions, credentials, browser state;
- runtime impact: memory, CPU, IO, network, goroutines/tasks, connection pools, model tokens;
- operational impact: deploy order, migration, rollback, feature flag, alerting, compatibility.
- maintainability impact: complexity, duplication, dead/obsolete paths, churn hotspots, test decay, and architecture drift.

Prioritize findings using severity and confidence, not a decorative overall score:

- P0 BLOCK: security, data loss, corruption, outage, privilege escalation, or an unbounded resource failure;
- P1 HIGH: likely production bug, broken contract, incorrect business behavior, or missing critical failure path;
- P2 MEDIUM: maintainability, performance, test, observability, or compatibility risk that should be fixed before merge when practical;
- P3 LOW: localized cleanup or non-blocking improvement.

Confidence is confirmed, high, medium, or needs-runtime-verification.

### 4. Run two independent review passes

Dispatch two isolated reviewer roles in parallel when subagents are available. Give both the same repository map, fixed diff, spec, graph context, and validation facts, but do not expose either reviewer's findings to the other during the first pass.

Maintainer reviewer:

- functionality and requirement coverage;
- code-writing quality, maintainability, YAGNI, and Code Rot baseline;
- architecture, contracts, callers, and downstream impact;
- tests, observability, rollout, and compatibility.

Adversarial reviewer:

- invalid input, partial failure, timeout, retry, cancellation, and duplicate execution;
- memory/resource ownership, unbounded growth, connection/task/handle cleanup, and backpressure;
- security boundaries, permissions, secrets, sandbox, prompt/tool input, and data leakage;
- concurrency, data consistency, rollback, operational failure, and whether the change adds another layer to an existing maintenance hotspot.

If no subagent mechanism is available, perform two clearly separated passes in one context and do not let the second pass see the first pass's findings until its own candidate list is complete.

Each reviewer must produce candidate findings with location, evidence, causal path, consequence, severity, confidence, and the smallest verification or fix. A reviewer must also report important paths that were checked and found sound.

### 5. Debate only high-value disagreements

Use references/debate-protocol.md. Do not debate every stylistic difference. Debate any P0 or P1 finding rejected by the other reviewer, disagreements about contracts/architecture/resource lifecycle/security, and P2 disagreements that change the merge decision or require expensive runtime validation.

The debate has a fixed budget: at most two rounds and at most eight disagreement packets per review. Do not use majority vote. If evidence remains insufficient, downgrade the finding to needs-runtime-verification and design the smallest distinguishing check.

### 6. Review the change through the project-health lenses

Read references/review-lenses.md and references/code-rot.md and apply only the relevant lenses. Always cover functionality, code-writing quality, Code Rot, architecture, tests, and reliability. Add resource/performance/security/operations lenses when the risk map triggers them.

For every finding, answer:

1. What exact behavior or design is problematic?
2. Where is the evidence: file, line, call path, test, config, or runtime result?
3. Why does it matter in this repository and not just in the abstract?
4. What is the smallest safe correction or verification?

### 7. Validate instead of speculating

Run only relevant, non-production checks discovered from the repository. Prefer affected tests over an unbounded full suite, but state what was not run. Typical checks include:

- Python: targeted pytest, ruff, pyright, async tests;
- TypeScript: package-scoped typecheck, lint, contract tests, targeted unit/E2E;
- Go: targeted go test, go vet, race tests when relevant, golangci-lint if configured;
- Code Rot: run scripts/analyze_code_rot.py when repository history is available, then verify hotspots with callers, tests, and local rules;
- resource checks: existing benchmarks, load tests, tracemalloc/memray, pprof, or Node heap tooling only when the change justifies them.

Never run production verification, destructive migration, real data repair, or live external side effects automatically. Treat any command with a production environment selector as human-approved only.

### 8. Produce a global review report

Use this order:

1. Verdict: BLOCK, CONCERNS, or PASS WITH NOTES.
2. Executive summary: what changed and the main system-level risk.
3. Change map: entry points, state/data flow, affected modules, callers, and tests.
4. Code quality and Code Rot baseline: hotspots, indicators, and whether this change improves or worsens them.
5. Review positions: maintainer and adversarial summaries before debate.
6. Debate outcomes: resolved, rejected, or unresolved findings with evidence.
7. Findings: ordered by severity, each with evidence and confidence.
8. Missing validation: tests, profiling, contract checks, or operational checks not performed.
9. What looks sound: important paths or safeguards that were verified.
10. Open questions and assumptions.

Do not bury a P0/P1 finding inside a long checklist. Do not report style issues already enforced by tooling unless the change bypasses or misconfigures the tooling.

The detailed output contract is in references/output-schema.md.

## Project adapters

Load references/project-profiles.md when reviewing the user's known local projects. These profiles select risk lenses and safe validation commands; they do not override repository-local rules.

## Failure handling

- Missing fixed point: ask for the target branch or commit.
- Missing spec: report functional intent as unverifiable and continue with safety/compatibility review.
- Stale or absent graph: fall back to code and tests; downgrade confidence for impact claims.
- No executable test path: report the gap; do not treat a successful lint as functional validation.
- Conflicting project instructions: prefer the most local, current repository rule and call out the conflict.
- Large diff: review the change map and high-risk paths first, then state the unreviewed surface.
- Debate overload: reduce the packet set to P0/P1 and merge duplicate findings before debating.
- Missing history: mark churn/age conclusions as unavailable rather than guessing; continue with static rot indicators and graph evidence.

## Non-goals

Do not automatically launch the full ln-620-codebase-auditor pipeline for a normal PR. Do not create Linear tasks, edit source code, or make a merge decision on behalf of the user. Use specialized audit skills only as focused follow-ups when the risk map warrants them. Do not let two agreeing model outputs substitute for evidence or human approval on high-risk changes.
