---
name: code-health
description: Diff-first repository code review with concrete file/line findings, call-chain tracing, protocol and resource checks, Code Rot analysis, bounded maintainer/adversarial debate, and evidence-gated learning from confirmed missed findings. Use when reviewing a branch, pull request, commit range, uncommitted worktree changes, bug fix, feature, refactor, or work-in-progress in a local project.
---

# Code Health Review

## Purpose

Review a change first as a precise Diff reviewer, then as a maintainer responsible for the whole project. Inspect every changed hunk in its enclosing function, verify the concrete behavior and call sites, and only then expand to requirements, callers, state transitions, tests, and runtime resources. Report actionable file/line findings with a causal chain; separate confirmed defects, high-confidence risks, and hypotheses that need profiling or human confirmation.

Execution priority:

1. Freeze the actual change set, including staged, unstaged, and untracked worktree changes when requested.
2. Load a small set of relevant, evidence-backed review memories without treating them as facts.
3. Perform a deterministic local correctness sweep before forming reviewer positions.
4. Trace the affected system path and assess global architecture, resources, tests, and Code Rot.
5. Use independent reviewer roles and debate only disagreements that can change the decision.

A report with only a project map, generic risks, or reviewer summaries is incomplete when the change contains executable behavior.

This skill is a review skill, not an auto-fixer. Do not modify code, create tracking tasks, approve/merge PRs, or run production actions unless the user explicitly asks.

## Research-informed principles

- Diff-only review is insufficient. Include the issue/spec, surrounding function or class, repository rules, relevant callers/callees, and test context.
- A review comment is useful only when it identifies a real risk, explains why it matters in this project, and gives a verifiable next step.
- Use program analysis and deterministic checks as evidence; use the model for synthesis, prioritization, and reasoning across artifacts.
- Do not confuse faster review with better review. A human remains responsible for high-risk decisions and unresolved uncertainty.
- Review the whole change path: intent -> entry point -> state/data flow -> side effects -> failure/retry/cancel path -> observability -> tests -> rollback or compatibility.
- Use two independent reviewer roles before debate. Independent first-pass reasoning reduces anchoring; debate is for resolving evidence-backed disagreements, not for generating more opinions.
- Treat code-writing quality and Code Rot as one maintainability axis: review both what the change does now and whether it makes the repository harder to change later.
- Treat confirmed post-review misses as learning signals, not as automatic rule changes. Store the evidence, failure category, detection rule, regression test, and negative control before promoting a lesson.

See references/research-foundations.md for the papers and design decisions derived from them.

## Required input

Identify:

1. repo_path: absolute repository path.
2. fixed_point: target branch, merge-base, commit, tag, or HEAD~N. For current uncommitted worktree review, use HEAD or an explicitly supplied base and include the worktree patch.
3. spec_source: issue, PRD, task, acceptance criteria, or a clear statement that no spec exists.

Pin and validate the reference before analysis. For a committed change, use:

    git -C <repo_path> rev-parse <fixed_point>
    git -C <repo_path> diff --stat <fixed_point>...HEAD
    git -C <repo_path> log --oneline <fixed_point>..HEAD

For a worktree review, also use:

    git -C <repo_path> status --short --branch
    git -C <repo_path> diff --stat HEAD
    git -C <repo_path> diff --cached --stat
    git -C <repo_path> ls-files --others --exclude-standard

An invalid reference is a stop condition. An empty committed diff is not a stop condition when staged, unstaged, or untracked changes exist. Label the review as `HEAD + working tree` and preserve existing changes; do not use destructive Git commands.

### 1. Freeze the change set and perform the local correctness sweep

Before building reviewer positions, create a change inventory. For every changed file and untracked file:

- inspect every changed hunk with enough surrounding context to identify the enclosing function/class;
- record the exact file and line location, changed symbol, behavior changed, and nearest callers/callees;
- compare function signatures with every call site, especially positional arguments, defaults, keyword names, and enum/string values;
- check early `return`/`break`, loop aggregation, chunk/stream handling, exception paths, state transitions, IDs/correlation fields, bytes-versus-text semantics, and serialization boundaries;
- compare the new behavior with the nearest existing tests and identify the smallest missing regression test.

Use `references/diff-first.md`. This pass must produce concrete candidate findings before the global review. Prefer a false-positive-free short list over a long smell list.

For logging, tracing, event, streaming, or metrics changes, also read `references/observability-review.md` and verify event schema, lifecycle correlation, aggregation semantics, log volume, and sampling.

Before finalizing the sweep, use `references/review-learning-loop.md` and load at most three relevant memories:

    python3 scripts/review_memory.py select --repo <repo-name> --service <service> --tag <change-area>

Use them to add targeted checks. Record in the report which memories were applied, contradicted, confirmed, or unused.

## Review workflow

### 2. Build the repository map around the changed path

After the local sweep, read the smallest set of high-value context:

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

Use scripts/collect_review_context.py to create a deterministic first-pass context bundle when useful. Pass `--working-tree` when the review includes staged, unstaged, or untracked changes.

### 3. Reconstruct intent and system flow

Before judging implementation, write a short internal flow map:

    user/event -> entry point -> service/agent -> state/data store -> external side effect
              -> success path / failure path / retry path / cancel path
              -> observable signal -> test or operational verification

For each changed file, classify its role: API, domain logic, orchestration, persistence, transport, shared library, UI, worker, configuration, test, migration, or deployment. Identify the nearest upstream callers and downstream consumers.

