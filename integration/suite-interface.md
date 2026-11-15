# skill-criticagent ↔ 证据评审套件：整合接口

本文件把 `skill-criticagent` 定义为证据评审套件的**第八名成员**：skill 领域的行为与安装决策专家。本文件是接口契约，不复制 criticagent 的方法正文。

## 定位

| 成员 | 负责 | 不负责 |
|---|---|---|
| 七项评审 skill | 概念、实质、证据链、等效性、学术、来源、缺点、改进、门禁 | skill 的**行为增量和触发准确率** |
| skill-criticagent | skill 的合规/安全、**with/without 行为对比**、触发测试、安装裁决 | 科研方向、文献、规划、多维学术评审 |

七项缺的正是行为维度；criticagent 缺的是统一报告与多维门禁。二者互补，不重叠。

## 何时调用

评审对象是 Agent Skill（目录含 SKILL.md）、skill 集合，且需要回答"是否真的有用/能否安装"时，由 `project-review-orchestrator` 派发到 criticagent。

对象是非 skill 的代码、论文、理论、计划时**不调用**，走七项各自路径。

## 输出映射（criticagent → report.schema.json v3.2）

criticagent 的裁决必须写入统一报告的 `behavior_evidence`：

| criticagent 证据 | v3.2 字段 |
|---|---|
| 带上 skill 通过数 | `with_skill_pass` |
| 不带 skill 通过数（隔离基线） | `without_skill_pass` |
| 用例总数 | `cases_total` |
| 触发正确数 / 总查询数 | `trigger_correct` / `trigger_total` |
| 源输入与 SKILL.md 前后 hash 未变 | `source_hashes_stable` |
| 基线用 fresh subagent 未污染 | `baseline_isolated` |
| 运行产物、transcript、grader JSON 路径 | `execution_evidence` |
| 建议安装 / 先修复 / 不建议安装 | `install` / `fix-first` / `reject` |
| 不适用（对象非 skill） | `not_applicable` + `verdict_reason` |

## 门禁耦合（已由 validator 强制）

- `install` 要求：`execution_evidence` 非空、`source_hashes_stable=true`、`baseline_isolated=true`、`with_skill_pass > without_skill_pass`。四者任一不满足即校验失败。
- `reject` 要求报告 gate 为 `REJECT` 或 `INCOMPLETE`。
- `fix-first` 禁止 gate `ACCEPT`。
- `not_applicable` 必须给 `verdict_reason`。

**"答案里写了文件路径"不算证据** —— 这正是 `execution_evidence` 必填的原因。

## 执行机制（委托，不重写）

- 合规/安全：`vendor/mcp_criticagent/src/core/` 下的确定性 kernel，有 SHA-256 manifest 保护。
- 行为评分：`scripts/grade_runs.py`
- 触发评分：`scripts/grade_triggers.py`
- 宿主工具断言适配：`scripts/adapt_host_tool_assertions.py`
- 用例：`evals/evals.json`、`evals/trigger_queries.json`

本套件不复制上述脚本；只消费其输出。

## 边界

1. criticagent 的触发决策是自报的，可能不同于真实在任务中的激活——报告须保留此限制。
2. provider/权限/超时/传输失败是**执行失败**，不得计为 skill 质量失败；对应本套 `ENVIRONMENT_BLOCKED`。
3. 行为通过不证明科研正确性、理论成立或创新性；这些仍归七项的专项审查。
4. 三层证据不可互相替代：**静态合规**、**行为增量**、**领域学术判断**。
