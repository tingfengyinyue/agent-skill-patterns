# SPAR Framework

A four-phase cognitive loop for AI agent operational tasks.

SPAR stands for **Sense → Plan → Act → Reflect**. It transforms agents from stateless executors (agents that forget everything between tasks) into learning systems that compound operational wisdom over time.

---

## Why SPAR?

Most AI agent workflows are two-phase: understand the request, then execute it. This works for simple tasks but fails for operations work where:

- The same type of problem recurs with variations
- Past experience contains critical shortcuts
- Mistakes are expensive and should never repeat
- Knowledge must compound across sessions

SPAR adds two phases that create a feedback loop:
- **Plan** = recall what worked before (prevents repeating mistakes)
- **Reflect** = capture what you learned (feeds future Plan phases)

```
Session 1: S → P(empty) → A → R(create OM-001)
Session 2: S → P(recall OM-001) → A(faster) → R(update OM-001)
Session 3: S → P(recall OM-001, high confidence) → A(optimal) → R(nothing new)
```

---

## The Four Phases

### Phase S — Sense

**Purpose:** Extract structured signals from an unstructured request.

**Actions:**
1. Identify task type (incident / batch operation / query / config change / audit)
2. Extract service name from context
3. Extract error messages, user identifiers, timestamps
4. Determine environment (test / staging / production)

**Output:** A structured understanding of what needs to happen.

```markdown
Task: incident response
Service: payment-service
Error: "timeout after 9s on /api/order/create"
User: uid-12345
Environment: production
Time: 2026-07-15 14:30
```

### Phase P — Plan

**Purpose:** Recall past experience and choose an execution strategy.

**Actions:**
1. **First action: recall Operational Memory**
   - Filter by task_type + service + symptoms
   - Read the `better_action` field of matched memories
   - Decide whether to apply past lessons
2. Consult relevant runbooks if needed
3. Formulate execution plan

**Critical rule:** The Plan phase ALWAYS starts with memory recall. Even if no memories exist yet (e.g., first-ever task for a new service), the recall attempt must happen — it establishes the habit and ensures the system starts learning from day one.

**Recall method:**
```
1. Read index.md JSON block
2. Filter: task_type contains "incident" AND services contains "payment"
3. Match symptoms: "timeout" appears in om-001
4. Read om-001 full entry → better_action says "check row locks first"
5. Plan: start with row lock check instead of generic log search
```

### Phase A — Act

**Purpose:** Execute the plan. This is where the actual work happens.

**Actions vary by task type:**

| Task Type | Typical Act Phase |
|-----------|-------------------|
| Incident | Query logs → analyze → locate code → generate report |
| Batch operation | Download data → validate → generate script → risk assessment |
| Data query | Build SQL → execute → format results |
| Config change | Query current state → generate change command → risk assessment |

**Key principle during Act:** Follow the priority-based query strategy.

```
Priority 1: Cheapest deterministic verification (trace_id, specific ID)
Priority 2: Scoped query (path + time window)
Priority 3: Filtered broad query (error level + service)
Priority 4: Expensive global search (full text, user ID)
```

### Phase R — Reflect

**Purpose:** Capture lessons learned. This phase is **mandatory** — never skip it.

**The Four Questions:**

After every task completion, ask:

1. **Did I take a detour?** (wrong path before finding the right one)
2. **Was I faster than last time?** (or slower — regression?)
3. **Any unexpected pitfalls?** (something that would surprise a future agent)
4. **Can I distill a "next time, do X" rule?** (actionable improvement)

**If ANY answer is "yes"** → Create an Operational Memory entry.

**Reflect output:**
```markdown
Applied: om-2026-04-23-001 (used row lock check shortcut — saved 5 min)
Memorized: om-2026-07-15-001 (new: payment timeout in batch mode requires checking queue depth first)
```

---

## Task Classification and Routing

SPAR's Sense phase classifies tasks and routes them to specialized Act flows:

