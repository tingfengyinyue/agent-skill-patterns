# Template: Workflow Engine Skill

State-machine driven operational workflows with memory recall and reflection.

---

## When to Use This Pattern

- The task has multiple phases (investigation, execution, documentation)
- Different task types require different execution paths (routing/dispatch)
- Past experience should inform current execution (memory recall)
- Completed tasks should generate reusable knowledge (reflection)

---

## SKILL.md Template

```markdown
---
name: ops-troubleshooter
description: "Operational task handler with SPAR cognitive loop: sense → recall experience → execute → reflect and memorize. Use when user reports issues, requests operations, or asks for troubleshooting."
---

# Ops Troubleshooter (ops-troubleshooter)

Automated operational task handling: smart identification → experience recall → execution → knowledge capture.

## Knowledge Base References

| Resource | Path | Purpose |
|----------|------|---------|
| Knowledge base | `knowledge-base/` | Services, runbooks, incidents, memory |
| Service docs | `knowledge-base/services/*.md` | Service architecture reference |
| Runbooks | `knowledge-base/runbooks/` | Procedural guides |
| Operational Memory | `knowledge-base/memory/operational/` | Lessons learned |

## SPAR Workflow (Mandatory)

Every task walks through four phases. **Never skip Reflect.**

| Phase | Name | Key Action |
|-------|------|-----------|
| **S** | Sense | Extract service, error, user, environment |
| **P** | Plan | **First action: recall OM**, then choose strategy |
| **A** | Act | Execute per task type (see routing below) |
| **R** | Reflect | Ask 4 questions, create OM if any "yes" |

**Output must include:** `Applied: om-xxx` and `Memorized: om-yyy` tags.

### Plan Phase: OM Recall

\```
1. Read memory/operational/index.md JSON block
2. Filter by task_type + service + symptoms
3. Read matched entries' better_action
4. Incorporate into execution plan
\```

### Reflect Phase: 4 Questions (Mandatory)

1. Did I take a detour?
2. Was I faster than last time?
3. Any unexpected pitfall?
4. Can I distill "next time, do X"?

Any "yes" → create OM entry (see operational-memory-spec.md).

## Task Classification and Routing

| Task Type | Trigger Keywords | Route To |
|-----------|-----------------|----------|
| Incident response | error, timeout, failure, 500 | → Flow A1 |
| Batch operation | batch, import, script, bulk | → Flow A2 |
| Configuration | config, enable, permission | → Flow A3 |
| Data query | query, statistics, export | → Flow A4 |

## Flow A1: Incident Response

\```
0. [P] Recall OM (task_type=incident + service + symptoms)
1. [A] Extract key info → identify environment → map to log source
2. [A] Query logs (priority-based strategy):
     ① trace_id (cheapest, most deterministic)
     ② endpoint + time window
     ③ error level + service name
     ④ user_id / keyword (last resort)
3. [A] Analyze logs → identify root cause → locate code
4. [A] Generate report (see output template below)
5. [A] Save incident record to knowledge-base/incidents/
6. [R] Reflect → create OM if warranted
\```

## Flow A2: Batch Operation

\```
0. [P] Recall OM (focus: encoding, field mapping, rate limits)
1. [A] Extract: target, data source, required fields, operation type
2. [A] Download/parse data → validate format
3. [A] Generate script → preview (first 5 rows) → risk assessment
4. [A] Provide script + execution instructions + rollback plan
5. [R] Reflect → create OM
\```

## Flow A3: Configuration Change

\```
0. [P] Recall OM (focus: hidden side effects)
1. [A] Extract change request → query current state
2. [A] Generate change command → risk assessment
3. [A] Output: change plan + rollback steps
4. [R] Reflect → create OM
\```

## Flow A4: Data Query

\```
0. [P] Recall OM (focus: query optimization, table schemas)
1. [A] Understand query need → check schema reference → build query
2. [A] Execute query → format results
3. [A] Return formatted data with context
4. [R] Reflect → create OM
\```

## Output Templates

### Incident Report

\```markdown
## Incident Analysis Report

**Service:** <service>  **Endpoint:** <path>  **Time:** <timestamp>
**Affected:** <scope>  **Trace:** <trace_id>

### Root Cause
<root cause description>

### Analysis Steps
1. ...

### Code Location
- <file>:<line>

### Fix Recommendation
1. Immediate: <workaround>
2. Permanent: <proper fix>

Applied: om-xxx | Memorized: om-yyy
\```

### Batch Operation Plan

\```markdown
## Batch Operation Plan

**Target:** <what>  **Operation:** <type>  **Data Source:** <source>

### Data Preview (first 5 rows)
| col1 | col2 | col3 |
|------|------|------|
| ... | ... | ... |

### Execution Steps
1. ...

### Risk Assessment & Rollback
- Risk: <description>
- Rollback: <steps>

Applied: om-xxx | Memorized: om-yyy
\```

## Safety Rules

1. **Read-only by default** — only query; never modify without explicit confirmation
2. **Human confirmation required** — for database changes, bulk deletes, config changes
3. **Audit trail** — all operations recorded
4. **Data masking** — auto-mask passwords, tokens, PII in output

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Service not recognized | Unknown service name | List known services |
| Log source not found | Environment mismatch | Verify environment detection |
| Query timeout | Too broad | Narrow scope, suggest alternatives |
| No OM matches | Novel problem | Proceed without shortcuts, will create new OM |
```

---

## Key Design Decisions

1. **SPAR is non-negotiable** — every execution includes Plan (recall) and Reflect (create)
2. **Task routing** — classify first, then dispatch to specialized flows
3. **Priority-based queries** — cheap deterministic checks before expensive broad ones
4. **Mandatory output tags** — `Applied:` and `Memorized:` make the learning loop visible
5. **Safety by default** — read-only unless explicitly told to mutate
