# 证据评审套件公共协议 v3.6

> **八成员制**：七项通用评审 skill + `skill-criticagent`（skill 领域行为与安装决策专家）。接口见 `catalog/skill-criticagent/references/suite-interface.md`。
>
> v3.3 关闭了 v3.2 遗留的六项缺口；v3.4 关闭 PASS 分级（enforcement）；v3.5 新增证据锚定与理由强度检查；v3.6 关闭 council 评审出的 7 项形式化绕过。

只读审查默认不改项目。路径简称先列父目录解析全名；会话 ID 可以是独立评审对象，先定位实际交付物。

## 状态和总门禁

审查项：PASS/FAIL/UNVERIFIED/N/A。执行：EXECUTED_PASS/EXECUTED_FAIL/ENVIRONMENT_BLOCKED/NOT_RUN/NOT_APPLICABLE。总门禁：ACCEPT/CONDITIONAL/REJECT/INCOMPLETE。

环境权限/依赖失败不是项目逻辑失败；必要检查未完成时门禁 INCOMPLETE。exit 0 不是充分证据，要检查计数、预算、hash 和结构化输出。未解决 blocker/high FAIL 禁止 ACCEPT/CONDITIONAL；findings 或 comparisons 有 UNVERIFIED 禁止 ACCEPT；ACCEPT 至少一个实际执行的 PASS finding，只有 N/A 不算实质检查。

## 版本冻结

记录 commit 和 dirty；无 git 标本次快照。历史 PASS 不覆盖当前修改。先查代码、测试、结果、文档和 manifest 一致，再解释测试。

## GitHub 分级

official-reference / independent-reproduction / comparable-method / topic-only。记录 URL、版本、检索日期、正文核对和是否运行。仓库存在、HTTP 200、README 和 badge 不等于复现成功；summary-only 不得标 independent-reproduction。

## 文献来源

v3.1 新增 `literature_sources`：arXiv、Google Scholar、专利、会议论文集、技术报告、博客。记录 type、title、URL/DOI、检索日期、引用数、相关性（core/related/peripheral）。文献检索不替代代码复现验证。

## 对比

MATCH 必须实际执行通过，DIFF 必须实际观察到差异；INCOMPARABLE 给未对齐原因；UNVERIFIED 是未运行或环境阻塞。禁止将相似功能直接当 MATCH。

v3.1 新增 `performance_evidence`：在 comparison 中记录 baseline_runtime_ms、current_runtime_ms、regression_percent、benchmark_command。性能回归需机器可验证。

## 项目适配

concept 查假设和证伪；engineering 查入口、状态机和发布物；experiment 查对照、缺失、噪声和区间；reproduction 查 reference、输入域、容差；theory 查定义、推导、反例和边界；**planning**（v3.1 新增）查里程碑、资源分配、延期原因。N/A 给理由。

## 产出质量度量

v3.1 新增 `quality_metrics`：code_maintainability（A-F）、documentation_completeness（0-1）、test_coverage_percent（0-100）、reproducibility_score（A-F）、overall_maturity（0-100）。质量分数不替代 gate，gate 仍为四态。

## 战略决策证据

v3.1 新增 `strategy_evidence`：记录 decisions（decision/rationale/alternatives_considered/rejection_reasons）。方向转换、技术路线选择需留痕。

## 里程碑追踪

v3.1 新增 `milestone_tracking`：name、status（completed/delayed/at-risk/planned）、target_date、actual_date、delay_reason。delayed 必须给原因。

## 证据锚定（v3.5，把"引用了"变成"引用处真的有这句话"）

当 `scope.resolve_root` 存在且 locator 是 `file:line` 形态时，校验器会取出**被引用的那些行**，要求：

1. 观察文本里的**锚定 token**（≥4 字符的标识符或数字，去掉停用词）至少有一个**真实出现在所引行中**；
2. 若所引行有 token 而观察文本**一个 token 都没有**（例如纯中文描述），同样判失败——否则可以靠"全写中文"绕过检查；
3. 需要语义引用时，必须显式设 `evidence.semantic_only=true` 并给出 `anchor_note` 说明为何没有字面锚点。不允许静默保留一个不锚定的引用。

这关闭了一类真实问题：**行号指向的位置并不包含观察描述的东西**。在 v3.5 自身迁移中，56 条引用有 20 条未锚定（36%）：其中 14 条经补入所引行**真实存在的标识符**而锚定，11 条如实标为 `semantic_only`——**没有用 token 重合把弱匹配洗成强引用**。

## 理由强度（v3.5）

- `na_reason` 至少 30 字符：必须说明**哪项检查不适用、为什么**，不能写"不适用"。
- `rejected_reason` 至少 30 字符，且必须点名搜索动作（路径 / 模式 / grep / pytest 等）或同时提供 `searched_scope`。
- `claim_class` 为 `novelty` 或 `equivalence` 时，报告必须至少引用一个外部来源（`github_sources` 或 `literature_sources`）：**没有最近工作比对的"新颖性"不可审计**。

## 行为用例覆盖（v3.5）

`behavior_evidence.case_tags` 必须逐用例给出标签（≥3 个）且**至少 2 个不同场景**；`verdict` 为 `install`/`fix-first` 时必填。只有同类用例堆数量不算覆盖。

**这一项做到什么程度是诚实的**：机器能查"标签是否多样"，不能查"标签是否覆盖真实使用分布"。后者仍需人工抽样。

## 结构化报告

每项目单独报告，project.evidence_scope 标 single-project 或 isolated-multi-project。scope 必填输入、排除、readonly 布尔值和覆盖范围；缺输入不得 ACCEPT。报告对应 `report.schema.json`，用 `validate_report.py` 校验。机器只检查结构、状态、来源、比较和门禁一致性，不证明概念、创新、科学或等效性。

