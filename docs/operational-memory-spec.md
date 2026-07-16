# Operational Memory Specification

Operational Memory (OM) is the structured output of SPAR's Reflect phase: lessons learned from execution, stored for future recall.

**Not** a runbook (pre-existing procedural knowledge), incident report (event facts), or audit log (operation records).

**One sentence:** Execution optimization notes left for your future self.

---

## Storage

```
knowledge-base/memory/operational/
├── index.md                              # Master index with JSON recall block
└── om-YYYY-MM-DD-NNN-<slug>.md           # Individual memory entries
```

---

## Data Schema

Each Operational Memory entry uses this frontmatter structure:

```yaml
---
id: om-YYYY-MM-DD-NNN
created_at: 2026-07-15T16:30:00+08:00
updated_at: 2026-07-15T16:30:00+08:00
title: "One-line summary of the lesson"
trigger:
  task_type: [incident]              # incident | batch | query | config | audit
  services: [payment-service]        # Which services this applies to
  symptoms: [timeout, 500]           # Keywords that should trigger recall
  tags: [database, row-lock]         # Free-form tags
context_before: |
  What happened before (the detour or mistake)
better_action: |
  What to do next time (the improved strategy)
evidence:
  incidents: [2026-07-15-payment-timeout]
  what_went_wrong: "Description of the detour"
confidence: low                      # low → medium → high
hits: 0                              # Times recalled and effective
last_verified_at: 2026-07-15
status: active                       # active | deprecated | superseded
supersedes: []                       # IDs of memories this one replaces
---
```

---

## Field Semantics

### confidence

Tracks how reliable this memory is:

| Level | Meaning | Promotion criteria |
|-------|---------|-------------------|
| `low` | New, unverified lesson | Default for newly created memories |
| `medium` | Verified once, worked as expected | hits ≥ 2 and no failures |
| `high` | Battle-tested, consistently effective | hits ≥ 5 over 1+ month |

### hits

Counter incremented when:
1. The memory is recalled during a Plan phase
2. The `better_action` is applied
3. The outcome was positive (confirmed in Reflect)

If recalled but unhelpful → do NOT increment; note in reflect instead.

### status

| Status | Meaning | Trigger |
|--------|---------|---------|
| `active` | Available for recall | Default |
| `deprecated` | No longer reliable | Applied 2x consecutively with worse outcome |
| `superseded` | Replaced by a better memory | New memory created with `supersedes: [this-id]` |

---

## The Index File

The index serves two purposes:
1. **JSON block** — for fast programmatic filtering (cheap, ~50 tokens)
2. **Markdown tables** — for human review and maintenance

### JSON Quick Recall Block

```json
[
  {
    "id": "om-2026-07-15-001",
    "task_type": ["incident"],
    "services": ["payment-service"],
    "symptoms": ["timeout", "500", "slow"],
    "tags": ["database", "row-lock"],
    "confidence": "medium",
    "hits": 3,
    "status": "active"
  }
]
```

### Multi-Dimensional Indexes (Markdown)

The index file also maintains indexes by:
- **task_type** — all incident memories, all query memories, etc.
- **service** — all memories touching payment-service
- **tag** — all memories tagged with "database"

These serve human reviewers; agents use the JSON block.

---

## Recall Flow (Plan Phase)

Every task's Plan phase starts with memory recall:

```
1. Read index.md JSON block (cheap: ~50 tokens)
2. Filter by task_type AND service
3. Optionally filter by symptoms/tags for precision
4. For matched candidates: read full entry's better_action field
5. Decide: apply, skip, or partially adapt
6. Record which memories were applied
```

**Recall priority:**
- Exact service + exact symptom match → read immediately
- Same service, different symptom → scan if few results
- Different service, same symptom → consider if no direct matches

---

## Creation Flow (Reflect Phase)

### The Four Questions

After task completion, ask:

1. **Did I take a detour?** → Write `context_before` (the wrong path)
2. **Was I faster than last time?** → If NO, write what slowed you down
3. **Any unexpected pitfall?** → Write `what_went_wrong`
4. **Can I distill "next time, do X"?** → Write `better_action`

