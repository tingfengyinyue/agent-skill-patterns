# 操作记忆规范

操作记忆（Operational Memory, OM）是 SPAR 反思阶段的结构化输出：从执行中学到的教训，存储供未来召回。

**不是** runbook（预先存在的程序性知识）、事件报告（事件事实记录）或审计日志（操作记录）。

**一句话定义：** 留给未来自己的执行优化笔记。

---

## 存储结构

```
knowledge-base/memory/operational/
├── index.md                              # 主索引（含 JSON 召回块）
└── om-YYYY-MM-DD-NNN-<slug>.md           # 单条记忆文件
```

---

## 数据格式

每条操作记忆使用以下 frontmatter 结构：

```yaml
---
id: om-YYYY-MM-DD-NNN
created_at: 2026-07-15T16:30:00+08:00
updated_at: 2026-07-15T16:30:00+08:00
title: "一句话总结教训"
trigger:
  task_type: [incident]              # incident | batch | query | config | audit
  services: [payment-service]        # 适用的服务
  symptoms: [timeout, 500]           # 应触发召回的关键词
  tags: [database, row-lock]         # 自由标签
context_before: |
  之前发生了什么（走的弯路或错误）
better_action: |
  下次应该怎么做（改进后的策略）
evidence:
  incidents: [2026-07-15-payment-timeout]
  what_went_wrong: "弯路的描述"
confidence: low                      # low → medium → high
hits: 0                              # 被召回且有效的次数
last_verified_at: 2026-07-15
status: active                       # active | deprecated | superseded
supersedes: []                       # 被本条替代的记忆 ID
---
```

---

## 字段语义

### confidence（可信度）

追踪这条记忆有多可靠：

| 级别 | 含义 | 晋升条件 |
|------|------|---------|
| `low` | 新的、未验证的教训 | 新创建时的默认值 |
| `medium` | 验证过一次，按预期生效 | hits ≥ 2 且无失败 |
| `high` | 久经考验，持续有效 | hits ≥ 5 且跨越 1 个月以上 |

### hits（命中次数）

在以下情况下递增：
1. 该记忆在 Plan 阶段被召回
2. `better_action` 被应用
3. 结果是正面的（在 Reflect 中确认）

如果召回了但没有帮助 → **不要**递增；而是在反思中记录。

### status（状态）

| 状态 | 含义 | 触发条件 |
|------|------|---------|
| `active` | 可被召回 | 默认状态 |
| `deprecated` | 不再可靠 | 连续应用 2 次导致更差结果 |
| `superseded` | 被更好的记忆替代 | 新记忆创建时指定 `supersedes: [本条ID]` |

---

## 索引文件

索引服务于两个目的：
1. **JSON 块** —— 供程序化快速过滤（便宜，~50 tokens）
2. **Markdown 表格** —— 供人类审查和维护

### JSON 快速召回块

```json
[
  {
    "id": "om-2026-07-15-001",
    "task_type": ["incident"],
    "services": ["payment-service"],
    "symptoms": ["timeout", "500", "slow"],
    "tags": ["database", "row-lock"],
    "confidence": "medium",
    "hits": 3,
    "status": "active"
  }
]
```

### 多维度索引（Markdown）

索引文件还按以下维度维护分类：
- **task_type** —— 所有事件类记忆、所有查询类记忆等
- **service** —— 所有涉及 payment-service 的记忆
- **tag** —— 所有标记为 "database" 的记忆

这些是给人看的；agent 用 JSON 块。

---

## 召回流程（Plan 阶段）

每个任务的 Plan 阶段都以记忆召回开始：

```
1. 读取 index.md 的 JSON 块（便宜: ~50 tokens）
2. 按 task_type 且 service 过滤
3. 可选：按 symptoms/tags 进一步精确过滤
4. 对命中的候选项：读取完整条目的 better_action 字段
5. 决定：应用、跳过、或部分适配
6. 记录哪些记忆被应用了
```

**召回优先级：**
- 精确匹配 service + 精确匹配 symptom → 立即读取
- 同 service，不同 symptom → 如果结果不多就扫一眼
- 不同 service，同 symptom → 如果没有直接匹配时再考虑

---

## 创建流程（Reflect 阶段）

### 四个问题

任务完成后，问自己：

1. **走了弯路吗？** → 写入 `context_before`（走错的路径）
2. **比上次更快了吗？** → 如果否，写下什么拖慢了你
3. **遇到意外陷阱了吗？** → 写入 `what_went_wrong`
4. **能提炼"下次做 X"的规则吗？** → 写入 `better_action`

