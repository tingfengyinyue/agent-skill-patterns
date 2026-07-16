# Template: CLI Wrapper Skill

Wraps a command-line tool with domain knowledge, natural language interface, and intelligent query strategies.

---

## When to Use This Pattern

- You have a CLI tool (cloud provider CLI, database client, log query tool)
- The tool requires specific flags, IDs, and configurations that vary by environment
- Users want to ask questions in natural language instead of writing raw commands
- Query results need formatting and contextual interpretation

---

## SKILL.md Template

```markdown
---
name: <tool-name>-query
description: "<Tool> query skill: natural language interface for <tool>. Supports <use cases>. Use when user mentions <trigger words>."
---

# <Tool Name> Query (<tool-name>-query)

<One-line description of what this skill does.>

## Trigger Conditions

When user says `/<command>`, `<natural language variant 1>`, `<variant 2>`.

## Usage

- `/<command>` — interactive mode
- `/<command> <natural language query>` — auto-parsed query
- `/<command> --service=X --last=1h --error` — explicit parameters

## Configuration

### Environment Detection

| Keyword in user message | Environment | Profile/Config |
|-------------------------|-------------|----------------|
| "test" / "testing" | Test | profile=test |
| "staging" / "uat" | Staging | profile=staging |
| "prod" / (default) | Production | profile=default |

### Resource Mapping

| Service | Resource ID (Test) | Resource ID (Prod) |
|---------|-------------------|-------------------|
| service-a | <test-resource-id> | <prod-resource-id> |
| service-b | <test-resource-id> | <prod-resource-id> |

## Query Strategy (Priority-Based)

> Meta-pattern: cheapest deterministic verification first.

| Priority | Strategy | When to Use |
|----------|----------|-------------|
| 1 | Exact ID lookup | User provides trace_id or request_id |
| 2 | Scoped: endpoint + time | Known path and time window |
| 3 | Filtered: level + service | Know the service, looking for errors |
| 4 | Broad: keyword search | Last resort, warn about noise |

## Execution Flow

### Step 1: Parse Intent

Extract from user message:
- Service name (match against known services)
- Time range (default: last 1 hour)
- Identifiers (trace_id, user_id, request_id)
- Keywords (error messages, function names)

### Step 2: Build Command

Template:
\```bash
<cli-tool> <subcommand> \
  --<resource-flag>=<mapped-resource-id> \
  --<time-from>="YYYY-MM-DD HH:MM:SS" \
  --<time-to>="YYYY-MM-DD HH:MM:SS" \
  --<query-flag>="<constructed-query>"
\```

### Step 3: Execute and Parse

\```bash
<command> 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
# Parse and format results
for item in data.get('results', []):
    print(item)
"
\```

### Step 4: Format Output

\```
=== Query Results ===

Conditions:
  Service: <service>
  Time: <from> ~ <to>
  Filter: <applied filters>

Results: N entries found

[1] <timestamp>
    <key field 1>: <value>
    <key field 2>: <value>

[2] ...

=== Suggested Next Steps ===
1. <contextual suggestion based on results>
2. <related command suggestion>
\```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| --service | Service name | auto-detect |
| --last | Time range (1h, 30m, 2h) | 1h |
| --error | Filter errors only | false |
| --limit | Max results | 100 |

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Timeout | Query too broad | Narrow time range or add filters |
| Access denied | Credentials expired | Check credential configuration |
| No results | Wrong service/time | Suggest alternatives |
| Too many results | Query too broad | Auto-truncate + suggest narrowing |
```

---

## Key Design Decisions

1. **Environment detection from natural language** — user says "test environment" and the skill auto-selects the right config
2. **Priority-based query strategy** — prevents expensive broad searches when cheap exact queries would work
3. **Result formatting with next steps** — don't just dump data, help the user know what to do next
4. **Error table is exhaustive** — every known failure mode has a resolution
