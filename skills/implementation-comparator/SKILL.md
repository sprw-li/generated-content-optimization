---
name: implementation-comparator
description: >-
  对齐版本、环境、输入和输出做 reference/candidate 事实比较，区分 MATCH、DIFF、INCOMPARABLE 和 UNVERIFIED。
---

# 实现事实对比 v2

只回答：哪些对象在什么条件下，对哪些输入，产生了什么相同或不同。不直接作学术等价或创新结论。

## 比较合同

记录对象与 commit、环境依赖、输入数据版本、配置 seed、执行命令和 exit code、原始输出、规范化规则、预声明容差、差异、未覆盖范围。

## 状态

- MATCH：按预声明规则一致。
- DIFF：存在可定位差异。
- INCOMPARABLE：版本、环境、输入、指标或语义未对齐。
- UNVERIFIED：未执行或证据不足。

检查结构化结果；命令 exit 0 仍可能有 hash/预算失配。环境阻塞标 ENVIRONMENT_BLOCKED，不判 DIFF。

## 等效性接口

bitwise/canonical-exact/numeric-tolerance/statistical/metamorphic 先声明后运行。容差不能事后调；无 reference 时用 MR，但必要非充分。相似 API、算法名或功能不自动等价。

## 输出

机器可读比较记录、失败样本、环境指纹和覆盖边界；交专项审查解释，不擅自宣称复现成功。

## 公共规则

状态、版本冻结和 GitHub 分级见 `references/protocol.md`。

## v3.6 可执行验收

公共规则为 `references/protocol.md`。报告合同为 `schemas/report.schema.json`；在本 skill 目录执行 `py -3 scripts/validate_report.py --self-test`（64 项状态合同测试（v3.6 扩展六维度））。聚合验收执行 `py -3 scripts/check_convergence.py`，检查七 skill 资源、manifest、版本与 validator 一致性。
