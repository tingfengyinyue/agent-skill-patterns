# Skill Patterns

[中文版文档 / Chinese Documentation](docs/zh/README.md)

A collection of production-tested patterns for building AI agent knowledge systems.

These patterns are extracted from a real-world operations platform where AI agents handle incident response, service monitoring, data reporting, and cross-service validation — running in production daily.

## Design Philosophy

Seven principles guide the design of every skill in this collection:

| # | Principle | Summary |
|---|-----------|---------|
| 1 | **Skills are agent manuals, not human docs** | Every skill has explicit triggers, parameters, numbered steps, and machine-parseable structure |
| 2 | **Parallelism first** | Steps that can run concurrently are explicitly marked |
| 3 | **Errors are first-class citizens** | Every skill includes an error handling table |
| 4 | **State-aware: incremental > full** | State files track what changed; only process deltas |
| 5 | **Temporal knowledge management** | All knowledge is timestamped, ordered, and lifecycle-managed |
| 6 | **Token-efficient architecture** | JSON indexes for programmatic recall; read cheap summaries before expensive full pages |
| 7 | **Layered processing (SPAR)** | Sense → Plan → Act → Reflect — a cognitive loop that compounds wisdom |

→ [Full design philosophy documentation](docs/design-philosophy.md)

## Repository Structure

```
skill-patterns/
├── docs/                          # Design documentation
│   ├── design-philosophy.md       # 7 principles in depth
│   ├── spar-framework.md          # The SPAR cognitive loop
│   ├── operational-memory-spec.md # How agents learn from experience
│   ├── knowledge-base-architecture.md  # Multi-layer knowledge design
│   ├── knowledge-graph-design.md  # ⭐ Token efficiency + cross-ref + temporal design
│   └── token-efficiency.md        # Token-saving strategies
│
├── templates/                     # 5 skill pattern templates
│   ├── 01-cli-wrapper/            # Wrap CLI tools with domain knowledge
│   ├── 02-doc-maintainer/         # Auto-sync code → documentation
│   ├── 03-cross-validator/        # Cross-reference validation
│   ├── 04-workflow-engine/        # State-machine driven workflows
│   └── 05-data-reporter/          # Query → compute → visualize
│
├── knowledge-base/                # Knowledge base scaffold
│   ├── services/                  # Service documentation
│   ├── incidents/                 # Event records
│   ├── memory/operational/        # Operational Memory (lessons learned)
│   └── runbooks/                  # Procedural knowledge
│
└── examples/                      # Complete runnable example
    └── ops-troubleshooter/        # Full incident response skill
```

## Skill Pattern Templates

### 01 - CLI Wrapper

Wraps a CLI tool (cloud provider CLI, database client, log query tool) with:
- Natural language interface
- Environment-aware configuration mapping
- Priority-based query strategies
- Formatted output with next-step suggestions

### 02 - Doc Maintainer

Keeps knowledge base documentation in sync with source code:
- Incremental scanning (only process repos with new commits)
- Diff-path → doc-section mapping
- State file tracks last scanned commit per service

### 03 - Cross Validator

Reads multiple documents and cross-references them for consistency:
- Endpoint existence validation
- Bidirectional dependency verification
- Orphan detection (producers without consumers)

### 04 - Workflow Engine

State-machine driven operational workflows:
- SPAR cognitive loop (Sense → Plan → Act → Reflect)
- Task classification and routing
- Operational Memory recall and creation
- Structured output formats

### 05 - Data Reporter

Automated data collection, comparison, and visualization:
- Parallel query execution (today vs yesterday)
- Delta computation with change rates
- Canvas/visualization integration

## Core Innovation: Knowledge Graph for Agents

The most distinctive feature of this architecture — a knowledge base designed as a **navigable graph** with three key properties:

### 1. Funnel Read — Load Only What You Need

> The agent doesn't read the whole knowledge base. It filters first (cheap), then drills into matches (only if needed).

