---
id: om-YYYY-MM-DD-NNN
created_at: YYYY-MM-DDThh:mm:ss+08:00
updated_at: YYYY-MM-DDThh:mm:ss+08:00
title: "One-line summary: <situation> → <what to do>"
trigger:
  task_type: [incident]
  services: [service-name]
  symptoms: [keyword1, keyword2]
  tags: [tag1, tag2]
context_before: |
  What happened before (the mistake or detour taken).
better_action: |
  What to do next time (imperative, actionable, 1-2 steps).
evidence:
  incidents: [YYYY-MM-DD-service-slug]
  what_went_wrong: "Brief description of the detour"
confidence: low
hits: 0
last_verified_at: YYYY-MM-DD
status: active
supersedes: []
---

# om-YYYY-MM-DD-NNN: <Short Title>

## Lesson

<2-3 sentences explaining the core insight.>

## Decision Tree

1. <First thing to check> → if yes, this is likely the cause
2. <If not> → proceed to standard diagnosis
3. <Fallback> → escalate or broaden search

## Why This Matters

<Why checking this first saves time. What percentage of cases does this explain.
What's the cost of NOT checking this first.>