**如果任何一个答案是"是" → 创建一条记忆。**

### 编写 better_action

`better_action` 是最重要的字段。指导原则：

- 用**祈使句**写（"先检查 X"而不是"我应该检查 X"）
- 包含**验证顺序**（先查什么、再查什么、最后查什么）
- 说明**为什么**（让未来的召回能评估是否适用）
- 保持**1-2 步可操作**（不是完整的 runbook）

**好的写法：**
```yaml
better_action: |
  支付超时在 14:xx → 先检查批量导入 cron 是否在运行
  (它 14:30 启动，会对 orders 表加表级锁)。
  如果 cron 在运行: 等它完成或 kill 掉。
  如果 cron 没在运行: 按标准超时诊断流程走。
```

**差的写法：**
```yaml
better_action: |
  可能有批量任务在跑。检查各种东西。
```

---

## 生命周期管理

### 维护规则

| 事件 | 动作 |
|------|------|
| 记忆被召回且有效 | `hits += 1`，更新 `last_verified_at` |
| 记忆被召回但无效 | 不递增；在反思中记录 |
| 记忆连续无效 2 次 | `status: deprecated` |
| 新记忆覆盖了相同场景 | `supersedes: [旧ID]`，旧的 → `superseded` |
| 记忆 6 个月未被召回 | 在索引中标记为 `stale`（过期） |
| `confidence: high` + `hits ≥ 10` + 稳定 3 个月 | 晋升为 runbook |

### 晋升为 Runbook

当一条记忆达到高可信度且持续有命中时，它已经证明了自己是可靠的程序性知识。此时，将其提取为正式的 runbook，并将原记忆标记为 superseded。

---

## 元模式（Meta-Patterns）

当积累了多条记忆后，寻找跨越单条记忆的重复策略。将这些记录为**元模式**放在索引顶部。

**已观察到的元模式：**

> **先做最便宜的确定性验证；把昂贵的全局搜索推到最后。**

跨记忆的应用示例：
- om-001: trace_id（便宜）→ 行锁检查（便宜）→ 广泛日志搜索（昂贵）
- om-002: 单条 SQL 匹配（便宜）→ 登录记录（中等）→ 网关追踪（昂贵）

> **API 返回空 ≠ 数据不存在。换个维度查询试试。**

示例：
- om-003: SearchDatabase 返回空 → ListInstances + ListDatabases 找到了
- om-004: 服务专属 logstore 为空 → 实际用的是共享 logstore

---

## 完整条目示例

```markdown
---
id: om-2026-07-15-001
created_at: 2026-07-15T14:45:00+08:00
title: "支付超时在 14:xx → 先检查批量任务的时间冲突"
trigger:
  task_type: [incident]
  services: [payment-service]
  symptoms: [timeout, slow, order creation]
  tags: [database, cron, batch, schedule]
context_before: |
  花了 5 分钟广泛搜索日志查找超时原因。
  最后发现是批量导入任务在持有表锁。
  如果先查 cron 状态，30 秒就能定位。
better_action: |
  支付超时在 14:00-15:00 之间 → 先检查批量导入
  cron 是否在运行（14:30 启动，锁 orders 表约 5 分钟）。
  快速检查: 查询 cron 执行日志，看今天 14:30 的执行记录。
  如果在运行: 这就是原因。等完成或 kill。
  如果没在运行: 按标准超时诊断流程走。
evidence:
  incidents: [2026-07-15-payment-timeout-uid12345]
  what_went_wrong: "直接做了广泛日志搜索，而不是先检查已知的时间冲突"
confidence: low
hits: 0
last_verified_at: 2026-07-15
status: active
supersedes: []
---

# om-2026-07-15-001: 支付超时 → 先查批量任务时间表

## 教训

payment-service 在 14:00-15:00 之间的超时有很大概率
是由每日批量导入 cron 任务引起的（14:30 启动，对 orders 表
持有表级锁约 5 分钟）。

## 决策树

1. 是 14:00-15:00 之间吗？→ 先查 cron 状态
2. Cron 在运行 + 持有锁？→ 这就是原因。等完成或 kill。
3. Cron 没在运行？→ 标准超时诊断（行锁、连接池等）

## 为什么重要

批量任务是最便宜的检查项（一条查询查 cron 日志），并且
能解释这个时间窗口内约 40% 的支付超时。先查它可以节省
5 分钟以上的广泛日志分析时间。
```
