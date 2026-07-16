# 知识库架构

为 AI Agent 消费而设计的多层知识系统，以最小 token 开销提供最大相关性。

---

## 概述

知识库将运维知识组织为四个不同的层次，每层有不同的更新频率、访问模式和生命周期：

```
knowledge-base/
├── services/              # 第 1 层：服务文档（自动生成）
├── runbooks/              # 第 2 层：程序性知识（人工编写）
├── incidents/             # 第 3 层：事件记录（按事件创建）
├── memory/operational/    # 第 4 层：经验教训（SPAR 反思输出）
└── .service-scan-state.json  # 状态追踪
```

---

## 第 1 层：服务文档

**更新频率：** 每周（由代码变更触发）
**作者：** doc-maintainer skill 自动生成
**目的：** 每个服务的 API、数据模型、依赖关系的权威参考

### 每个服务文件的结构

```markdown
---
type: service
tags: [service]
aliases: ["payment-service"]
repo: "<git-repo-url>"
module: "<module-path>"
database: "<db-name>"
last_scan: "2026-07-15"
---

# payment-service

## 概述
本服务的简要描述。

## 技术栈
语言、框架、关键依赖。

## API 接口
| 方法 | 路径 | Handler | 描述 |
|------|------|---------|------|
| POST | /api/order/create | CreateOrder | 创建订单 |
| GET | /api/order/:id | GetOrder | 按 ID 查询订单 |

## 数据模型
关键数据库表及其字段。

## 服务依赖
### 下游（本服务调用的）
- auth-service: /api/user/validate
- notification-service: /api/notify/send

### 上游（调用本服务的）
- gateway: /api/order/*
- admin-service: /api/order/refund

## 消息队列
| 角色 | Topic | 描述 |
|------|-------|------|
| 生产者 | order.created | 订单创建成功后发出 |
| 消费者 | payment.confirmed | 处理支付确认 |

## 定时任务
| 调度 | 任务 | 描述 |
|------|------|------|
| */5 * * * * | SyncOrderStatus | 同步待处理订单与支付网关 |

---

## 相关操作记忆
（自动关联查询）

## 相关事件
（自动关联查询）
```

### 关键设计决策

- **Frontmatter** 支持程序化查询（按 type、database 等过滤）
- **依赖关系是双向的** —— 同时记录"我调用谁"和"谁调用我"
- **自动生成的章节** 与手动标注明确分离
- **底部的关联章节** 通过查询/链接机制自动填充

---

## 第 2 层：Runbook

**更新频率：** 按需（流程变更时）
**作者：** 人工编写，有时从 OM 晋升而来
**目的：** 常见操作的分步指南

### Runbook 类型

| Runbook | 用途 |
|---------|------|
| `sls_query_guide.md` | 如何查询日志系统 |
| `dms_query_guide.md` | 如何查询数据库 |
| `core_table_schemas.md` | 核心表结构（写 SQL 前先读） |
| `service_dependency_map.md` | 跨服务调用关系 |
| `operational_memory_spec.md` | OM 系统规范 |

### Runbook 模板

```markdown
---
task_type: runbook
keywords: ["日志查询", "SLS", "排查"]
tags: [runbook, logging]
---

# 日志查询指南

## 什么时候用
- 诊断服务错误
- 追踪请求路径
- 分析性能

## 前置条件
- CLI 工具已配置凭证
- 了解服务到日志源的映射

## 快速参考

| 服务 | 日志源 | 环境 |
|------|--------|------|
| payment-service | payment-logs | 生产 |
| auth-service | auth-logs | 生产 |

## 分步操作

### 1. 确定环境
...

### 2. 构建查询
...

## 常见坑

| 坑 | 解决方案 |
|----|----------|
| 时间范围错误 | 始终使用 UTC |
| 服务名不匹配 | 查看上面的映射表 |
```

---

## 第 3 层：事件记录

**更新频率：** 按事件（每次事件发生时创建）
**作者：** workflow-engine skill 生成
**目的：** 发生了什么、什么时候、如何解决的历史记录

### 命名规则

```
incidents/YYYY-MM-DD-<service>-<slug>.md
```

### 事件模板

