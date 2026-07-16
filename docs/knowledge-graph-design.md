# Knowledge Graph Design

How the knowledge base achieves three things simultaneously: **minimal token cost**, **rich cross-referencing**, and **bidirectional temporal awareness**.

---

## The Core Problem

AI agents have a finite context window (the amount of text they can "see" at once). A knowledge base with 50 service docs, 200 operational memories, and 100 incident records cannot be loaded wholesale — it would exhaust the context window before the agent starts working. Yet the agent needs to:

1. Find the right knowledge *fast* (without reading everything)
2. Follow *connections* between related entities (incident → OM → service)
3. Understand *temporal direction* (what happened before vs. what to do next time)

This design solves all three simultaneously.

---

## Architecture: A Graph, Not a Filing Cabinet

```
                    ┌─────────────┐
            ┌──────│   Service    │──────┐
            │      │  (Layer 1)   │      │
            │      └──────┬───────┘      │
            │             │              │
     "affects"    "documents"     "configured by"
            │             │              │
            ▼             ▼              ▼
    ┌───────────┐  ┌───────────┐  ┌───────────┐
    │ Incident  │  │  Runbook  │  │   Config   │
    │ (Layer 3) │  │ (Layer 2) │  │  (Layer 2) │
    └─────┬─────┘  └───────────┘  └───────────┘
          │                ▲
    "learned"         "graduates to"
          │                │
          ▼                │
    ┌───────────┐          │
    │    OM     │──────────┘
    │ (Layer 4) │
    └───────────┘
```

Every entity in the knowledge base is a **node** with typed **edges** to related nodes. This is not a tree structure — it's a graph with cycles (OM references the incident it came from, while the incident references the OM it generated).

---

## Highlight 1: Funnel Read — Load Only What You Need

> Also known as "token-efficient traversal" — the agent reads knowledge like a funnel: wide filter first (cheap), narrow deep-read next (only if needed).

### The Pattern

Instead of loading all related knowledge, the agent reads in expanding concentric circles — stopping as soon as it has enough context:

```
Cost:   ~50 tokens     ~100 tokens     ~300 tokens      ~500+ tokens
        ─────────────────────────────────────────────────────────────▶

Ring 0: JSON index     Read matching    Read full        Read linked
        (filter only)  OM entries       service doc      incident history
```

### Concrete Example

Task: "payment-service timeout at 14:30"

```
Step 1: Read OM index JSON block                          [50 tokens]
        → Filter: service=payment, symptoms=timeout
        → Match: om-2026-07-01-001 (confidence: medium, hits: 3)

Step 2: Read om-2026-07-01-001.better_action              [80 tokens]
        → "Check if batch-import cron is running (starts 14:30)"
        → Agent now knows what to check FIRST

Step 3: (Only if Step 2 insufficient)
        Read payment-service.md → Scheduled Tasks section [150 tokens]

Step 4: (Only for novel problems)
        Search incidents/ for similar past events          [200+ tokens]
```

**Typical resolution: Steps 1-2 = 130 tokens.**
**Without graph traversal: read entire service doc + all OMs = 2000+ tokens.**

### Why This Works

The JSON index acts as a **pre-filter** for the knowledge base — like a table of contents that lets you skip irrelevant chapters without opening them:

- Every entry is represented in the index (nothing is missed)
- Typical filtering eliminates 80-95% of entries without reading their full content
- Cost is fixed (~50 tokens) regardless of how large the knowledge base grows

---

## Highlight 2: Two-Way Links — Navigate in Any Direction

> "Bidirectional cross-referencing" means: when A links to B, B also links back to A. No matter which node you're at, you can find all related nodes without searching.

### Every Edge is a Two-Way Street

When an incident creates an OM, **both** the incident and the OM record the relationship:

```yaml
# In incident file (2026-07-15-payment-timeout.md)
lessons:
  - Created OM: om-2026-07-15-001

# In OM file (om-2026-07-15-001.md)
evidence:
  incidents: [2026-07-15-payment-timeout]
```

When a service doc lists its dependencies, the **downstream** service also lists the **upstream** caller:

```markdown
# In payment-service.md
## Downstream (this service calls)
- notification-service: POST /api/notify/send

# In notification-service.md
## Upstream (calls this service)
- payment-service: POST /api/notify/send
```

### Why Bidirectional Matters

| Scenario | Forward link needed | Backward link needed |
|----------|-------------------|---------------------|
| "What did we learn from this incident?" | incident → OM | — |
| "Why does this OM exist?" | — | OM → incident |
| "What calls payment-service?" | — | service → upstream callers |
| "What does payment-service depend on?" | service → downstream | — |
| "Is this runbook still relevant?" | — | runbook ← OM that graduated |

Without bidirectional links, the agent must **scan all files** to find backward references (expensive). With them, it's a **direct lookup** — go straight to the answer in constant time, regardless of how many files exist.

### The Cross-Reference Matrix

```
            Service    Incident    OM        Runbook    Config
Service        —       affects     about     guides     defines
Incident    affected      —       learned   followed      —
OM          applies    evidence      —      graduates   relates
Runbook     targets       —       from         —       references
Config      configures    —         —           —          —
```

Every cell with a value means there's a direct link navigable from either direction.

---

## Highlight 3: Time Flows Both Ways — Past Informs Future

