---
name: defect-synthesizer
description: >-
  把实际项目审查证据去重为分级缺点，区分真实失败、环境阻塞和未验证，绑定文件行号、影响和改进。
---

# 缺点综合 v2

## 输入

专项审查、实际运行、版本核对和比较记录。不是自由感想，也不把 GitHub 相似项目问题移植成本项目问题。

## 规则

- 每条 finding 有 ID、维度、陈述、证据定位、影响 claim、严重度、反证和不确定性。
- 合并重复但保留所有证据；区分根因与表象、已证实缺陷与风险。
- FAIL 必须实际执行且违反判据；权限/依赖阻塞用 UNVERIFIED+ENVIRONMENT_BLOCKED。
- exit 0 但预算/hash 失败仍可为 FAIL；测试计数必须对应快照。
- 严重度由对核心 claim 影响决定，不由措辞和文档长度决定。
- 不写无证据的“创新不足”“工程不成熟”等套话。

## 输出

阻断/高/中/低分组→根因→受影响声称→反证/未验证范围→关联改进。结构化 JSON 使用公共 validator；N/A 给理由，RESOLVED 必须有验收结果。

## 资源与校验

公共规则见 `references/protocol.md`。在 skill 目录执行 `py -3 scripts/validate_report.py path/to/report.json`；结构违规 exit 1，不得将结构 PASS 当项目质量 PASS。

## v3.6 可执行验收

公共规则为 `references/protocol.md`。报告合同为 `schemas/report.schema.json`；在本 skill 目录执行 `py -3 scripts/validate_report.py --self-test`（64 项状态合同测试（v3.6 扩展六维度））。聚合验收执行 `py -3 scripts/check_convergence.py`，检查七 skill 资源、manifest、版本与 validator 一致性。
