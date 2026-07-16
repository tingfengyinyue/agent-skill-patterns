---
type: service
tags: [service]
aliases: ["<service-name>"]
repo: "<git-repo-url>"
module: "<module-path>"
database: "<database-name>"
last_scan: "<YYYY-MM-DD>"
---

# <service-name>

## Overview

Brief description of what this service does, its role in the system, and key responsibilities.

## Tech Stack

- **Language:** Go 1.22 / Python 3.12 / Node 20 / etc.
- **Framework:** Gin / FastAPI / Express / etc.
- **Database:** MySQL 8.0 / PostgreSQL 15 / etc.
- **Cache:** Redis 7.x
- **Message Queue:** RabbitMQ / Kafka / etc.

## API Endpoints

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| POST | /api/example/create | CreateExample | Create a new resource |
| GET | /api/example/:id | GetExample | Get resource by ID |
| PUT | /api/example/:id | UpdateExample | Update resource |
| DELETE | /api/example/:id | DeleteExample | Soft-delete resource |

## Data Models

### example_table

| Field | Type | Description |
|-------|------|-------------|
| id | bigint | Primary key |
| name | varchar(255) | Resource name |
| status | tinyint | -1=deleted, 0=inactive, 1=active |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

## Service Dependencies

### Downstream (this service calls)

| Target Service | Endpoint | Purpose |
|---------------|----------|---------|
| auth-service | GET /api/user/validate | Validate user token |
| notification-service | POST /api/notify | Send notifications |

### Upstream (calls this service)

| Source Service | Endpoint | Purpose |
|---------------|----------|---------|
| gateway | POST /api/example/create | Proxied from frontend |
| admin-service | GET /api/example/:id | Admin queries |

## Message Queue

### Producer

| Topic | Trigger | Payload |
|-------|---------|---------|
| example.created | After successful creation | `{id, name, created_at}` |

### Consumer

| Topic | Handler | Processing |
|-------|---------|-----------|
| payment.completed | OnPaymentDone | Update order status |

## Scheduled Tasks

| Schedule | Task Name | Description |
|----------|-----------|-------------|
| 0 3 * * * | CleanupExpired | Remove expired records |
| */5 * * * * | SyncStatus | Sync status with upstream |

## Key Business Logic

Brief description of the core domain logic, key flows, and important invariants.

---

## Related Operational Memory

<!-- Auto-populated: memories that reference this service -->

## Related Incidents

<!-- Auto-populated: incidents involving this service -->
