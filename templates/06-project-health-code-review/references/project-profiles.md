# Generic project profiles

Use these profiles only to choose review lenses and safe checks. Repository-local instructions always win. Do not run production commands automatically.

## Async Python service

Focus on API routes, service/repository boundaries, database sessions, migrations, Redis/Celery or other queues, streaming behavior, multi-instance state, permissions, and data mutations. Prefer targeted tests and the repository's configured formatter, linter, type checker, and test markers.

## TypeScript web monorepo

Focus on package dependency direction, server/client boundaries, SSR/ISR/cache behavior, state and rerendering, browser memory, internationalization, secrets, and generated artifacts. Exclude build output, minified files, and generated directories from meaningful source analysis. Run package-scoped typecheck, lint, and contract checks.

## SSE or agent service

Focus on stream lifecycle, async cancellation, Redis state, retries/timeouts, HTTP client reuse, tool or MCP contracts, telemetry, and cross-package models. Use unit/integration tests and existing coverage or stress scripts when justified.

## Distributed worker pipeline

Focus on API/worker/queue protocol, task idempotency, progress terminal states, retry and timeout behavior, independently scaled processes, result consistency, and safe local/test-environment verification. Never automatically run production verification or real external side effects.

## Go service

Focus on controller/service/repository boundaries, worker lifecycle, dynamic configuration, database/Redis transactions, RPC/HTTP contracts, goroutine/resource cleanup, and deployment changes. Treat missing test or lint gates as a review finding when executable code changes.

## Shared library

Treat changes as high blast radius. Focus on public contracts, error codes, tracing/logging, encryption, workflow/session behavior, backward compatibility, and downstream callers. Run configured lint and tests and perform an impact scan before approval.

## Security-sensitive platform

Focus on credentials, ACLs, sandbox isolation, egress, persistence, audit logs, plugin contracts, worker lifecycle, secret handling, and tenant boundaries. Existing deterministic CI is the source of truth; use AI review as a second opinion, never as the sole approval for high-risk changes.
