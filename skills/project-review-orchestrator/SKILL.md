---
name: project-review-orchestrator
description: >-
  多项目证据评审的总控：识别项目与版本、调度专项审查和 GitHub 对比、聚合缺点并给最终门禁；不替专项伪造结论。
---

# 总审查调度 v2

## 输入

项目目录、会话归档、概念文档或用户明确给出的评审对象。多个对象分别建档案，不共享证据。

## 流程

1. 解析路径全名和会话实际交付物；不存在就报告，不猜。
2. 记录 commit/dirty/无 git 快照；先核对 manifest、冻结快照与当前结果。
3. 判定 concept/engineering/experiment/reproduction/theory/mixed，列 claim 和适用检查。
4. 调 concept-substance-reviewer 和 equivalence-scholarship-reviewer；只读任务不改文件。
5. **对象是 Agent Skill 时，派发到 `skill-criticagent`**（套件第八名成员）做合规/安全、with/without 行为对比与触发测试，结果写入 `behavior_evidence`；非 skill 对象跳过此步。
6. 只把真正外部证据缺口交给 github-reproduction-scout。
7. 将候选交 implementation-comparator；INCOMPARABLE 不得强行判等。
8. defect-synthesizer 去重定级；需要修改才调 targeted-remediator。
9. 聚合各维度结论、环境阻塞、未覆盖范围，给总门禁。
10. `behavior_evidence.verdict` 与 gate 必须一致：reject→REJECT/INCOMPLETE；fix-first 禁止 ACCEPT；install 需执行证据、源 hash 稳定、基线隔离且 with>without。

## 禁止

- 无具体项目时评分或编造发现。
- 把历史 PASS 当当前 PASS。
- 把 exit 0 当科学通过，把权限错误当逻辑失败。
- 把相似 GitHub 项目当复现。
- 用单一总分掩盖阻断项。

## 输出

范围与版本→项目实质→证据分层→阻断问题→各专项结论→未验证范围→总门禁。

## 资源

- `references/protocol.md`：公共状态、版本与 GitHub 分级。
- `schemas/report.schema.json`：结构化报告合同。
- 校验：`py -3 scripts/validate_report.py path/to/report.json`，在 skill 目录运行；通过 exit 0，结构违规 exit 1，读取/JSON 错误 exit 2。机器通过不证明科学或创新。

## v3.6 可执行验收

公共规则为 `references/protocol.md`。报告合同为 `schemas/report.schema.json`；在本 skill 目录执行 `py -3 scripts/validate_report.py --self-test`（64 项状态合同测试（v3.6 扩展六维度））。聚合验收执行 `py -3 scripts/check_convergence.py`，检查七 skill 资源、manifest、版本与 validator 一致性。
