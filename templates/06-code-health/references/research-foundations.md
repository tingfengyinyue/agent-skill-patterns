# Research foundations

This first version uses research as design input, not as a claim that an LLM can replace an experienced reviewer.

## Findings adopted

### 1. Preserve the review unit, not only changed lines

CodeReviewer formalizes code review around code changes and review comments, and reports that diff-aware representations matter for review tasks. It also separates quality estimation, comment generation, and refinement into different tasks. The Skill therefore starts from a pinned diff but retrieves the enclosing function/class and surrounding flow before judging a line.

Source: https://arxiv.org/abs/2203.09095

### 2. Enrich the diff with semantic and structural context

ContextCRBench reports that issue/PR text and contextual code improve review evaluation more than code context alone, while current models remain below human-level review ability. The Skill therefore requires the spec/issue when available and uses repository rules, callers/callees, tests, and state flow as first-class evidence.

Source: https://arxiv.org/abs/2511.07017

### 3. Use function call graphs and summaries as review context

Research on prompting for code review found gains from augmenting a patch with function call graphs and code summaries. The Skill therefore prefers codebase-memory-mcp impact analysis and asks for callers/callees of important changed symbols instead of relying on the patch alone.

Source: https://arxiv.org/abs/2411.10129

### 4. Evaluate comprehension as separate reasoning steps

CodeReviewQA decomposes review comprehension into change-type recognition, change localisation, and solution identification. The Skill mirrors this as: classify the change and risk, localize the affected flow and evidence, then propose the smallest safe correction or verification.

Source: https://arxiv.org/abs/2503.16167

### 5. Prefer repository-level, multi-dimensional evaluation

CodeFuse-CR-Bench argues that isolated, context-poor benchmarks create a reality gap and evaluates repository-level review with multiple PR problem domains. The Skill therefore reviews functionality, architecture, resource behavior, reliability, security, operations, and tests as separate lenses and reports missing evidence.

Source: https://arxiv.org/abs/2509.14856

### 6. Do not equate faster review with better review

A large-scale study of human, LLM-assisted, and agentic review found faster decisions with agent involvement but no corresponding quality improvement. The Skill therefore keeps human approval for high-risk changes, avoids automatic merge decisions, and reports confidence and unknowns rather than manufacturing certainty.

Source: https://arxiv.org/abs/2607.13196

### 7. Combine LLM review with static analysis

The Ericsson experience report describes a lightweight approach combining LLMs with static program analysis. The Skill follows the same boundary: deterministic tools establish facts; the model connects facts across requirements, architecture, and runtime behavior.

Source: https://arxiv.org/abs/2507.19115

### 8. Separate independent judgment from interaction

The evidence about agentic review supports using agents to reduce review effort, but not treating multi-agent agreement as a quality guarantee. The Skill therefore separates first-pass judgments before interaction, limits debate to material disagreements, and makes the final decision depend on evidence and targeted verification.

This is a design inference from the empirical findings above, not a claim that debate itself guarantees correctness.

## Design consequence

The review unit is not a file or a line. It is:

    requirement -> changed symbol -> enclosing flow -> callers/consumers
                 -> state/resource side effects -> failure/retry/cancel paths
                 -> tests/observability/rollback evidence

Any review that cannot traverse this chain must label its conclusion as partial.
