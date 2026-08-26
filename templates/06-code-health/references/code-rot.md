# Code Rot Assessment

## Definition

Code Rot is the gradual loss of understandability, changeability, testability, and operational confidence as code accumulates complexity, duplication, obsolete paths, drift, and unowned behavior.

The assessment is not a style score. It is an evidence-backed explanation of where the repository is becoming more expensive or risky to change.

## Rot indicators

### Complexity accumulation

- large or frequently edited files;
- long functions, deep nesting, high cyclomatic complexity, many parameters;
- repeated branches that encode the same business rule;
- a small change requiring edits across unrelated modules.

### Duplication and divergence

- copy-pasted validation, serialization, error handling, or adapter logic;
- two implementations of the same contract;
- compatibility paths that no longer share behavior with the main path;
- tests duplicated without a distinct business purpose.

### Dead and obsolete behavior

- symbols with no callers in the repository graph;
- stale routes, commands, feature flags, migrations, or configuration keys;
- commented-out code and old TODO/FIXME/HACK markers;
- deprecated dependencies or compatibility layers with no active consumer;
- unreachable branches and tests that no longer represent production behavior.

### Churn hotspots

- high change frequency combined with high file size or complexity;
- repeated bug fixes in the same module;
- a new change expanding an already unstable boundary;
- frequent reverts, follow-up fixes, or adjacent emergency patches.

Use git history as evidence. Do not infer ownership or quality from commit count alone.

### Test and observability decay

- critical paths changed repeatedly without meaningful behavior tests;
- tests skipped, quarantined, flaky, or asserting implementation details;
- code paths with no metrics, logs, traces, health checks, or failure visibility;
- operational workarounds that exist only in scripts or tribal knowledge.

### Architecture and documentation drift

- code no longer matches ADRs, architecture diagrams, API docs, or dependency rules;
- shared code bypassed by one-off implementations;
- domain boundaries weakened over time;
- multiple configuration sources disagree about the same runtime behavior.

## Evidence requirements

Classify each indicator:

- confirmed: direct call graph, test result, history, linter, or repository rule proves it;
- high: two independent indicators point to the same maintenance consequence;
- medium: one credible indicator suggests risk and needs targeted validation;
- unknown: insufficient history, graph, or runtime evidence.

Do not label a whole repository rotten. Identify hotspots and explain whether the current change:

1. reduces existing rot;
2. leaves it unchanged;
3. depends on it;
4. worsens it.

## Rot-aware review questions

- If this change is copied five times, what will drift?
- If the original author leaves, can another engineer find the behavior, owner, tests, and rollback path?
- Does this add a new abstraction, compatibility layer, flag, config source, or script that needs a future deletion plan?
- What is the simplest existing component that should be reused?
- Which old path becomes safe to remove after this change?
- What test or metric would tell us this area is decaying again?

## Suggested deterministic scan

Run:

    python3 scripts/analyze_code_rot.py <repo_path> --since-days 180 --output /tmp/code-rot-report.md

The scanner reports indicators and candidates only. The reviewers must verify the candidates with the repository graph, code, tests, and local documentation before turning them into findings.
