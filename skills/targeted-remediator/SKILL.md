---
name: targeted-remediator
description: >-
  把已证实项目缺点转为最小修改、可执行验收和回归；获授权才修改，保留旧档，未运行不得称已解决。
---

# 针对性改进 v2

## 权限

只读评审不得自动改项目。只有用户明确授权修改时才实施；先保留旧档或分支，写新档，不覆盖历史证据。不要改动无关工作树文件。

## 每项改进

关联 finding ID、根因、修改文件/组件、最小动作、验收命令、预期机器可读结果、回归检查、残余风险。优先阻断核心 claim 的根因，不先美化 README。

## 验收

未执行写 NOT_RUN；失败写 FAILED；权限阻塞写 ENVIRONMENT_BLOCKED。只有实际验收命令、exit code 和结构化结果支持时才写 RESOLVED。修改后更新 claim-evidence、版本和 manifest。

性能/效果改动先重复测同配置基线与修改后结果，估计噪声；Δ 在噪声内不称提升或退步。单次运行和 demo 合同不构成普遍改进。

## 输出

改动清单、旧档位置、验收日志、残余风险、未执行项和复审状态。不要编造 commit，不要把计划说成已修复。

## 公共规则

状态、版本冻结和 GitHub 分级见 `references/protocol.md`。

## v3.6 可执行验收

公共规则为 `references/protocol.md`。报告合同为 `schemas/report.schema.json`；在本 skill 目录执行 `py -3 scripts/validate_report.py --self-test`（64 项状态合同测试（v3.6 扩展六维度））。聚合验收执行 `py -3 scripts/check_convergence.py`，检查七 skill 资源、manifest、版本与 validator 一致性。
