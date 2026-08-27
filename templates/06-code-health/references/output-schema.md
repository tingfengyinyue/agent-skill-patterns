# Review output contract

Use Markdown for the human report. Keep the following structure stable so it can later be rendered into PR comments or machine-readable summaries.

    # Code Health Review

    Verdict: BLOCK | CONCERNS | PASS WITH NOTES
    Base: <fixed point>
    Head: <head sha>
    Scope: <files/modules reviewed>

    ## Executive summary
    <What changed, what system flow it affects, and the largest risk.>

    ## Change map
    - Intent/spec:
    - Entry points:
    - Main callers and consumers:
    - State/data stores:
    - External side effects:
    - Failure/retry/cancel paths:
    - Tests and checks run:

    ## Code quality and Code Rot baseline
    - Hotspots:
    - Complexity/duplication indicators:
    - Dead/obsolete path indicators:
    - Test/observability decay:
    - Architecture/documentation drift:
    - This change: improves | unchanged | depends on | worsens the baseline

    ## Standards and repository rules
    - Rules found:
    - Relevant conventions:
    - Conflicts or missing standards:

    ## Findings

    ### [P1][high confidence] Short title
    - Location: path/file.ext:line
    - Lens: functionality | cleanliness | architecture | memory | performance | reliability | security | operations | tests
    - Evidence: <specific code path, graph result, test output, or config>
    - Risk: <project-specific consequence>
    - Recommendation: <smallest safe fix or verification>

    ## Independent review positions
    ### Maintainer
    - Summary:
    - Strong paths:
    - Candidate findings:

    ### Adversarial
    - Summary:
    - Strong paths:
    - Candidate findings:

    ## Debate outcomes
    - Packet:
    - Maintainer position:
    - Adversarial position:
    - Status: resolved | rejected | unresolved
    - Decision reason:
    - Next verification:

    ## Missing validation
    - <check not run and why>

    ## Verified strengths
    - <important safeguard or path checked>

    ## Spec alignment
    - Covered:
    - Not verifiable:
    - Out of scope side effects:

    ## Open questions
    - <assumption or runtime fact that needs confirmation>

## Finding quality gate

When the change contains executable behavior, the report must include concrete findings or explicitly state that the focused sweep found none. Every finding needs an exact file/line (or an explicit missing control), code/test/config evidence, a causal chain to the project-specific consequence, severity, confidence, and the smallest fix or distinguishing verification. Do not replace this with only an architecture summary, smell list, or reviewer agreement.

## Finding rules

- A finding must point to a location or an explicit missing control.
- Separate duplicate symptoms that share one root cause.
- Do not elevate a style preference above a functional, security, reliability, or resource risk.
- Do not state a memory leak or performance regression as confirmed without a proof, benchmark, or reproducible path.
- If the issue is real but outside the requested scope, report it as a side-effect finding and say whether it blocks the current change.
- Do not report the number of agreeing Agents as evidence.
- Preserve unresolved disagreements and downgrade confidence when the evidence is incomplete.