```
JSON index (50 tokens) → matched OM entry (80 tokens) → service doc section (150 tokens)
         ↓ filter                  ↓ if needed                    ↓ if needed
   95% eliminated            direct answer found           full context loaded
```

Typical knowledge loading: **130-280 tokens** vs 2000+ for naive approaches. The index acts as a table of contents — the agent reads it to decide what to open, not to open everything.

### 2. Two-Way Links — Navigate in Any Direction

> Every relationship is stored on **both endpoints**. No matter where the agent is in the graph, it can find all related nodes directly — no file scanning needed.

```
Incident → "Created OM: om-xxx"        (forward: what was learned)
OM → "evidence.incidents: [...]"        (backward: why this exists)
Service A → "calls Service B"           (forward: dependency)
Service B → "called by Service A"       (backward: dependent)
```

### 3. Time Flows Both Ways — Past Informs Future

> OM (Operational Memory) acts as a **temporal bridge**: it points backward to the event that taught the lesson, and forward to the future tasks that should apply it.

```
PAST                          PRESENT                        FUTURE
[Incident: what happened] → [OM: the lesson] → [Next task: recall & apply]
    evidence.incidents ──▶       ◀── trigger.symptoms match
```

Knowledge has a lifecycle: born (incident) → distilled (OM, low confidence) → verified (medium) → battle-tested (high) → graduated (runbook) or deprecated.

→ [Full Knowledge Graph Design](docs/knowledge-graph-design.md)

---

## Operational Memory System

Agents that **learn from experience** through the SPAR Reflect phase.

Each task completion asks four questions:
1. Did I take a detour?
2. Was I faster than last time?
3. Any unexpected pitfalls?
4. Can I distill a "next time, do X" rule?

If yes → create an Operational Memory entry with:
- Trigger conditions (task type, service, symptoms)
- What went wrong before (`context_before`)
- What to do better next time (`better_action`)
- Confidence scoring (low → medium → high)
- Hit counting (usage frequency)
- Lifecycle management (active → deprecated → superseded → graduated)

→ [Full Operational Memory specification](docs/operational-memory-spec.md)

## Meta-Patterns

Two recurring strategies observed across all operational memories:

> **Do the cheapest deterministic verification first; push expensive global searches to the end.**

> **An API returning empty does not mean data doesn't exist — try a different dimension.**

## Glossary

| Term | Meaning |
|------|---------|
| **Token** | The unit of text an LLM processes. More tokens consumed = less room for reasoning. Think of it as "desk space" |
| **Context window** | The total amount of text an LLM can see at once — like a desk with limited surface area |
| **Skill** | A structured markdown file that tells an AI agent exactly how to perform a specific task |
| **OM (Operational Memory)** | A "lesson learned" entry — records what went wrong and what to do better next time |
| **SPAR** | Sense → Plan → Act → Reflect. A cognitive loop that makes agents learn from experience |
| **Funnel Read** | Reading strategy: filter with a cheap index first, only read full content for matches |
| **Two-Way Links** | Every relationship stored on both endpoints, so you can navigate in either direction |
| **Temporal Bridge** | OM's unique property: it points backward (evidence) and forward (trigger) simultaneously |
| **Graduated** | When an OM becomes so reliable it gets promoted into a permanent runbook |
| **Deprecated** | When an OM has failed enough times that it's no longer trustworthy |
| **Meta-Pattern** | A strategy that appears across multiple OMs — a "pattern of patterns" |
| **Hit** | One successful recall + application of an OM entry (tracks how useful it is) |
| **Confidence** | Reliability level of an OM: low (new) → medium (verified) → high (battle-tested) |

## Who Is This For

- **AI/Agent developers** building agent knowledge systems
- **DevOps/SRE teams** wanting AI-assisted operations
- **Knowledge workers** designing personal AI workflows
- **Cursor/Claude/Codex users** optimizing their skill configurations

## Compatibility

These patterns are platform-agnostic. They work with:
- Claude Code / Cursor (SKILL.md format)
- OpenAI Codex CLI
- Any LLM agent that can read markdown instructions

## License

MIT