## 行为证据（v3.2，整合 skill-criticagent）

对象是 Agent Skill 时，由 orchestrator 派发到 `skill-criticagent`，其裁决写入 `behavior_evidence`：

- `with_skill_pass` / `without_skill_pass` / `cases_total`：行为对比。
- `trigger_correct` / `trigger_total`：触发准确率。
- `source_hashes_stable`：审查前后源输入与 SKILL.md hash 未变。
- `baseline_isolated`：基线轮次用 fresh subagent，未被读过 skill 污染。
- `execution_evidence`：运行产物、transcript、grader JSON 路径。
- `verdict`：`install` / `fix-first` / `reject` / `not_applicable`。

**门禁强制**（validator 实施）：`install` 需 execution_evidence 非空、源 hash 稳定、基线隔离、且 with>without；`reject` 需 gate 为 REJECT/INCOMPLETE；`fix-first` 禁止 ACCEPT；`not_applicable` 需 verdict_reason。

**"答案里写了路径"不算证据。** 三层证据不可互替：静态合规、行为增量、领域学术判断。

## 证据定位解析（v3.1 引入，v3.2 保留）

`scope.resolve_root` 存在时，`file:line` 与裸路径形态的 evidence locator 会被实际解析：文件必须存在，行号必须在范围内；HTTP(S) URL 和散文式定位（如 `session seq 5206`）不解析。无法解析即校验失败。**这使伪造的 file:line 不能通过 PASS/FAIL。** 未提供 `resolve_root` 时只做非空检查。定位解析只证明"文件与行存在"，不证明观察文字正确。

## 已知缺口（自审记录，不得声称已修复）

2026-11-12 以本套 skill 自审并对照 GitHub [repo-audit evidence-grading](https://github.com/conorbronsdon/repo-audit/blob/main/checklists/modules/evidence-grading.md)：

v3.2 列出的 6 项已在 v3.3 关闭，对应实现与测试：

| 原缺口 | v3.3 修复 | 机器证据 |
|---|---|---|
| 无 rejected 出路 | `status=REJECTED`：须 `rejected_reason`、不得带 evidence、执行只能是 `NOT_RUN`/`ENVIRONMENT_BLOCKED` | `test_rejected_removes_unevidenced_rating` 等 3 项 |
| 无 searched_scope | `claim_kind=absent` 时强制 `searched_scope` 非空 | `test_absent_claim_requires_searched_scope` |
| readonly 自报 | `readonly=true` 时强制 `scope.source_hashes`，且 `stable=true`；配套 `source_fingerprint.py` | `test_readonly_requires_source_hashes` 等 2 项 |
| remediation 自由文本 | `NAMED_FIX` 要求 blocker/high/medium 的 action 点名文件/守卫/测试；`EXEC_CMD` 要求 acceptance 是可执行命令 | `test_medium_fix_*` 等 3 项 |
| 无 in-flight 分桶 | `in_flight_fixes` 须引用存在的 finding 且 `verified_against` 点名文件/diff/命令；**不豁免门禁** | `test_in_flight_*` 等 2 项 |
| 行为用例仅 1 条、5 条非判别断言 | 扩到 3 条纯任务用例；断言改词界正则；剔除 3 条非判别断言 | grader `non_discriminating=0`，with 3/3 vs without 0/3 |

另新增两条门禁收紧：

- **ACCEPT 不得存在任何未解决 FAIL**（不限严重度），防止 medium 级缺陷被 ACCEPT 吞掉。
- REJECTED 不计入 blocker，但也不能充当 ACCEPT 所需的 PASS 证据。

## PASS 分级（v3.4，关闭最后一项缺口）

`finding.enforcement` 必填于所有 PASS：

- `code`：实现存在于代码中，且证据必须含 `file:line`。
- `test`：有测试强制执行，证据必须含 `file:line`。
- `prose`：仅文档/声称存在——**不构成 PRESENT**，不能单独支撑 ACCEPT。
- `not_applicable`：不适用（如配置类陈述）。

机器强制：

1. PASS 缺 `enforcement` → 校验失败（"a label without substance is a FAIL"）。
2. `enforcement=code|test` 但证据中没有 `file:line` → 校验失败。
3. gate=ACCEPT 时至少需要一条 `enforcement` 为 `code` 或 `test` 的 PASS；**纯 prose PASS 不够**。
4. `prose` PASS 可以存在，但不能替代实质证据。

这直接实现了 repo-audit 的 `PRESENT = implemented and enforced in code or a test, not prose`。

**仍未关闭（如实记录，不得声称已修）**：


**仍不做机器判断的事（v3.5 后收窄）**：

- 仍完全不可机器判定：科学正确性、创新性、理论有效性。机器只能强制「新颖性声明必须附外部引用」，
  不能判断该引用是否真的构成最近工作。
- 已转为机器可查（v3.5）：证据文字是否与所引行**字面锚定**；`N/A` 理由是否给出实质说明；
  `rejected_reason` 是否点名搜索动作；新颖性/等效性声明是否附外部引用；行为用例标签是否多样。
- 半可查：理由「是否成立」仍需人看。机器只挡住三种最差情况——根本没写理由、理由过短、没有搜索动作。

历史自审见 `meta-eval/self-review.json`（v3.2，gate=REJECT）；v3.3 复评见 `meta-eval/integrated-review-v3.3.json`。

## 证据来源

由 2026-11-11 五项目只读审查校正；v3 经状态合同对抗测试修复；v3.1 扩展至科研方向、文献、产出质量、规划维度并引入证据定位解析；v3.2 整合 `skill-criticagent` 为第八名成员，补齐行为与触发维度并修复路由劫持。sandbox PermissionError、历史快照漂移、算法名不等价、demo 非独立验证均为实际发现。
