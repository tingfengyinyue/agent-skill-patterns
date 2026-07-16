---
name: ops-troubleshooter
description: "Operations troubleshooter with SPAR loop: incident response, batch operations, data queries, config changes. Recalls past experience, executes with priority-based strategies, reflects and memorizes lessons. Use when user reports errors, requests troubleshooting, asks for operational help, mentions timeout/500/failure."
---

# Ops Troubleshooter

Automated operational task handling with compounding intelligence.

## Knowledge Base

| Resource | Path | Purpose |
|----------|------|---------|
| Service docs | `knowledge-base/services/*.md` | Architecture reference |
| Runbooks | `knowledge-base/runbooks/` | Procedural guides |
| OM Index | `knowledge-base/memory/operational/index.md` | Lessons learned |
| Incidents | `knowledge-base/incidents/` | Historical events |

## SPAR Workflow (Mandatory — Never Skip Reflect)

| Phase | Action |
|-------|--------|
| **S** Sense | Extract: task_type, service, error, user, environment |
| **P** Plan | 1st action: recall OM by task_type + service + symptoms |
| **A** Act | Execute per task type routing (see below) |
| **R** Reflect | 4 questions → create OM if any answer is "yes" |

Output **must** include: `Applied: om-xxx | Memorized: om-yyy`

## Environment Detection

| User says | Environment | Config profile |
|-----------|-------------|---------------|
| "test" / "testing" | Test | test |
| "staging" / "uat" | Staging | staging |
| "prod" / (default) | Production | default |

## Task Routing

| Type | Keywords | Flow |
|------|----------|------|
| Incident | error, timeout, 500, failure, slow | → A1 |
| Batch operation | batch, import, bulk, script | → A2 |
| Config change | config, enable, permission, toggle | → A3 |
| Data query | query, count, statistics, export | → A4 |

## Flow A1: Incident Response

```
0. [P] Recall OM (filter: task_type=incident + service + symptoms)
     → Read index.md JSON block
     → Match candidates → read better_action
     → Integrate into plan

1. [A] Extract: service, error message, trace_id, user_id, time
     → Map service to log source (see service docs)

2. [A] Query logs (PRIORITY ORDER — do not skip levels):
     ① trace_id exists? → query by trace_id (cheapest, most deterministic)
     ② specific endpoint + time window known? → scoped query
     ③ service + error level? → filtered query
     ④ only keywords/user_id? → broad search (last resort, warn about noise)

3. [A] Analyze:
     → Identify timeout location / error stack / latency breakdown
     → Cross-reference with service dependency map
     → If cross-service: follow dependency chain, query downstream logs

4. [A] Locate code:
     → Use log file path + line number
     → Check service doc for architecture context
     → Identify root cause function/module

5. [A] Generate report:
     → Service, endpoint, trace_id, time
     → Root cause (1-2 sentences)
     → Code location (file:line)
     → Fix recommendation (immediate + permanent)

6. [A] Save incident:
     → Create knowledge-base/incidents/YYYY-MM-DD-<service>-<slug>.md

7. [R] Reflect (MANDATORY):
     → Q1: Did I take a detour?
     → Q2: Was I faster than last time?
     → Q3: Unexpected pitfall?
     → Q4: "Next time, do X" distillable?
     → If any YES: create OM entry, update index
```

## Flow A2: Batch Operation

```
0. [P] Recall OM (focus: encoding, field mapping, rate limits, rollback)
1. [A] Extract: target system, data source, fields needed, operation type
2. [A] Download data → parse → validate format and completeness
3. [A] Generate execution script
4. [A] Preview (first 5 rows) → risk assessment → rollback plan
5. [A] Output: script + instructions + risks + rollback
6. [R] Reflect → OM if detour or pitfall encountered
```

## Flow A3: Config Change

```
0. [P] Recall OM (focus: hidden side effects of similar changes)
1. [A] Extract change request → query current state
2. [A] Generate change command → assess impact
3. [A] Output: change plan + verification steps + rollback
4. [R] Reflect → OM if unexpected dependency or side effect discovered
```

## Flow A4: Data Query

```
0. [P] Recall OM (focus: query optimization, correct table/field names)
1. [A] Understand need → read relevant schema reference
2. [A] Build query (prefer indexed fields, avoid full scans)
3. [A] Execute → parse results
4. [A] Format output with context (what the numbers mean)
5. [R] Reflect → OM if query required unexpected optimization
```

## Output Templates

### Incident Report

```markdown
## Incident Report

**Service:** <name> | **Endpoint:** <path> | **Time:** <timestamp>
**Trace:** <trace_id> | **Affected:** <scope>

### Root Cause
<1-2 sentence explanation>

### Evidence
- Log: <key log line>
- Code: <file>:<line>

### Fix
1. Immediate: <stop the bleeding>
2. Permanent: <prevent recurrence>

Applied: om-xxx | Memorized: om-yyy
```

### Batch Operation Plan

```markdown
## Batch Operation

**Target:** <system> | **Type:** <operation> | **Records:** <count>

### Preview (5 rows)
| field1 | field2 | field3 |
|--------|--------|--------|

### Script
\`\`\`bash
<generated script>
\`\`\`

### Risks & Rollback
- Risk: <what could go wrong>
- Rollback: <how to undo>

Applied: om-xxx | Memorized: om-yyy
```

## Safety Rules

1. **SELECT only** — never modify data without explicit user confirmation
2. **Preview first** — always show sample before bulk execution
3. **Rollback required** — every mutation plan must include undo steps
4. **Mask secrets** — auto-redact passwords, tokens, PII in output

## Error Handling

| Error | Resolution |
|-------|------------|
| Service not recognized | List available services from knowledge-base/services/ |
| Log source not found | Verify environment detection; check service doc mapping |
| Query timeout | Narrow time range; retry once; suggest more specific filters |
| No OM matches | Proceed without shortcuts; will create new OM in Reflect |
| Trace_id not found | Fall back to priority 2 (endpoint + time) |
| Cross-service issue | Read service_dependency_map, follow the chain |
