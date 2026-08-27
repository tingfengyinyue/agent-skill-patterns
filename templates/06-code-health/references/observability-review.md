# Observability Change Review

Apply this reference when a change adds or modifies logs, metrics, traces, stream events, model-output diagnostics, or correlation fields. Observability code is production behavior: it can be wrong, expensive, or misleading even when the business path still succeeds.

## Event contract

- Define one canonical request/run/task correlation ID at the entry point and propagate the same value through producers, consumers, SSE/HTTP conversion, and acknowledgement.
- Verify event identity fields (`event_id`, `redis_id`, sequence, chunk index) and lifecycle fields (created, published, delivered, converted, yielded, acknowledged) are consistent and queryable.
- Compare logger/helper signatures with every call site. Prefer keyword arguments for fields whose positional order could be confused.
- Ensure a field name describes its actual value: raw-byte hash, normalized-text fingerprint, first-chunk metadata, and full-response metadata must not be conflated.

## Streaming and duplicate diagnosis

- Aggregate model or stream metadata across all chunks before emitting a response-level record; do not return after the first text-bearing part unless the event is explicitly first-chunk metadata.
- Test duplicate detection against the real symptom shape: repeated characters, punctuation-separated repetition, repeated n-grams, periodic chunks, and duplicated event IDs are different signals.
- If sample content is needed for diagnosis, use a bounded, redacted sample with an explicit size limit. A hash alone cannot explain the shape of a repetition.
- Keep source-stage markers distinct so operators can separate extraction, model generation, queue publication, delivery, SSE conversion, and frontend replay.

## Production cost and safety

- Count full-content serialization, concatenation, hashing, and copying across every layer. Check large pages/documents and high-concurrency behavior.
- Prefer incremental hashing and bounded summaries. Put detailed event logs behind sampling, a debug flag, or an error-only path; keep normal INFO records aggregated.
- Avoid logging raw prompts, documents, credentials, or sensitive user content. Check field cardinality and whether the logging backend will ingest every stream event.

## Minimum validation matrix

For a meaningful observability change, look for targeted coverage of:

- logger argument/field mapping;
- canonical ID propagation when the client omits an ID;
- multi-chunk model or stream aggregation;
- repeated n-gram or periodic-pattern detection;
- binary versus text fingerprint semantics;
- publish → deliver → convert → yield → ACK correlation;
- bounded logging cost for a large payload.
