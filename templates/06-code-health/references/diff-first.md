# Diff-First Review Protocol

Use this protocol before global architecture or agent debate. Its purpose is to find concrete regressions in the change itself, not to produce a broad checklist.

## Change-set modes

Committed branch or PR:

    git diff --no-ext-diff --unified=80 <base>...HEAD

Current worktree:

    git diff --no-ext-diff --unified=80 HEAD
    git diff --cached --no-ext-diff --unified=80
    git ls-files --others --exclude-standard

For an untracked file, inspect the file and record it as part of `HEAD + working tree`. Never silently review only the committed range when the user asked for the current workspace.

## Local correctness sweep

For each changed hunk, inspect its enclosing function/class and perform these focused checks:

1. Contract mapping: compare definitions and all callers. Check positional argument order, keyword names, default values, return shape, enum/string values, and optional fields.
2. Control flow: look for early returns inside aggregation loops, skipped cleanup, swallowed exceptions, retry multiplication, and branches that never emit the expected event or result.
3. State and identity: trace request/task/run/event IDs from entry to persistence, queue, consumer, response, and acknowledgement. Check that one canonical ID is used.
4. Data semantics: verify bytes versus text, raw versus normalized content, hash inputs, truncation, encoding replacement, and serialization boundaries.
5. Streaming and aggregation: check whether metadata describes one chunk or the whole call, whether counters reset correctly, and whether duplicate detection matches the observed failure shape.
6. Resource cost: identify full-body copies, repeated serialization/hash work, unbounded buffers, per-event logs, and missing sampling or size limits.
7. Regression proof: map each risky behavior to an existing test. If absent, name the smallest test that would fail before the fix and pass after it.

## Finding quality gate

Report a finding only when it has all of the following:

- exact file and line (or an explicit missing control);
- concrete evidence from code, a call site, test output, configuration, or reproducible behavior;
- a complete causal chain from the changed line to the project-specific consequence;
- severity and confidence;
- the smallest safe fix or distinguishing verification.

Merge findings that share one root cause. Distinguish defects introduced by the change from pre-existing debt that the change expands or relies on. If evidence is incomplete, preserve the hypothesis as `needs-runtime-verification` instead of upgrading it for narrative impact.