> "Bidirectional temporal design" means: knowledge has both a backward pointer (where it came from) and a forward pointer (what to do next time). The OM entry is the bridge connecting past incidents to future decisions.

### Two Directions of Time

Knowledge in the system flows in two temporal directions:

```
PAST ◀──────────────────────────────────────────────────▶ FUTURE

  Incidents             OM                  Runbooks
  (what happened)       (the bridge)        (what to do)
  ────────────────────────────────────────────────────────

  Record facts    →   Extract lesson   →   Graduated
  about the past      for the future       procedures
```

**Backward-looking (forensic):**
- Incidents record *what happened* (facts, timeline, root cause)
- OM's `context_before` records *what went wrong* (the detour)
- OM's `evidence` links back to the triggering event

**Forward-looking (prescriptive):**
- OM's `better_action` tells the agent *what to do next time*
- Runbooks encode *procedures* for execution
- Service docs describe *current state* of the system

### The OM as Temporal Bridge

Operational Memory is the **only entity** that lives in both directions simultaneously:

```
     PAST                    PRESENT                   FUTURE
       │                        │                        │
  [Incident]              [OM Entry]               [Next Task]
  "On 07-15,              "Payment timeout         Agent recalls
   payment timed           between 14-15:          OM, checks cron
   out because of          check batch cron        FIRST → resolves
   batch job locks"        schedule first"         in 30 seconds
       │                        │                        │
       └── evidence ──────────▶ │ ◀── recall ───────────┘
```

This is why OM has both `evidence.incidents` (pointing backward) and `trigger.symptoms` (matching forward). It's a temporal bridge connecting past events to future decisions.

### Knowledge Lifecycle — Birth, Growth, Retirement

Knowledge is not static. It has a lifecycle that moves through time:

```
Birth                   Growth                  Maturity                Retirement
─────────────────────────────────────────────────────────────────────────────────
Incident happens   →   OM created         →   OM verified (hits↑)  → Graduated
(Layer 3)              (Layer 4, low)         (Layer 4, medium)      to Runbook
                                                                      (Layer 2)
                                              OR
                                              OM contradicted        → Deprecated
                                              (ineffective 2x)        (archived)
```

**Time-based markers in every entity:**

| Entity | Temporal fields | Purpose |
|--------|----------------|---------|
| Service | `last_scan` | When was this doc last verified against code? |
| Incident | `date`, Timeline table | When did it happen, in what sequence? |
| OM | `created_at`, `last_verified_at`, `hits` | When born, when last confirmed useful |
| Runbook | keywords: `last_reviewed` | Is this procedure still current? |
| State file | `last_commit_sha`, `last_scan` | What has been processed up to what point? |

### Staleness Detection — Automatic Expiration

Time flows forward, knowledge decays. The system actively detects outdated content:

```
Rule 1: OM not recalled for 6 months     → flag as stale
Rule 2: Service doc not scanned for 30d  → trigger rescan
Rule 3: Runbook not referenced for 90d   → flag for review
Rule 4: Incident older than 12 months    → archive (low priority in recall)
```

This prevents the knowledge base from becoming a graveyard of outdated information.

---

## How It All Connects (The Full Picture)

Given a task "payment-service returns 500 on /api/order/create":

```
1. SENSE: Extract → service=payment, symptom=500, endpoint=/api/order/create

2. PLAN (Token-efficient traversal):
   ├── Read OM index JSON (50 tokens) → filter by service + symptom
   ├── Match: om-2026-07-01-001 (payment timeout → check cron)
   ├── Read better_action (80 tokens)
   └── Strategy: check batch schedule first, then standard diagnosis

3. ACT (Graph-guided execution):
   ├── Check cron status → not running → not the known cause
   ├── Follow service graph edge: payment → downstream deps
   │   └── notification-service: is it responding?
   ├── Read payment-service.md (only Dependencies section, 100 tokens)
   └── Diagnose: downstream notification-service timeout → cascading 500

4. REFLECT (Temporal bridge creation):
   ├── Q1: Detour? YES — checked cron first (from OM), but issue was downstream
   ├── Q4: "Next time"? YES → "500 on payment + notification in deps → check notification-service health first"
   ├── Create: om-2026-07-16-001 (new OM, confidence: low)
   │   ├── evidence.incidents → [today's incident]     ← backward link
   │   └── trigger.symptoms → [500, order, cascade]    ← forward matching
   └── Update incident record → lessons: "Created OM om-2026-07-16-001"
```

**Total knowledge tokens consumed: ~280**
**Knowledge entities created: 1 OM + 1 incident (with full bidirectional links)**
**Future benefit: next similar task starts at Step 2 with a better strategy**

---

## Design Principles Summary

| Principle | Implementation | Benefit |
|-----------|---------------|---------|
| **Read cheap, drill deep** | JSON index → relevant entry → linked docs | 85% token reduction |
| **Link both directions** | Every edge stored on both endpoints | Direct lookup, no scanning |
| **Bridge past and future** | OM has evidence (past) + trigger (future) | Compounding intelligence |
| **Track time everywhere** | Timestamps, hit counts, staleness rules | Self-maintaining freshness |
| **Graph, not tree** | Cycles allowed (OM↔incident, service↔service) | Natural relationship modeling |
