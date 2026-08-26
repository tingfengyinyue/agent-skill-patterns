# Structured adversarial debate protocol

## Objective

Use debate to test important findings, not to create a performance of disagreement. The output is a confidence-adjusted decision backed by evidence or an explicit runtime verification plan.

## Phase A: independent first pass

Both reviewers receive:

- repository map and local rules;
- fixed-point and diff;
- issue/spec or an explicit no-spec marker;
- changed symbols and enclosing functions/classes;
- callers/callees and data/resource flow;
- deterministic checks already run.

They must not receive the other reviewer's analysis. Each produces candidate findings, paths checked and found sound, unknowns, assumptions, and suggested tests or profiling.

The maintainer role emphasizes intent, architecture, contracts, cleanliness, tests, and compatibility. The adversarial role emphasizes failure modes, security, concurrency, resource lifecycle, and operational recovery.

## Phase B: normalize findings

The orchestrator merges obvious duplicates by root cause. Every candidate gets an ID and contains:

    id
    title
    location
    lens
    claim
    evidence
    causal_path
    consequence
    severity
    confidence
    requested_verification

Do not debate a pure style preference unless it implies a concrete maintainability or correctness risk.

## Phase C: create disagreement packets

Create a packet only when:

- one reviewer marks P0/P1 and the other rejects or materially downgrades it;
- the reviewers disagree about an API, data, or architecture contract;
- the reviewers disagree about whether a resource is bounded or released;
- a P2 disagreement changes the merge recommendation or needs non-trivial runtime work.

Packet format:

    Disagreement ID:
    Claim:
    Maintainer position:
    Adversarial position:
    Shared evidence:
    Missing evidence:
    Decision that depends on this:

## Phase D: two bounded debate rounds

Round 1 is challenge. Each side may only accept the opposing claim with a consequence, reject it with a concrete counterexample/test/rule, or request one specific distinguishing verification.

Round 2 is resolution. Each side must choose one:

- CONFIRMED: evidence establishes the finding;
- REJECTED: counterevidence defeats the claim;
- CONDITIONAL: plausible but depends on runtime/configuration;
- OUT OF SCOPE: real issue, but not caused by this change;
- UNKNOWN: insufficient evidence.

No round may introduce unrelated findings. New issues become new candidates.

## Phase E: adjudication rules

The judge applies these rules in order:

1. A precise reproduction, failing test, invariant violation, or direct call path outranks a general best-practice claim.
2. Repository-local rules outrank generic style preferences.
3. A finding needs a location or an explicit missing control.
4. A resource or performance claim without runtime evidence cannot be labeled confirmed unless boundedness is disproved directly from the code path.
5. Unresolved P0/P1 risk is not silently dismissed; it becomes a human-review blocker or targeted validation request.
6. Agreement is not proof. Two reviewers can share an incorrect assumption.

For each packet report:

    status: resolved | rejected | unresolved
    final_severity:
    final_confidence:
    evidence:
    decision_reason:
    next_verification:

If unresolved, do not inflate it to P0 merely because the topic is scary. Mark the uncertainty, explain the worst plausible consequence, and request the smallest safe check.

## Cost and safety limits

- Build repository context once and share the read-only bundle.
- Run the two first passes in parallel when possible.
- Debate at most eight packets and two rounds.
- Run targeted validation after debate only for questions that the check can distinguish.
- Never run production commands or destructive migrations as a debate experiment.
- Keep high-risk human approval outside the model debate.
