# Agent Skill Patterns

[中文版文档 / Chinese Documentation](docs/zh/README.md)

Build AI agent skills that **recall experience, load knowledge efficiently, and improve over time**.

---

## Why This Project?

Most AI agent setups treat knowledge as static context — dump a bunch of docs into the prompt and hope for the best. This works until your knowledge base grows beyond what a context window can hold.

### From My Own Pain Point to Reusable Patterns

I originally designed this architecture to solve a concrete problem in my own work: when taking ownership of many unfamiliar projects at once, I needed to understand their code structure, service relationships, and history quickly enough to diagnose and resolve production issues. The traditional approach meant repeatedly searching through code, documentation, and incident history, while very little of that work carried over to the next task.

To address this, I designed and iterated on an internal tool in daily use: operational procedures became Skills; services, incidents, runbooks, and lessons learned became a connected knowledge base; and SPAR with Operational Memory made previous troubleshooting experience directly recallable in future tasks.

It did not remain a documentation-only idea. After internal demonstrations, the tool was recommended across several teams, adopted in real workflows, and received positive feedback from users.

In practice, it has helped:

- turn recurring operational tasks into reusable, consistent skill workflows;
- reduce repeated knowledge lookup and unnecessary context loading;
- carry lessons from past incidents into future troubleshooting;
- make team practices easier to share, reuse, and improve over time.

This repository extracts the reusable architecture and patterns; it does not contain internal business data or environment-specific configuration.

This project solves that with three architectural innovations:

### 1. Funnel Read — Load Only What You Need

The agent doesn't read the whole knowledge base. It filters first (cheap), then drills into matches (only if needed).

```
JSON index (50 tokens) → matched entry (80 tokens) → service doc section (150 tokens)
         ↓ filter                ↓ if needed                   ↓ if needed
   95% eliminated          direct answer found          full context loaded
```

**Result:** 130-280 tokens typical load vs 2000+ for naive approaches.

### 2. Two-Way Links — Navigate in Any Direction

Every relationship is stored on **both endpoints**. No matter where the agent is in the graph, it can find all related nodes directly — no file scanning needed.

```
Incident → "Created OM: om-xxx"        (forward: what was learned)
OM → "evidence.incidents: [...]"        (backward: why this exists)
Service A → "calls Service B"           (forward: dependency)
Service B → "called by Service A"       (backward: dependent)
```

### 3. Time Flows Both Ways — Past Informs Future

Operational Memory (OM) acts as a **temporal bridge**: it points backward to the event that taught the lesson, and forward to the future tasks that should apply it.

```
PAST                          PRESENT                        FUTURE
[Incident: what happened] → [OM: the lesson] → [Next task: recall & apply]
```

Knowledge has a lifecycle: born (incident) → distilled (OM) → verified → battle-tested → graduated to runbook — or deprecated if proven wrong.

→ [Full Knowledge Graph Design](docs/knowledge-graph-design.md)

---

## How It Works

### The SPAR Cognitive Loop

Every task follows four phases — Sense, Plan, Act, Reflect:

```
Session 1: S → P(empty)      → A         → R(create OM-001)
Session 2: S → P(recall OM)  → A(faster) → R(update OM-001)
Session 3: S → P(recall OM)  → A(optimal) → R(nothing new)
```

The key insight: **Plan** recalls past lessons (prevents repeating mistakes), and **Reflect** captures new ones (feeds future Plan phases). This creates a compounding feedback loop — the agent gets better with every task.

→ [Full SPAR Framework](docs/spar-framework.md)

### Operational Memory

The structured output of the Reflect phase. Each OM entry contains:

- **Trigger conditions** — when to recall this lesson (task type + service + symptoms)
- **`better_action`** — what to do next time (imperative, actionable)
- **Confidence scoring** — low → medium → high (tracks reliability)
- **Hit counting** — how often recalled and effective
- **Lifecycle** — active → deprecated / superseded / graduated

→ [Full Operational Memory Spec](docs/operational-memory-spec.md)

---

## Design Principles

Seven principles guide every skill in this system:

| # | Principle | Summary |
|---|-----------|---------|
| 1 | **Skills are agent manuals, not human docs** | Explicit triggers, typed parameters, numbered steps, templated output |
| 2 | **Parallelism first** | Independent steps are explicitly marked as parallelizable |
| 3 | **Errors are first-class citizens** | Every skill includes an error → resolution table |
| 4 | **State-aware: incremental > full** | State files track progress; only process deltas |
| 5 | **Temporal knowledge management** | Everything timestamped, lifecycle-managed, staleness-detected |
| 6 | **Token-efficient architecture** | JSON indexes, layered reads, priority-based queries |
| 7 | **Layered processing (SPAR)** | Sense → Plan → Act → Reflect compounds wisdom over time |

