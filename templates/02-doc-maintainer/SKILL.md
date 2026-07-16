# Template: Doc Maintainer Skill

Automatically keeps knowledge base documentation in sync with source code repositories.

---

## When to Use This Pattern

- You have multiple services/repos whose documentation drifts from reality
- You want documentation to auto-update when code changes
- Full re-scans are too expensive; you need incremental processing
- Different code paths map to different documentation sections

---

## SKILL.md Template

```markdown
---
name: scan-services
description: "Service documentation scanner: auto-updates knowledge base docs by scanning code repos. Supports incremental and full scan modes. Use when user says /scan, update docs, sync documentation."
---

# Service Documentation Scanner (scan-services)

Scans code repositories → detects changes → updates knowledge base documentation.

## Trigger Conditions

When user says `/scan-services`, `update docs`, `sync documentation`.

## Usage

- `/scan-services` — incremental (only repos with new commits)
- `/scan-services full` — full re-scan of all repos
- `/scan-services <service-name>` — scan one specific service

## Service Registry

| Service | Repository | Default Branch |
|---------|-----------|----------------|
| service-a | <repo-url> | main |
| service-b | <repo-url> | main |
| service-c | <repo-url> | master |

## Execution Flow

### Step 1: Read State

Read `.service-scan-state.json`:
\```json
{
  "services": {
    "service-a": {"last_commit_sha": "abc123", "last_scan": "2026-07-01"},
    "service-b": {"last_commit_sha": "def456", "last_scan": "2026-07-10"}
  }
}
\```

### Step 2: Check for Updates (parallel)

For each service:
\```bash
git clone --depth=50 <repo> /tmp/scan/<service>
cd /tmp/scan/<service>
git log <last_commit_sha>..HEAD --oneline
\```

- No new commits → **skip** (log: "service-a: no changes")
- Has new commits → proceed to scan

### Step 3: Determine What Changed

\```bash
git diff <last_commit>..HEAD -- <relevant-paths>
\```

**Diff path → documentation section mapping:**

| Code Path | Documentation Section |
|-----------|-----------------------|
| `routes/` or `router/` | API Endpoints |
| `models/` or `schema/` | Data Models |
| `client/` or `rpc/` | Service Dependencies |
| `consumer/` or `handler/` | Message Queue |
| `cron/` or `schedule/` | Scheduled Tasks |
| `service/` or `domain/` | Business Logic |

### Step 4: Scan Changed Sections

For each affected section, read the relevant source files and extract:
- **API Endpoints:** method, path, handler function name
- **Data Models:** table/collection name, key fields, relationships
- **Dependencies:** which external services are called, via what interface
- **Message Queue:** producer topics, consumer topics, processing logic
- **Scheduled Tasks:** cron expression, task name, description

### Step 5: Update Documentation

Update `knowledge-base/services/<service>.md`:
- Only rewrite sections that changed
- Preserve manually-authored sections (like "Related OM" at bottom)
- Update frontmatter `last_scan` date

### Step 6: Update State

\```json
{
  "services": {
    "service-a": {"last_commit_sha": "<new-HEAD>", "last_scan": "2026-07-15"}
  }
}
\```

### Step 7: Cleanup

\```bash
rm -rf /tmp/scan/
\```

## Output Summary

\```
Service Scan Complete:
- service-a: updated (API Endpoints, Data Models)
- service-b: no changes (skipped)
- service-c: updated (Message Queue)

Total: 2 services updated, 1 skipped
\```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Clone failed | Network or auth issue | Retry once; if fails, skip and report |
| No state file | First run | Treat as full scan for all services |
| Diff too large | Major refactor | Fall back to full scan for that service |
| Path not found | Project structure changed | Log warning, scan available paths |
```

---

## Key Design Decisions

1. **Incremental by default** — only process repos with new commits since last scan
2. **Diff path → section mapping** — surgical updates instead of full rewrites
3. **State file as single source of truth** — simple JSON, easy to inspect and debug
4. **Preserve manual content** — auto-generated sections coexist with human annotations
5. **Parallel service checking** — check all repos for updates concurrently