```markdown
---
date: 2026-07-15
service: payment-service
severity: high
status: resolved
tags: [incident]
---

# 2026-07-15 payment-service 订单超时

## 基本信息
- **时间：** 2026-07-15 14:30 - 14:45
- **服务：** payment-service
- **接口：** POST /api/order/create
- **影响范围：** 15 分钟窗口内约 200 用户
- **错误：** "lock wait timeout exceeded"

## 表现
用户反映创建订单挂起 9 秒以上后失败。

## 时间线
| 时间 | 事件 |
|------|------|
| 14:30 | 批量导入 cron 任务启动 |
| 14:32 | 日志中出现首批超时错误 |
| 14:35 | 告警触发 |
| 14:38 | 定位根因（批量任务的表锁） |
| 14:40 | Kill 批量任务 |
| 14:42 | 服务恢复 |
| 14:45 | 确认全部正常 |

## 根因
每日批量导入任务（14:30 cron）对 orders 表加了表级锁，
阻塞了所有并发 INSERT 操作。

## 修复
1. 即时：Kill 批量任务进程
2. 永久：将批量任务改为行级锁 + 分批插入

## 教训与改进
→ 创建 OM: om-2026-07-15-001 (支付超时先查批量任务时间表)
→ 行动项: 将批量任务移到 03:00 低峰时段

## 关联
**服务：** [payment-service](../services/payment-service.md)
**OM：** [om-2026-07-15-001](../memory/operational/om-2026-07-15-001-batch-schedule-conflict.md)
```

---

## 第 4 层：操作记忆

详见 [操作记忆规范](operational-memory-spec.md)。

**关键要点：** OM 是唯一有**生命周期**的层（可信度评分、命中计数、废弃、晋升）。其他层要么是静态的（runbook）、自动生成的（services）、或只增不减的（incidents）。

---

## 访问模式（Token 节约）

各层被设计为按特定顺序读取，以最小化 token 消耗：

```
查询到达
    │
    ▼
┌─────────────────────────────────┐
│ 1. 读取 OM 索引 JSON 块         │  ~50 tokens
│    (程序化过滤)                  │
└───────────────┬─────────────────┘
                │ 找到相关 OM？
    ┌───────────┼───────────────┐
    │ 是        │               │ 否
    ▼           │               ▼
┌──────────┐    │    ┌─────────────────────┐
│ 读取 OM  │    │    │ 2. 读取服务文档      │  ~300 tokens
│ better_  │    │    │    (相关章节)        │
│ action   │    │    └──────────┬──────────┘
│ ~100 tok │    │               │
└──────────┘    │               ▼
                │    ┌─────────────────────┐
                │    │ 3. 读取 runbook     │  ~200 tokens
                │    │    (如需要)         │
                │    └──────────┬──────────┘
                │               │
                └───────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │ 4. 搜索事件记录      │  仅在需要
              │    (仅必要时)        │  模式匹配时
              └─────────────────────┘
```

**典型读取量：** 150-500 tokens 用于上下文加载，vs 全部读取的 2000+。

---

## 交叉引用

所有层互相引用：

| 来源 | 目标 | 链接类型 |
|------|------|---------|
| 事件 → 服务 | `[payment-service](../services/payment.md)` | 哪个服务受影响 |
| 事件 → OM | `Created OM: om-xxx` | 学到了什么 |
| OM → 事件 | `evidence.incidents: [...]` | 什么事件触发了这条教训 |
| 服务 → OM | "相关操作记忆"章节 | 关于这个服务的教训 |
| OM → Runbook | `better_action` 中引用流程 | "详见 runbook X" |

---

## 状态追踪

`.service-scan-state.json` 文件追踪增量状态：

```json
{
  "last_scan": "2026-07-15T10:30:00+08:00",
  "services": {
    "payment-service": {
      "last_commit_sha": "abc123def456",
      "last_scan": "2026-07-15",
      "sections_updated": ["api_endpoints", "data_models"]
    },
    "auth-service": {
      "last_commit_sha": "789ghi012jkl",
      "last_scan": "2026-07-10",
      "sections_updated": []
    }
  }
}
```

**用途：** doc-maintainer skill 读取此文件判断哪些服务需要重新扫描（只有 `last_commit_sha` 之后有新提交的才需要）。

---

## 维护日历

| 频率 | 动作 | 自动化？ |
|------|------|---------|
| 每次提交 | 服务文档更新（扫描触发时） | 是（doc-maintainer skill） |
| 每次事件 | 事件记录创建 | 是（workflow-engine skill） |
| 每次任务 | OM 创建/更新 | 是（SPAR 反思阶段） |
| 每周 | OM 索引过期检查 | 人工审查 |
| 每月 | Runbook 准确性审查 | 人工 |
| 每季度 | OM 批量晋升审查 | 人工 |
