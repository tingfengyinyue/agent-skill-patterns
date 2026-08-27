# Review Learning Loop

Use this protocol to turn confirmed post-review feedback into safer future checks. The durable memory is private and separate from the skill package.

## Memory boundary

Default store:

    ~/.codex/code-health-memory/

Keep real project paths, internal service names, production evidence, user data, and credentials in this local store only. Never copy the local memory directory into the public skill repository.

The store follows the SN-style pattern:

- `index.md`: small JSON metadata index for retrieval;
- `memories/*.md`: detailed evidence and strategy;
- `audit.log`: local READ/WRITE history;
- `status`: `candidate`, `validated`, `global-rule`, `superseded`, or `invalidated`;
- `supersedes`/`superseded_by`: explicit correction links.

## Before a review

Select at most three relevant memories using repository, service, symptoms, task type, and tags:

    python3 scripts/review_memory.py select \
      --repo <repo-name> \
      --service <service> \
      --symptom <observed-symptom> \
      --tag <change-area>

Treat selected memories as targeted hypotheses and checks, not as facts. Prefer `global-rule` and `validated` entries, but do not suppress contradictory code or test evidence.

## After a missed finding

Only record a lesson when the user or later evidence confirms that the earlier review missed a real issue. Do not write memory merely because a reviewer expressed an uncertain concern.

Create a JSON record with:

- the original review ID and repository context;
- the concrete missed behavior and evidence;
- why the first review missed it;
- a detection rule that another reviewer can execute;
- a regression test or smallest distinguishing verification;
- a negative control showing when the rule should not fire.

Record it as a candidate:

    python3 scripts/review_memory.py record --input /path/to/missed-review.json

The script rejects common credential-like values. Still manually remove sensitive payloads, absolute paths, raw prompts, and customer data before recording.

## Promotion gates

Do not silently edit the core Skill after one incident.

1. `candidate`: observed lesson, not yet trusted.
2. `validated`: confirmed evidence plus a regression test or reproducible check, with explicit human approval.
3. `global-rule`: validated in at least two independent contexts, with explicit human approval; only then consider adding a concise rule to the public Skill.
4. `superseded` or `invalidated`: no longer trusted; preserve the reason and replacement link.

Promotion commands require `--approved-by`; global promotion also requires two `--cross-project` contexts:

    python3 scripts/review_memory.py promote <id> --to validated --approved-by <human>
    python3 scripts/review_memory.py promote <id> --to global-rule \
      --approved-by <human> --cross-project <context-a> --cross-project <context-b>

Use `supersede` when new evidence corrects an older lesson. Retrieval must ignore superseded and invalidated entries.

## Reflection categories

When recording a miss, classify the failure before writing a rule:

- context failure: caller, callee, configuration, or repository rule was not loaded;
- reasoning failure: loaded evidence was not connected across the call path;
- detector failure: a known pattern was not checked, such as argument order or chunk aggregation;
- validation failure: the smallest regression test or runtime check was absent;
- tool failure: graph, search, test, or runtime evidence was stale, unavailable, or misleading;
- scope failure: the issue was outside the requested change and should remain a non-blocking side effect.

The next review report should state which memories influenced its checks and whether any memory was contradicted, confirmed, or unused.
