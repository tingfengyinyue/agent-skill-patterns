# Token Efficiency Strategies

How to architect an agent knowledge system that respects context window limits.

---

## The Problem

Every token consumed by knowledge loading is a token unavailable for actual reasoning, tool calls, and output generation. A knowledge base that dumps 5000 tokens of context before the agent starts working is wasteful.

**Goal:** Maximum relevant context with minimum token cost.

---

## Strategy 1: JSON Index at Markdown Top — The "Table of Contents" Trick

Place a machine-readable JSON block at the top of human-readable Markdown files. The agent reads the compact JSON (50 tokens) for filtering, then reads full entries only for matches. Think of it as a table of contents: the agent decides which chapters to open without reading the whole book.

### Pattern

```markdown
# Memory Index

## Quick Recall (JSON)

\```json
[
  {"id":"om-001","services":["payment"],"symptoms":["timeout"],"confidence":"high","hits":5},
  {"id":"om-002","services":["auth"],"symptoms":["403"],"confidence":"medium","hits":2}
]
\```

## Full Entries

### om-001: Payment timeout row lock shortcut
(200 tokens of detailed content)
...

### om-002: Auth 403 token expiry check
(200 tokens of detailed content)
...
```

**Cost analysis:**
- Without JSON index: read all entries = 400+ tokens
- With JSON index: read JSON (50 tokens) + 1 relevant entry (200 tokens) = 250 tokens
- Savings grow linearly with number of entries

### When to use

- Index files with 5+ entries
- Any file where the agent needs to filter before reading detail
- Memory indexes, service catalogs, incident lists

---

## Strategy 2: Layered Read Depth — Read Shallow First, Go Deep Only If Stuck

Structure knowledge in layers of increasing detail. Read the cheapest layer first; only drill deeper when needed.

### The Four Layers

```
Layer 0: Hot cache       (~100 tokens)  ← Always read
Layer 1: Index/catalog   (~200 tokens)  ← Read if hot cache misses
Layer 2: Topic page      (~300 tokens)  ← Read only the relevant one
Layer 3: Raw/full detail (~500+ tokens) ← Read only for deep investigation
```

### Implementation

```markdown
## Hot Cache (Layer 0)
Recent context summary. Updated after every session.
Contains: last 3 incidents, active alerts, today's key metrics.

## Index (Layer 1)
Master catalog of all knowledge pages.
Contains: page titles, types, dates — enough to locate what you need.

## Topic Pages (Layer 2)
Individual service docs, runbooks, memory entries.
Contains: full procedural knowledge for one specific topic.

## Raw Sources (Layer 3)
Original source material, full log dumps, complete reports.
Contains: everything — only read when you need exact details.
```

### Read protocol

```
Agent receives task
  → Read hot cache (always, ~100 tokens)
  → Sufficient? → Execute
  → Insufficient? → Read index (additional ~200 tokens)
  → Found relevant page? → Read that ONE page (~300 tokens)
  → Still need more? → Read raw source (~500+ tokens)
```

**Typical cost:** 100-400 tokens for context loading.
**Worst case:** 1000+ tokens (only for novel, complex problems).

---

## Strategy 3: Priority-Based Query Ordering — Cheapest First, Broadest Last

When searching for information, try the cheapest queries first. Only escalate to expensive queries when cheap ones fail.

### Query Cost Hierarchy

| Priority | Query Type | Token Cost | Determinism |
|----------|-----------|------------|-------------|
| 1 | Exact ID lookup (trace_id) | Low | High |
| 2 | Scoped filter (service + time) | Low-Medium | High |
| 3 | Category filter (error level) | Medium | Medium |
| 4 | Full-text search (keywords) | High | Low |
| 5 | Broad scan (all recent logs) | Very High | Very Low |

### Implementation in skills

```markdown
## Query Strategy

1. Has trace_id? → Use it directly (one precise query)
2. Has specific endpoint + time? → Scoped query
3. Has service + error level? → Filtered query
4. Only keywords? → Full-text (last resort, warn about noise)
```

**Why this saves tokens:** A trace_id query returns 3-5 relevant lines. A broad keyword search returns 100+ lines that the agent must then filter — consuming tokens for irrelevant content.

---

## Strategy 4: Structured Over Prose — Tables Beat Paragraphs

Tables and structured formats are more token-efficient than prose for reference material.

### Comparison

**Prose (87 tokens):**
```
The payment service uses the payment-logs logstore in production,
and the payment-dev logstore in testing. The auth service uses
auth-logs in production and auth-dev in testing. The gateway uses
gateway-logs in production and gateway-dev in testing.
```

**Table (45 tokens):**
```markdown
| Service | Production | Testing |
|---------|-----------|---------|
| payment | payment-logs | payment-dev |
| auth | auth-logs | auth-dev |
| gateway | gateway-logs | gateway-dev |
```

**Same information, 48% fewer tokens.** And the agent can parse tables more accurately.

### Where to use tables

- Configuration mappings (service → resource)
- Error handling (error → resolution)
- Decision matrices (condition → action)
- Parameter references (flag → description)

---

## Strategy 5: Incremental State Over Full Reload — Only Process What Changed

Track what has been processed. Only load/process the differences (deltas) since last run.

### Anti-pattern: Full reload every time

```
Every scan: clone 8 repos → scan all files → rewrite all docs
Cost: 10 minutes, 50,000+ tokens of code reading
```

### Pattern: Incremental with state file

```json
{
  "payment-service": {"last_commit_sha": "abc123"},
  "auth-service": {"last_commit_sha": "def456"}
}
```

```
Every scan:
  For each service:
    new_commits = git log last_commit_sha..HEAD
    if none → skip (0 tokens)
    if some → git diff last_commit_sha..HEAD -- relevant_paths/
    Update only affected doc sections
Cost: 30 seconds, 2,000 tokens of focused diff reading
```

**Savings:** 96% reduction in typical runs.

---

## Strategy 6: Progressive Disclosure — Reveal Details Only When Needed

> "Progressive disclosure" means: don't show everything upfront. Reveal information layer by layer, only when the agent actually needs it. Like a book that only shows the chapter you opened — not all chapters at once.

Skills themselves should be token-efficient. Not everything needs to be in the main SKILL.md.

### Three-Level Loading

```
Level 1: Metadata (always in context)        ~20 tokens
  name + description in frontmatter

Level 2: SKILL.md body (loaded on trigger)   ~200-400 tokens
  Core instructions, steps, templates

Level 3: Reference files (loaded on demand)  ~300+ tokens each
  Detailed docs, examples, schemas
  Only read when the skill explicitly says to
```

### SKILL.md size guideline

| Content Type | Recommendation |
|-------------|----------------|
| Core instructions | In SKILL.md (≤500 lines) |
| Configuration tables | In SKILL.md |
| Detailed schemas | In `references/schema.md` |
| Extended examples | In `references/examples.md` |
| Utility scripts | In `scripts/` (execute, don't read) |

---

## Measuring Token Efficiency

### Metrics to track

1. **Context load ratio:** tokens spent on knowledge / tokens spent on task execution
   - Target: < 30% on knowledge, > 70% on execution
   
2. **Hit rate:** how often loaded knowledge is actually used in the response
   - Target: > 80% of loaded content referenced in output

3. **Escalation frequency:** how often cheap queries fail and expensive ones are needed
   - Target: < 20% escalation rate (means your indexes and caches are effective)

### Signs of poor token efficiency

- Agent reads the same file multiple times per session
- Agent loads 1000+ tokens of context then only references 50 tokens of it
- Full scans run when incremental would suffice
- Index files are prose-only (no JSON quick-recall block)
