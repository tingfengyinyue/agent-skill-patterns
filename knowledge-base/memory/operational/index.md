# Operational Memory Index

> SPAR Reflect phase output: strategic lessons from execution experience.
> **Not** fact records — these are "next time, do X" optimization notes.
>
> **Recall method:** During every Plan phase, filter JSON block by task_type + service + symptoms.
> **Full spec:** [Operational Memory Specification](../../../docs/operational-memory-spec.md)

Last updated: 2026-07-15

## Quick Recall Index (JSON)

```json
[
  {"id":"om-2026-07-01-001","task_type":["incident"],"services":["payment-service"],"symptoms":["timeout","500","slow"],"tags":["database","row-lock","cron"],"confidence":"medium","hits":3,"status":"active"},
  {"id":"om-2026-07-05-001","task_type":["incident","config"],"services":["auth-service","gateway"],"symptoms":["403","token expired","not authorized"],"tags":["JWT","token","config"],"confidence":"medium","hits":2,"status":"active"},
  {"id":"om-2026-07-10-001","task_type":["query"],"services":["order-service"],"symptoms":["not found","empty result"],"tags":["API","fallback","alternative-query"],"confidence":"low","hits":1,"status":"active"}
]
```

## All Entries

<!-- Note: In a real vault, each link points to its own om-*.md file.
     Here they reference _template.md to show the format. Replace with
     actual file paths as you create real entries. -->

| ID | Title | Confidence | Hits | Status | Created |
|----|-------|-----------|------|--------|---------|
| [om-2026-07-01-001](_template.md) | Payment timeout → check batch cron schedule first | medium | 3 | active | 2026-07-01 |
| [om-2026-07-05-001](_template.md) | Auth 403 → check token expiry config before log search | medium | 2 | active | 2026-07-05 |
| [om-2026-07-10-001](_template.md) | Query returns empty → try alternative API dimension | low | 1 | active | 2026-07-10 |

## By task_type

### Incident
- om-2026-07-01-001 — Payment timeout → check batch cron first
- om-2026-07-05-001 — Auth 403 → check token config first

### Data Query
- om-2026-07-10-001 — Empty result → try alternative query dimension

### Batch Operation
- *(none yet — will populate after first batch task)*

## By Service

### payment-service
- om-2026-07-01-001

### auth-service
- om-2026-07-05-001

### order-service
- om-2026-07-10-001

## Meta-Patterns

> **Do the cheapest deterministic verification first; push expensive global searches to the end.**

- om-2026-07-01-001: check cron status (1 query, 2s) before broad log search (many queries, 5+ min)
- om-2026-07-05-001: decode token + check config (local, instant) before gateway trace search

> **API returning empty ≠ data doesn't exist. Try a different query dimension.**

- om-2026-07-10-001: SearchByName returns empty → ListAll + filter finds it

## Maintenance Rules

- **New:** After any Reflect phase with a "yes" answer → create entry + update this index
- **Hit:** Recalled + effective → `hits += 1`, update `last_verified_at`
- **Downgrade:** Ineffective 1x → `confidence` drops one level
- **Deprecate:** Ineffective 2x consecutively → `status: deprecated`
- **Supersede:** Better memory covers same ground → old one `status: superseded`
- **Stale:** 6 months un-recalled → flag for review
- **Graduate:** `confidence: high` + `hits ≥ 10` + 3 months stable → extract to runbook
