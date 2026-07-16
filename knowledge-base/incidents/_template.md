---
date: <YYYY-MM-DD>
service: <service-name>
severity: <high|medium|low>
status: <investigating|resolved>
tags: [incident]
aliases: ["<date> <brief-description>"]
---

# <date> <service-name> <Brief Description>

## Basic Info

- **Time:** <YYYY-MM-DD HH:mm> - <HH:mm (resolved)>
- **Service:** <service-name>
- **Endpoint:** <affected API path>
- **Affected users:** <scope description>
- **Error:** <error message>

## Symptoms

<What users/monitors observed>

## Timeline

| Time | Event |
|------|-------|
| HH:mm | Issue discovered |
| HH:mm | Investigation started |
| HH:mm | Root cause identified |
| HH:mm | Fix applied |
| HH:mm | Confirmed resolved |

## Root Cause

<Technical explanation of why this happened>

## Fix

1. **Immediate:** <what was done to stop the bleeding>
2. **Permanent:** <what was done to prevent recurrence>

## Lessons & Improvements

<Post-mortem insights, action items>

→ Created OM: <om-id> (if applicable)

## Relations

**Service:** [<service-name>](../services/<service-name>.md)
