# Project-health review lenses

Apply these as questions tied to evidence, not as a checklist that must produce findings.

## Functionality and specification

- Does the implementation satisfy every explicit requirement and acceptance criterion?
- Are success, invalid input, empty result, timeout, retry, cancellation, duplicate request, and partial failure paths defined?
- Does the code change behavior outside the requested scope?
- Do API status codes, error shapes, event names, schemas, and compatibility promises remain correct?

## Cleanliness and maintainability

- Is responsibility located in the correct module?
- Is there duplicated logic, speculative abstraction, primitive obsession, hidden coupling, or shotgun surgery?
- Are names, interfaces, and control flow understandable without reconstructing hidden state?
- Are comments explaining why rather than repeating what the code does?
- Is the change smaller or more complicated than the problem requires?

## Code-writing quality and Code Rot

Review code quality as a time-based property. A change can be locally correct while still adding another layer to a repository that is already difficult to maintain.

Check:

- complexity accumulation: long functions, deep nesting, repeated conditionals, large files, and too many parameters;
- duplication and parallel implementations: similar logic that will drift, duplicate adapters, repeated validation, and copy-pasted fixes;
- dead or obsolete paths: unused functions/classes/routes, stale feature flags, commented-out code, TODO/FIXME/HACK markers, deprecated compatibility layers, and unreachable branches;
- hotspot risk: high-churn files/functions, recent edits concentrated in already complex modules, and changes that expand a maintenance hotspot;
- architecture drift: new dependency direction violations, bypassed abstractions, cross-domain imports, and documentation/ADR mismatch;
- test decay: changed behavior without meaningful tests, skipped or flaky tests, tests that assert implementation details, and critical paths with no owner;
- dependency/config drift: stale packages, duplicate libraries, inconsistent configuration, and runtime behavior no longer matching documentation.

Do not call a file “rotten” from one smell. Require at least two independent indicators or one strong indicator plus a concrete maintenance consequence. Distinguish pre-existing rot from rot introduced or worsened by the change. Report a pre-existing issue as blocking only when the change relies on or expands it.

## Architecture and global flow

- Does dependency direction respect the repository's declared layers?
- What are the changed symbols' callers, callees, implementers, and shared consumers?
- Does a shared utility or contract change have downstream impact that the diff does not show?
- Does a migration/config/deployment change have a safe ordering and rollback path?
- Are domain, transport, persistence, and orchestration concerns leaking across boundaries?

## Memory and resource lifecycle

Look for evidence of unbounded or duplicated resource ownership:

- unbounded lists, maps, caches, queues, Redis Streams, event buffers, or retained conversation/tool history;
- materializing large files, database results, HTTP bodies, or model outputs instead of streaming or paging;
- repeated serialization/deserialization or copying across layers;
- database sessions, Redis/HTTP clients, files, subprocesses, browser pages/contexts, goroutines, asyncio tasks, and cancellation tokens without a clear release path;
- retry loops that multiply queued work or retain failed payloads;
- per-request resources stored in global state;
- missing limits, TTLs, backpressure, pagination, batch size, timeout, or maximum payload size.

Classify the result:

- confirmed: a test/profile or clear boundedness proof demonstrates the issue;
- high: the code path clearly grows or leaks under a realistic input;
- needs-runtime-verification: a plausible risk that depends on payload size, traffic, framework behavior, or deployment configuration.

## Performance and data access

- Are loops, joins, filters, serialization, and network calls proportional to input size?
- Is there N+1 database/API access, repeated remote calls, unnecessary model/tool calls, or blocking IO in an async path?
- Are indexes, connection pools, batch sizes, cache keys, TTLs, and concurrency limits appropriate?
- Does the change add latency to a hot path identified by the call graph?

## Reliability and concurrency

- Are timeouts, retries, backoff, idempotency keys, deduplication, and dead-letter behavior coherent?
- Can concurrent workers race on state, publish duplicate events, or lose progress?
- Does cancellation propagate through every child task and external operation?
- Are partial failures observable and recoverable?

## Security and data boundaries

- Is untrusted input validated before SQL, shell, browser, prompt, filesystem, or network use?
- Are authentication, authorization, tenant isolation, secrets, credentials, and audit events preserved?
- Does a tool, agent, sandbox, or browser action cross an intended boundary?
- Could logs, traces, caches, prompts, or exceptions expose sensitive data?

## Observability and operations

- Can an operator distinguish success, retry, timeout, cancellation, partial completion, and permanent failure?
- Are metrics/logs/traces attached to the right request, task, tenant, and correlation ID?
- Are health checks, alerts, rollout order, feature flags, rollback, and migration compatibility addressed?

## Tests and validation quality

- Do tests exercise business behavior rather than framework behavior?
- Is the most dangerous path covered: permissions, data mutation, retry, concurrency, resource limit, or external contract?
- Are tests isolated, deterministic, and asserting meaningful outcomes?
- Does the test prove the reported bug could not recur, or merely execute the new lines?
- What must be profiled or manually verified because a unit test cannot establish it?
