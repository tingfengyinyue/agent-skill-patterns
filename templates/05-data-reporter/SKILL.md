# Template: Data Reporter Skill

Automated data collection, comparison, and visualization.

---

## When to Use This Pattern

- You need periodic reports (daily/weekly metrics)
- Reports compare current vs previous period (today vs yesterday, this week vs last)
- Multiple data sources need parallel querying
- Results feed into a visualization (dashboard, canvas, chart)

---

## SKILL.md Template

```markdown
---
name: daily-metrics-report
description: "Daily metrics reporter: queries databases for key business metrics (today + yesterday), computes deltas, updates visualization dashboard. Use when user asks for daily report, metrics, stats, dashboard update."
---

# Daily Metrics Report (daily-metrics-report)

Query databases → today + yesterday metrics → compute deltas → update dashboard.

## Quick Start

\```
/daily-report
\```

## Data Sources

| Source | Connection | Purpose |
|--------|-----------|---------|
| users-db | <connection-config> | Registration, login metrics |
| orders-db | <connection-config> | Order, payment metrics |

**Safety constraint:** SELECT only. Never INSERT/UPDATE/DELETE.

## Execution Flow

### Step 1: Execute Queries (Parallel)

Today group (queries 1-N) and yesterday group (queries N+1 to 2N)
can run **fully in parallel**. Same-source queries also parallelize.

**Query execution template:**
\```bash
<db-cli-tool> execute \
  --source=<source-id> \
  --query="<SQL>" 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for row in data.get('results', []):
    print(row)
"
\```

### Step 2: Query Definitions

#### Today Group
Time condition: `created_at >= CURRENT_DATE AND created_at < CURRENT_DATE + INTERVAL 1 DAY`

| # | Metric | Source | SQL |
|---|--------|--------|-----|
| 1 | New registrations | users-db | `SELECT COUNT(*) FROM users WHERE status != -1 AND <time_condition>` |
| 2 | Login success rate | users-db | `SELECT COUNT(*), SUM(CASE WHEN success THEN 1 ELSE 0 END) ... FROM login_log WHERE <time_condition>` |
| 3 | Orders placed | orders-db | `SELECT COUNT(*) FROM orders WHERE status = 'paid' AND <time_condition>` |
| 4 | Revenue | orders-db | `SELECT SUM(amount) FROM payments WHERE status = 'completed' AND <time_condition>` |

#### Yesterday Group
Same queries with time condition shifted to previous day.

### Step 3: Compute Deltas

For each metric pair (today, yesterday):
\```
change_amount = today - yesterday
change_rate = yesterday != 0
  ? (today - yesterday) / yesterday * 100%
  : (today > 0 ? "+∞" : "N/A")
\```

If yesterday = 0 and today = 0, display "—" (no meaningful delta).

### Step 4: Update Visualization

Update the dashboard file with new data:

\```tsx
const TODAY = {
  date: "<MM-DD>",
  registrations: <value>,
  loginSuccessRate: <value>,
  orders: <value>,
  revenue: <value>,
};

const YESTERDAY = {
  date: "<MM-DD>",
  registrations: <value>,
  loginSuccessRate: <value>,
  orders: <value>,
  revenue: <value>,
};
\```

### Step 5: Output Summary Table

\```markdown
| Metric | Today | Yesterday | Change | Rate |
|--------|-------|-----------|--------|------|
| Registrations | 1,757 | 2,445 | -688 | -28.1% |
| Login Success | 97.88% | 97.21% | +0.67% | — |
| Orders | 773 | 1,004 | -231 | -23.0% |
| Revenue | ¥12,500 | ¥15,800 | -¥3,300 | -20.9% |
\```

Note: today's data is as of current time; yesterday is full-day complete data.

## Query Optimization Notes

| Issue | Solution |
|-------|----------|
| Large table timeout | Ensure time-range index exists; retry once |
| Reserved word conflict | Wrap table names in backticks: \`order\` |
| Join performance | Always use smaller table as driver |
| NULL results | Today may have no records yet; fill with 0 |

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Query timeout (>9s) | Table too large | Retry once; narrow time if persists |
| Access denied | Credentials expired | Check credential configuration |
| NULL values | No activity yet today | Display as 0, note "partial day" |
| Dashboard not updated | File path changed | Verify dashboard file location |
```

---

## Key Design Decisions

1. **Parallel by default** — today and yesterday queries are independent; execute concurrently
2. **SQL explicitly documented** — no ambiguity about what's being queried
3. **Delta computation built-in** — raw numbers + change + rate for context
4. **Visualization integration** — skill doesn't just produce data, it updates the dashboard
5. **Partial data awareness** — today's data is always incomplete until EOD; acknowledge this