**If ANY answer is yes → create a memory.**

### Writing better_action

The `better_action` field is the most important. Guidelines:

- Write as an **imperative instruction** ("Check X first" not "I should have checked X")
- Include the **verification order** (what to check first, second, third)
- Mention the **why** (so future recall can assess applicability)
- Keep it **actionable within 1-2 steps** (not a full runbook)

**Good:**
```yaml
better_action: |
  Payment timeout at 14:xx → first check if batch-import cron is running
  (it starts at 14:30 and takes table-level locks on orders).
  If cron is active: wait for completion or kill the job.
  If cron is not running: proceed with standard timeout diagnosis.
```

**Bad:**
```yaml
better_action: |
  There might be a batch job running. Check various things.
```

---

## Lifecycle Management

### Maintenance Rules

| Event | Action |
|-------|--------|
| Memory recalled + effective | `hits += 1`, update `last_verified_at` |
| Memory recalled + ineffective | Do NOT increment; note in reflect |
| Memory ineffective 2x consecutively | `status: deprecated` |
| New memory covers same ground better | `supersedes: [old-id]`, old → `superseded` |
| Memory not recalled for 6 months | Flag as `stale` in index |
| `confidence: high` + `hits ≥ 10` + 3mo stable | Graduate to runbook |

### Graduation to Runbook

When a memory reaches high confidence with sustained hits, it has proven itself as reliable procedural knowledge. At this point, extract it into a proper runbook and mark the memory as superseded.

---

## Meta-Patterns

After accumulating multiple memories, look for recurring strategies that span individual entries. Document these as **meta-patterns** at the top of the index.

**Observed meta-patterns:**

> **Do the cheapest deterministic verification first; push expensive global searches to the end.**

Example application across memories:
- om-001: trace_id (cheap) → row lock check (cheap) → broad log search (expensive)
- om-002: single SQL match (cheap) → login records (medium) → gateway trace (expensive)

> **An API returning empty ≠ data doesn't exist. Try a different query dimension.**

Example:
- om-003: SearchDatabase returns empty → ListInstances + ListDatabases finds it
- om-004: Service-specific logstore empty → actually uses a shared logstore

---

## Example Entry

```markdown
---
id: om-2026-07-15-001
created_at: 2026-07-15T14:45:00+08:00
title: "Payment timeout at 14:xx → check batch job schedule conflict first"
trigger:
  task_type: [incident]
  services: [payment-service]
  symptoms: [timeout, slow, order creation]
  tags: [database, cron, batch, schedule]
context_before: |
  Spent 5 minutes searching logs broadly for timeout causes.
  Eventually found it was a batch import job holding table locks.
  Could have identified this in 30 seconds by checking cron status.
better_action: |
  Payment timeout between 14:00-15:00 → first check if batch-import
  cron is running (starts 14:30, locks orders table for ~5 min).
  Quick check: query cron execution log for today's 14:30 run.
  If active: this is the cause. Wait or kill job.
  If not active: proceed with standard timeout diagnosis.
evidence:
  incidents: [2026-07-15-payment-timeout-uid12345]
  what_went_wrong: "Went straight to broad log search instead of checking known schedule conflicts"
confidence: low
hits: 0
last_verified_at: 2026-07-15
status: active
supersedes: []
---

# om-2026-07-15-001: Payment timeout → check batch schedule first

## Lesson

Payment service timeouts between 14:00-15:00 have a high probability of being
caused by the daily batch-import cron job (starts 14:30, holds table-level locks
on the orders table for approximately 5 minutes).

## Decision Tree

1. Is it between 14:00-15:00? → Check cron status first
2. Cron running + holding locks? → THIS is the cause. Wait or kill.
3. Cron not running? → Standard timeout diagnosis (row locks, connection pool, etc.)

## Why This Matters

The batch job is the cheapest thing to check (one query to cron log) and explains
~40% of payment timeouts in this time window. Checking it first saves 5+ minutes
of broad log analysis.
```
