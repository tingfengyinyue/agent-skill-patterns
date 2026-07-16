# Design Philosophy

Seven principles for building production-grade AI agent skills.

These aren't theoretical — they emerged from running an AI-assisted operations platform handling real incidents, daily reports, and service monitoring across 8+ microservices.

---

## Principle 1: Skills Are Agent Manuals, Not Human Docs

A skill is not documentation for humans to read. It's an **executable instruction set** for an AI agent.

**What this means in practice:**

- Every skill has explicit **trigger conditions** (what phrases activate it)
- Every skill has **typed parameters** (what inputs it accepts)
- Steps are **numbered and unambiguous** (no "you might want to consider...")
- Output formats are **templated** (the agent knows exactly what to produce)

**Anti-pattern:**
```markdown
## Overview
This tool helps with log analysis. You can use it to query logs
from various services. Consider the time range and service name
when constructing your query.
```

**Correct pattern:**
```markdown
## Trigger
When user says `/log-query`, `查日志`, `查询错误`

## Parameters
- --service: service name (required)
- --last: time range (default: 1h)
- --error: filter error level only (flag)

## Execution
1. Parse query intent → extract service, time range, keywords
2. Map service → log source configuration
3. Build query → execute → parse results
4. Format output → suggest next steps
```

---

## Principle 2: Parallelism First

If steps are independent, **explicitly mark them as parallelizable**. LLM agents can dispatch concurrent operations, but only if the skill makes independence clear.

**Pattern:**
```markdown
### Step 1: Execute queries (parallel)

Today group (queries 1-6) and yesterday group (queries 7-12)
can run fully in parallel. Same-source queries within a group
can also parallelize.
```

**Why this matters:**
- A 12-query report that runs serially takes 60s
- The same report with parallelism takes 10s
- The skill must explicitly state which steps are independent

---

## Principle 3: Errors Are First-Class Citizens

Every skill ends with an **error handling table**. This isn't optional decoration — it's what prevents the agent from hallucinating recovery paths.

**Pattern:**
```markdown
## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Query timeout (>9s) | Large table scan | Retry once; if persists, narrow time range |
| Access denied | Credentials expired | Check ~/.config/credentials.json |
| No results | Wrong time range or service | Suggest broadening; list available services |
| NULL values | No records for today yet | Fill with 0, note "partial data" |
```

**Why a table, not prose:**
- Agents can pattern-match error messages against the table
- Each row is a self-contained decision rule
- No ambiguity about what to do

---

## Principle 4: State-Aware — Incremental Over Full

Never re-process everything when you can process only what changed.

**Pattern: State file**
```json
{
  "services": {
    "auth-service": {
      "last_commit": "abc123",
      "last_scan": "2026-07-01"
    },
    "payment-service": {
      "last_commit": "def456",
      "last_scan": "2026-07-10"
    }
  }
}
```

**Execution logic:**
```
1. Read state file
2. For each service: check if new commits exist since last_commit
3. No new commits → skip
4. New commits → diff only changed paths → update only affected sections
5. Write updated state
```

**Benefits:**
- 8-service scan drops from 10 min to 30s on a typical day
- Only touches documentation that actually needs updating
- State file is the single source of truth for "what's current"

---

## Principle 5: Temporal Knowledge Management

All knowledge has a timestamp. All knowledge has a lifecycle.

**Incident records:** `2026-07-15-payment-timeout.md`
**Operational memories:** `om-2026-07-15-001-<slug>.md`
**Service scans:** `last_scan: 2026-07-15`

**Why temporal ordering matters:**
- Recent incidents are more relevant than old ones
- Operational memories have confidence that evolves over time
- Stale knowledge (6 months un-recalled) should be flagged for review

**Lifecycle states:**
```
active → deprecated → superseded → archived
         (failed 2x)   (replaced)    (6mo stale)
```

---

## Principle 6: Token-Efficient Architecture

Every token loaded into the context window is a token the agent can't use for reasoning and output. Think of context window as a desk — the more reference books open on it, the less room for actual work. The knowledge architecture must minimize reads while maximizing relevance.

**Three strategies:**

### Strategy 1: JSON Index Block

Place a machine-readable JSON index at the top of human-readable Markdown:

```markdown
# Operational Memory Index

## Quick Recall Index (JSON)

\```json
[
  {"id":"om-001","task_type":["incident"],"services":["payment"],"symptoms":["timeout"],"confidence":"high","hits":5},
  {"id":"om-002","task_type":["query"],"services":["auth"],"symptoms":["not found"],"confidence":"medium","hits":2}
]
\```

## Full Entries (only read when needed)
...
```

The agent reads the JSON block (50 tokens), filters candidates, then reads only the 1-2 relevant full entries (200 tokens each) instead of scanning all entries (2000+ tokens).

### Strategy 2: Layered Reads

```
Layer 0: Hot cache (recent context, ~500 words)     ← read always
Layer 1: Index (master catalog, structured)          ← read if hot miss
Layer 2: Domain pages (detailed knowledge)           ← read only relevant ones
Layer 3: Raw sources (full documents)                ← read only on deep dive
```

### Strategy 3: Priority-Based Query

```
Priority 1: trace_id (cheapest, most deterministic)
Priority 2: specific path + time window
Priority 3: error level + service name
Priority 4: user ID / full text search (most expensive, noisiest)
```

Always try cheap deterministic queries first. Only escalate to expensive broad queries when cheap ones fail.

---

## Principle 7: Layered Processing — The SPAR Framework

> SPAR = **S**ense, **P**lan, **A**ct, **R**eflect. A cognitive loop that makes agents learn from experience, not just execute blindly.

Every operational task follows a four-phase cognitive loop:

| Phase | Name | Purpose |
|-------|------|---------|
| **S** | Sense | Extract key signals from the request |
| **P** | Plan | Recall past experience, choose strategy |
| **A** | Act | Execute the chosen strategy |
| **R** | Reflect | Did it work? What to remember for next time? |

**The critical innovation is Phase R (Reflect):**

Most agent systems are S→A (sense and act) — like a worker with amnesia who forgets everything between shifts. Adding Plan (recall past lessons) and Reflect (create new lessons) creates a **compounding feedback loop** — the agent gets better with every task, like a worker who keeps a notebook of lessons learned.

→ See [SPAR Framework](spar-framework.md) for the full specification.
→ See [Operational Memory Spec](operational-memory-spec.md) for how reflections are stored and recalled.

---

## Summary: The Compound Effect

These seven principles reinforce each other:

```
Principle 4 (State-aware) + Principle 6 (Token-efficient)
  → Only read what changed, in the cheapest way possible

Principle 7 (SPAR) + Principle 5 (Temporal)
  → Lessons compound over time with lifecycle management

Principle 1 (Agent manual) + Principle 3 (Errors first-class)
  → Agent never gets stuck; always knows what to do next

Principle 2 (Parallel) + Principle 4 (Incremental)
  → Operations that once took minutes now take seconds
```

The result: an agent that is **fast** (parallel + incremental), **reliable** (error handling + state tracking), and **gets smarter over time** (SPAR + operational memory).
