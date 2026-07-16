# Template: Cross Validator Skill

Reads multiple documents and cross-references them to find inconsistencies.

---

## When to Use This Pattern

- You have multiple services/documents that reference each other
- Dependency declarations can drift out of sync
- You want automated detection of orphaned endpoints, broken references, or one-sided dependencies
- Consistency checking is a manual burden you want to automate

---

## SKILL.md Template

```markdown
---
name: api-consistency-check
description: "Cross-service API consistency checker: validates that service dependency declarations match actual endpoint definitions. Use when user says /api-check, consistency check, validate dependencies."
---

# API Consistency Check (api-consistency-check)

Cross-references all service documentation to find inconsistencies in API dependencies, message queue connections, and endpoint definitions.

## Trigger Conditions

When user says `/api-check`, `consistency check`, `validate service dependencies`.

## Usage

- `/api-check` — full check across all services
- `/api-check <service-name>` — check only one service's upstream/downstream

## Execution Flow

### Step 1: Load Service Documents

Read all service documentation files from `knowledge-base/services/*.md`.

### Step 2: Extract Dependency Matrix

From each service document, extract:
- **Downstream calls:** which services/endpoints this service calls
- **Upstream callers:** who calls this service
- **Message queue:** topics produced and consumed

Build a dependency matrix:

\```
| From → To | Endpoint | Direction |
|-----------|----------|-----------|
| service-a → service-b | POST /api/order/create | downstream |
| service-b → service-c | GET /api/user/:id | downstream |
\```

### Step 3: Cross-Validate

For each dependency relationship `A calls B at /path`:

**Check 1 — Endpoint Existence:**
Does B's "API Endpoints" section list `/path`?
- YES → pass
- NO → flag: "A claims to call B at /path, but B has no such endpoint"

**Check 2 — Bidirectional Consistency:**
A says "I call B". Does B say "A calls me"?
- YES → pass
- NO → flag: "One-sided dependency: A→B recorded in A but not B"

**Check 3 — Message Queue Consistency:**
A produces `topic-x`. Is there any service consuming `topic-x`?
- YES → pass
- NO → flag: "Orphan producer: A produces topic-x but no consumer found"

A consumes `topic-y`. Is there any service producing `topic-y`?
- YES → pass
- NO → flag: "Orphan consumer: A consumes topic-y but no producer found"

### Step 4: Generate Report

\```markdown
## API Consistency Report

### Check Time: <date>

---

### ⚠️ Inconsistencies Found

| Type | Source | Target | Problem | Suggestion |
|------|--------|--------|---------|------------|
| Missing endpoint | service-a | service-b | A calls B at /api/foo, but B has no /api/foo | Doc outdated or endpoint removed |
| One-sided dep | service-a | service-b | A records calling B, B doesn't record being called by A | Update B's upstream section |
| Orphan producer | service-a | — | A produces topic-x, no consumer | Confirm if consumer is missing from docs |

### ✓ Validated (Consistent)

| Relationship | Status |
|-------------|--------|
| service-a → service-b /api/order | ✓ |
| service-b → service-c /api/user | ✓ |

### Dependency Matrix

|  | service-a | service-b | service-c |
|--|-----------|-----------|-----------|
| service-a | — | ✓ | |
| service-b | | — | ✓ |
| service-c | ✓ | | — |
\```

### Step 5: Auto-Fix Suggestions

For each inconsistency:
- **One-sided dependency:** provide the doc snippet to add
- **Missing endpoint:** suggest user confirm if doc is stale or endpoint removed
- **Orphan MQ:** suggest user check if consumer service doc is incomplete

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Service doc not found | Service not yet documented | List undocumented services |
| Section missing | Doc structure incomplete | Flag and continue with available data |
| Ambiguous endpoint match | Path params like /:id | Match on path pattern, not literal |

## Notes

- This check is documentation-based, not code-based
- External dependencies (third-party APIs) are excluded
- Run after every scan-services to catch drift early
```

---

## Key Design Decisions

1. **Three types of checks** — existence, bidirectionality, and orphan detection cover most consistency issues
2. **Matrix visualization** — gives an at-a-glance view of the full dependency graph
3. **Actionable suggestions** — don't just report problems, suggest the fix
4. **Documentation-based** — works without code access; validates the knowledge base itself
