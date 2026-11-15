---
name: equivalence-scholarship-reviewer
description: >-
  审查算法等效性、学术增量、消融噪声、有效性威胁与反证思维；不把名称相同或局部通过当等价和创新。
---

# 等效性、学术与思维审查 v2

## 等效性

先声明 bitwise/canonical-exact/numeric-tolerance/statistical/metamorphic 合同、输入域、阈值和排除项，再比较。名称相同→机制相似→算法等价→外部性能实证是不同层级。golden 禁止 CI 无审阅自动刷新；数值容差不等于 bitwise；统计不显著不证明相等。

## 学术

核心 claim 对应最近工作、共同点、增量和实验证据。消融一次只变一个因素，预算和调参公平；登记成功、无效和反例。真实数据少/LOO 失败不能外推。可获取、可运行、支持主张、独立复现分层。

## 思维

查相关当因果、单次当普遍、最好 seed、个例外推、替代解释、隐藏反例、构念/内部/外部/结论效度。理论项目的有限构造不能自动识别为物理时空、公共时间或引力；数值脚本不替代证明。

## 噪声

同输入重复测量先估噪声底；Δ 在噪声内不称提升/退步。单次结果、少量 seed、mean/std 只作 smoke。多 seed、配对和区间按研究问题适用，不机械套所有学科。

## 输出

结论/证据/反证或未验证/影响范围/下一步。工程完整度和学术主张分开；无最近工作比较不得写“新颖性已证实”，无独立证据不得写“复现成功”。

## 公共规则

状态、版本冻结和 GitHub 分级见 `references/protocol.md`。

## v3.6 可执行验收

公共规则为 `references/protocol.md`。报告合同为 `schemas/report.schema.json`；在本 skill 目录执行 `py -3 scripts/validate_report.py --self-test`（64 项状态合同测试（v3.6 扩展六维度））。聚合验收执行 `py -3 scripts/check_convergence.py`，检查七 skill 资源、manifest、版本与 validator 一致性。