→ [Design Philosophy in depth](docs/design-philosophy.md) · [Token Efficiency Strategies](docs/token-efficiency.md)

---

## What's Inside

### Repository Structure

```
agent-skill-patterns/
├── docs/                          # Design documentation
│   ├── design-philosophy.md       # 7 principles in depth
│   ├── spar-framework.md          # The SPAR cognitive loop
│   ├── operational-memory-spec.md # How agents learn from experience
│   ├── knowledge-base-architecture.md  # Multi-layer knowledge design
│   ├── knowledge-graph-design.md  # Token efficiency + cross-ref + temporal design
│   ├── token-efficiency.md        # 6 token-saving strategies
│   └── zh/                        # Chinese documentation (完整中文版)
│
├── templates/                     # 6 skill pattern templates
│   ├── 01-cli-wrapper/            # Wrap CLI tools with domain knowledge
│   ├── 02-doc-maintainer/         # Auto-sync code → documentation
│   ├── 03-cross-validator/        # Cross-reference consistency checks
│   ├── 04-workflow-engine/        # State-machine driven workflows + SPAR
│   ├── 05-data-reporter/          # Query → compute → visualize
│   └── 06-code-health/              # Repository-level, adversarial code review
│
├── knowledge-base/                # Ready-to-use scaffold
│   ├── services/                  # Service documentation (auto-generated)
│   ├── incidents/                 # Event records (per-incident)
│   ├── memory/operational/        # Operational Memory (SPAR output)
│   └── runbooks/                  # Procedural knowledge
│
└── examples/
    └── ops-troubleshooter/        # Complete working example
```

### Skill Templates

| Template | What it does | Key feature |
|----------|-------------|-------------|
| **01 CLI Wrapper** | Wraps CLI tools with natural language interface | Priority-based query strategy |
| **02 Doc Maintainer** | Auto-syncs code changes → knowledge base docs | Incremental scanning with state file |
| **03 Cross Validator** | Checks consistency across multiple documents | Bidirectional dependency verification |
| **04 Workflow Engine** | State-machine driven operational workflows | Full SPAR integration + task routing |
| **05 Data Reporter** | Parallel queries → delta computation → visualization | Today vs yesterday with change rates |
| **06 Code Health Review** | Repository-level review across functionality, architecture, resources, reliability, and security | Independent maintainer/adversarial passes with bounded evidence-based debate |

Template 06 includes the English runtime manual in [SKILL.md](templates/06-code-health/SKILL.md) and a Chinese companion in [SKILL.zh-CN.md](templates/06-code-health/SKILL.zh-CN.md).

### Knowledge Base Architecture

Four layers with increasing detail and decreasing update frequency:

```
Layer 1: Services     — auto-generated from code (weekly)
Layer 2: Runbooks     — manually authored procedures (as needed)
Layer 3: Incidents    — event records (per-event)
Layer 4: OM           — lessons learned with lifecycle (per-task)
```

→ [Knowledge Base Architecture](docs/knowledge-base-architecture.md)

---

## Meta-Patterns

Recurring strategies observed across operational memories:

> **Do the cheapest deterministic verification first; push expensive global searches to the end.**

> **An API returning empty does not mean data doesn't exist — try a different query dimension.**

---

## Who Is This For

- **AI/Agent developers** building knowledge systems for agents
- **DevOps/SRE teams** wanting AI-assisted operations
- **Knowledge workers** designing personal AI workflows
- **Cursor/Claude/Codex users** optimizing their skill configurations

## Compatibility

These patterns are platform-agnostic. They work with:
- Claude Code / Cursor (SKILL.md format)
- OpenAI Codex CLI
- Any LLM agent that can read markdown instructions

## Glossary

| Term | Meaning |
|------|---------|
| **Token** | Unit of text an LLM processes. More consumed = less room for reasoning |
| **Context window** | Total text an LLM can see at once — like a desk with limited surface area |
| **Skill** | Structured markdown file that tells an AI agent how to perform a specific task |
| **OM (Operational Memory)** | A "lesson learned" entry with trigger conditions, better action, and lifecycle |
| **SPAR** | Sense → Plan → Act → Reflect. Cognitive loop for learning agents |
| **Funnel Read** | Filter with cheap index first, read full content only for matches |
| **Two-Way Links** | Relationships stored on both endpoints for bidirectional navigation |
| **Temporal Bridge** | OM points backward (evidence) and forward (trigger) simultaneously |
| **Graduated** | OM promoted to permanent runbook after proving reliability |
| **Confidence** | OM reliability: low (new) → medium (verified) → high (battle-tested) |

## License

MIT