If the change has no usable spec, review functionality as “intent not verifiable” rather than inventing requirements. Still review safety, compatibility, and regressions.

### 4. Determine blast radius and risk

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

### 5. Run two independent review passes

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

### 6. Debate only high-value disagreements

Use references/debate-protocol.md. Do not debate every stylistic difference. Debate any P0 or P1 finding rejected by the other reviewer, disagreements about contracts/architecture/resource lifecycle/security, and P2 disagreements that change the merge decision or require expensive runtime validation.

The debate has a fixed budget: at most two rounds and at most eight disagreement packets per review. Do not use majority vote. If evidence remains insufficient, downgrade the finding to needs-runtime-verification and design the smallest distinguishing check.

### 7. Review the change through the project-health lenses

Read references/review-lenses.md, references/code-rot.md, and the observability reference when relevant. Apply only the relevant lenses, but always cover functionality, code-writing quality, Code Rot, architecture, tests, and reliability. Add resource/performance/security/operations lenses when the risk map triggers them.

For every finding, answer:

1. What exact behavior or design is problematic?
2. Where is the evidence: file, line, call path, test, config, or runtime result?
3. Why does it matter in this repository and not just in the abstract?
4. What is the smallest safe correction or verification?

### 8. Validate instead of speculating

Run only relevant, non-production checks discovered from the repository. Prefer affected tests over an unbounded full suite, but state what was not run. Typical checks include:

- Python: targeted pytest, ruff, pyright, async tests;
- TypeScript: package-scoped typecheck, lint, contract tests, targeted unit/E2E;
- Go: targeted go test, go vet, race tests when relevant, golangci-lint if configured;
- Code Rot: run scripts/analyze_code_rot.py when repository history is available, then verify hotspots with callers, tests, and local rules;
- resource checks: existing benchmarks, load tests, tracemalloc/memray, pprof, or Node heap tooling only when the change justifies them.

For every P1/P2 candidate, run or propose the smallest discriminating check: a targeted test, call-site inspection, schema assertion, fixture, sample replay, benchmark, heap measurement, or log-query validation. Do not replace a failed relevant test with a successful compile or lint.

Never run production verification, destructive migration, real data repair, or live external side effects automatically. Treat any command with a production environment selector as human-approved only.

### 9. Produce a global review report

Use this order:

1. Verdict: BLOCK, CONCERNS, or PASS WITH NOTES.
2. Executive summary: what changed and the main system-level risk.
3. Change-set inventory and call-chain map.
4. Findings: concrete file/line issues ordered by severity, with evidence, causal chain, project consequence, and smallest fix or verification.
5. Code quality and Code Rot baseline: hotspots, indicators, and whether this change improves or worsens them.
6. Review positions: maintainer and adversarial summaries before debate.
7. Debate outcomes: resolved, rejected, or unresolved findings with evidence.
8. Missing validation: tests, profiling, contract checks, or operational checks not performed.
9. Verified strengths: important paths or safeguards that were checked.
10. Spec alignment and open questions.

Do not bury a P0/P1 finding inside a long checklist. Do not report style issues already enforced by tooling unless the change bypasses or misconfigures the tooling.

The detailed output contract is in references/output-schema.md.

### 10. Learn only from confirmed post-review feedback

If the user or later evidence confirms that a previous review missed a real issue, perform a short reflection before changing any rule. Classify the miss as context, reasoning, detector, validation, tool, or scope failure. Create a `candidate` memory with evidence, detection rule, required regression test, and negative control:

    python3 scripts/review_memory.py record --input /path/to/missed-review.json

Do not record uncertain reviewer opinions as lessons. Promote only with explicit human approval:

    python3 scripts/review_memory.py promote <id> --to validated --approved-by <human>

Promote to `global-rule` only after independent confirmation in at least two contexts. Use `supersede` or `invalidated` when later evidence corrects a lesson. Never silently edit the core Skill or publish private project evidence.

## Project adapters

Load references/project-profiles.md when reviewing the user's known local projects. These profiles select risk lenses and safe validation commands; they do not override repository-local rules.

## Failure handling

- Missing fixed point: use HEAD for an explicitly requested worktree review; otherwise ask for the target branch or commit.
- Missing spec: report functional intent as unverifiable and continue with safety/compatibility review.
- Stale or absent graph: fall back to code and tests; downgrade confidence for impact claims.
- No executable test path: report the gap; do not treat a successful lint as functional validation.
- Conflicting project instructions: prefer the most local, current repository rule and call out the conflict.
- Large diff: review the change map and high-risk paths first, then state the unreviewed surface.
- Debate overload: reduce the packet set to P0/P1 and merge duplicate findings before debating.
- Empty committed diff with worktree changes: review the staged/unstaged/untracked change set and label the base/head accordingly.
- Missing history: mark churn/age conclusions as unavailable rather than guessing; continue with static rot indicators and graph evidence.
- Missing or unreadable review memory: continue the review, record that no memory was applied, and do not invent prior lessons.

## Non-goals

Do not automatically launch the full ln-620-codebase-auditor pipeline for a normal PR. Do not create Linear tasks, edit source code, or make a merge decision on behalf of the user. Use specialized audit skills only as focused follow-ups when the risk map warrants them. Do not let two agreeing model outputs substitute for evidence or human approval on high-risk changes.
