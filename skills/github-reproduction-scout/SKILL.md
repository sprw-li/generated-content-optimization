---
name: github-reproduction-scout
description: >-
  按证据缺口拆分 subagents 在 GitHub 寻找官方参照、独立复现和可比方法，核验来源并去重；不把相似仓库当复现。
---

# GitHub 复现检索 v2

## 启动条件

已有项目 claim 和证据缺口。不固定开四个 agent；按官方原实现、独立复现、可比方法/验证工具、相近工作与替代方案动态分工，任务不得重复。

## 每个 subagent 返回

查询词、日期、GitHub URL、固定 commit/版本、官方/独立/可比/主题分类、摘要或正文核对、是否运行、能支持与不能支持的结论。fork/镜像去重。

## 分级

- official-reference：官方参照实现，可做版本化数值/语义对照。
- independent-reproduction：有独立复现证据，仍需本地运行验证。
- comparable-method：可比算法或测量工具，不能称本项目复现。
- topic-only：主题相关线索，不支持等效性。

## 停止

所有问题覆盖、新查询持续重复、达到预算或网络/权限受限。检索失败如实报告，不用搜索数量补门面。HTTP 200、README、star、badge、仓库存在均不等于复现。

## 输出

候选表→去重→证据级别→适配的比较合同→未找到和未核对项。不要修改被审项目，不要把参考项目缺陷移植成本项目缺陷。

## 公共规则

状态、版本冻结和 GitHub 分级见 `references/protocol.md`。

## v3.6 可执行验收

公共规则为 `references/protocol.md`。报告合同为 `schemas/report.schema.json`；在本 skill 目录执行 `py -3 scripts/validate_report.py --self-test`（64 项状态合同测试（v3.6 扩展六维度））。聚合验收执行 `py -3 scripts/check_convergence.py`，检查七 skill 资源、manifest、版本与 validator 一致性。
