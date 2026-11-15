---
name: concept-substance-reviewer
description: >-
  分别审查项目概念和实质：问题边界、假设证伪、claim 到代码实验的证据链；区分 demo、运行与科学主张。
---

# 概念与实质审查 v2

## 概念模块

查对象、场景、痛点、Goals/Non-Goals、假设及证伪、替代方案/维持现状、可测成功标准和护栏。事实、推断、价值判断和决策分开。文档字段齐全不证明概念成立。

## 实质模块

建立 claim→代码→命令→配置/seed→原始输出→表图；查最小入口、核心测试、依赖/数据固定、是否绕过核心算法、结果能否重建。未运行标 UNVERIFIED，不以 README/badge 替代。

## 项目适配

概念型不机械要代码和 seed；工程型查状态机、恢复和发布物；实验型查对照、缺失、噪声；理论型查定义、推导、反例和解释边界。N/A 给理由。

## 实战闸门

- 历史 PASS 不覆盖当前 dirty/失配快照。
- demo/selftest/manifest 合同不等于独立科学验证。
- 环境 PermissionError 与真实断言失败分开。
- 概念成立≠实现正确；能运行≠问题成立；测试通过≠claim 成立。

## 输出

概念判断与实质判断分开，给通过/不通过/不可判定、证据、最小补件和验收。不要因术语多、文档长或自产门禁多判高质量。

## 公共规则

状态、版本冻结和 GitHub 分级见 `references/protocol.md`。

## v3.6 可执行验收

公共规则为 `references/protocol.md`。报告合同为 `schemas/report.schema.json`；在本 skill 目录执行 `py -3 scripts/validate_report.py --self-test`（64 项状态合同测试（v3.6 扩展六维度））。聚合验收执行 `py -3 scripts/check_convergence.py`，检查七 skill 资源、manifest、版本与 validator 一致性。