```
┌─────────────────────────────┐
│         S (Sense)           │
│  Extract: type, service,    │
│  error, user, environment   │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│         P (Plan)            │
│  1. Recall OM               │
│  2. Consult runbook         │
│  3. Choose strategy         │
└─────────────┬───────────────┘
              │
    ┌─────────┼─────────┬──────────┐
    ▼         ▼         ▼          ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│ A1:   │ │ A2:   │ │ A3:   │ │ A4:   │
│Incident│ │ Batch │ │ Query │ │Config │
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    └─────────┴─────────┴──────────┘
              │
              ▼
┌─────────────────────────────┐
│         R (Reflect)         │
│  4 questions → create OM    │
│  Tag: Applied / Memorized   │
└─────────────────────────────┘
```

---

## Integration with Operational Memory

SPAR's power comes from its tight coupling with the Operational Memory system:

| SPAR Phase | OM Interaction |
|------------|----------------|
| **Plan** | READ: recall relevant memories, apply `better_action` |
| **Act** | REFERENCE: follow strategies from recalled memories |
| **Reflect** | WRITE: create new memories, update hit counts |

**Lifecycle connection:**
- A memory recalled and effective → `hits + 1`, `confidence` may upgrade
- A memory recalled but unhelpful → note in reflect, may downgrade
- A memory never recalled for 6 months → flag as stale

---

## Example: Complete SPAR Cycle

**User request:** "payment-service 线上报 timeout，用户 uid-12345 下单失败"

### S (Sense)
```
Task type: incident
Service: payment-service
Symptom: timeout
User: uid-12345
Interface: order creation
Environment: production
```

### P (Plan)
```
1. Recall OM: found om-2026-04-23-001
   - "payment timeout → check row locks FIRST before broad log search"
   - confidence: medium, hits: 3
2. Plan:
   Step 1: Get trace_id from gateway logs (cheapest deterministic)
   Step 2: Check for row lock contention (from OM advice)
   Step 3: If not locks → broaden to full log analysis
```

### A (Act)
```
1. Query gateway logs with uid-12345 → found trace_id: abc-123
2. Query payment-service with trace_id → found "lock wait timeout"
3. Confirmed: row lock on orders table during concurrent batch insert
4. Root cause: batch job not using row-level isolation
5. Generated report with code location and fix suggestion
```

### R (Reflect)
```
Q1: Did I take a detour? NO — OM shortcut worked perfectly
Q2: Faster than last time? YES — skipped 5 min of generic log search
Q3: Unexpected pitfall? YES — batch job runs at 14:30, same time as peak orders
Q4: "Next time" rule? YES — "payment timeout at 14:xx → check batch job schedule conflict"

→ Created: om-2026-07-15-001 (batch schedule conflict pattern)
→ Updated: om-2026-04-23-001 (hits: 4, still valid)

Output tag: Applied: om-2026-04-23-001 | Memorized: om-2026-07-15-001
```

---

## Implementation Notes

### Making Reflect Mandatory

The Reflect phase is the easiest to skip ("task is done, why bother?"). To enforce it:

1. **Output format requires it** — every skill output template includes `Applied:` and `Memorized:` fields
2. **The 4 questions are a checklist** — even answering "no" to all 4 is a valid reflect (it means the execution was optimal)
3. **Reflect creates visible artifacts** — OM files in the knowledge base serve as proof of reflection

### SPAR vs Simple Agent Loops

| Feature | Simple Agent | SPAR Agent |
|---------|-------------|------------|
| Memory | None (forgets after each task) | Operational Memory persists across sessions |
| Learning | None | Confidence scoring + hit counting tracks reliability |
| Strategy | Same approach every time | Adapts based on past experience |
| Errors | May repeat same mistakes indefinitely | Explicitly prevents recurrence via OM recall |
| Speed | Constant (no improvement) | Improves over time (shortcuts accumulate) |
