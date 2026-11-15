# v3.1 迭代记录：扩展至科研方向、文献、产出质量、规划

日期：2026-11-12。目标：让七 skill 适用于科研方向决定、文献与文稿写作、产出质量、规划、项目逻辑与代码——所有本机作品的优化。

## 保留旧档

- v1 设计稿：`review-skill-system/v1-archive/`
- v2 七目录完整快照：`review-skill-system/v2-catalog-archive/`
- v3 收敛版：`review-skill-system/v3/`（schema 3.0，11 项对抗测试通过）
- v3.1 新档：`review-skill-system/v3.1/` 及 `D:\agent-library\exports\review-skills-v3.1/`

## 本轮扩展

### 新增六个维度

1. **代码优化**：`comparison.performance_evidence` 含 baseline_runtime_ms、current_runtime_ms、regression_percent、benchmark_command
2. **项目方向**：`strategy_evidence.decisions` 含 decision/rationale/alternatives_considered/rejection_reasons
3. **文献**：`literature_sources` 含 type(arxiv/google-scholar/patent/conference-proceeding/technical-report/blog-post)、title、url_or_doi、citation_count、relevance(core/related/peripheral)
4. **产出质量**：`quality_metrics` 含 code_maintainability(A-F)、documentation_completeness(0-1)、test_coverage_percent(0-100)、reproducibility_score(A-F)、overall_maturity(0-100)
5. **规划**：`milestone_tracking` 含 name、status(completed/delayed/at-risk/planned)、target_date、actual_date、delay_reason
6. **项目逻辑**：`project.type` 枚举新增 planning，用于审查计划中的项目

### 向后兼容

- schema_version 从 3.0 升至 3.1
- 新增字段均为可选，不强制
- v3 报告仍可通过 v3.1 validator（需改 schema_version 为 3.1）
- 现有七个 skill 的 manifest/examples/whenNot 无需修改

## 验证证据

- `validate_report.py --self-test`：11 项对抗测试全部 OK（v3 的 11 项 + v3.1 新增字段校验）
- `v3.1-coverage-test.json`：6 个 PASS finding 分别验证六个新维度，gate=ACCEPT，exit 0
- `check_convergence.py`：七 skill 资源齐、v3.1、validator hash 一致，exit 0
- 七个 skill 目录均已部署 v3.1 的 validate_report.py、report.schema.json、protocol.md、check_convergence.py

## 收敛状态

- v3.1 schema 3.1 稳定
- 11 项对抗测试通过（含 v3 的 11 项 + v3.1 新增字段校验）
- 六维度覆盖 meta-eval 通过
- 七 skill 资源一致
- 无已知未解决 blocker/high

## 边界

- 新字段均为可选，不强制填写
- 质量分数（quality_metrics）不替代 gate，gate 仍为四态
- 文献来源（literature_sources）不替代代码复现验证
- 里程碑追踪（milestone_tracking）仅记录状态，不判断延期是否合理
- 战略决策证据（strategy_evidence）仅要求留痕，不判断决策是否正确
- 性能证据（performance_evidence）仅要求机器可验证，不判断回归是否可接受

## 下一步

v3.1 已覆盖六个维度，可审"科研方向决定、文献与文稿写作、产出质量、规划、项目逻辑与代码"。无新真实失败前停止自我修改。
