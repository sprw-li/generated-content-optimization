# generated-content-optimization

**Generated Content Optimization — 八成员证据评审套件**

**用途：项目优化与证据式评审的交付包**  
**版本**：v3.6（八成员制；64 项合同测试；14 项对抗探针 0 漏洞；双次只读指纹；5 份项目记录共 30 条发现）  
**打包日期**：2026-11-15  
**本包自包含**：所有 skill、公共合同、整合接口与本次验收证据均在包内，不依赖外部路径。例外：被审查的五个项目本身不在包内；这些记录的原始证据行号需对应其项目根目录复核，缺失时验收脚本显式报告。

---

## 一句话说明

这是一套**用于审查"我的作品"的证据式评审框架**：审查代码与项目、科研方向、文献与文稿、产出质量、规划，以及 Agent Skill 的行为有效性。它的核心主张是——**把"声称"和"证据"分开，把"环境失败"和"逻辑失败"分开，把"结构合法"和"科学成立"分开。**

---

## 一、成员构成（8 个）

七项通用评审 skill + 一名 skill 领域专家：

| # | 成员 | 职责 |
|---|---|---|
| 1 | `project-review-orchestrator` | 总控：识别对象与版本、调度、聚合、最终门禁 |
| 2 | `github-reproduction-scout` | 按缺口拆 subagent 检索 GitHub，来源分四级 |
| 3 | `implementation-comparator` | 事实对比：MATCH / DIFF / INCOMPARABLE / UNVERIFIED |
| 4 | `defect-synthesizer` | 缺点去重、定级、绑定证据 |
| 5 | `targeted-remediator` | 改进：留旧档存新档、验收、回归 |
| 6 | `concept-substance-reviewer` | 概念与实质分开判断 |
| 7 | `equivalence-scholarship-reviewer` | 等效性、学术增量、噪声、反证 |
| 8 | `skill-criticagent` | **skill 领域专家**：合规安全、with/without 行为对比、触发测试、安装裁决 |

第 8 名以**引接**方式整合（不复制其正文，避免双份真源）：接口契约见 `integration/suite-interface.md`。

---

## 二、这套框架解决什么问题

### 状态三层分离

- **审查项状态**：`PASS` / `FAIL` / `UNVERIFIED` / `N/A` / `REJECTED`
- **执行状态**：`EXECUTED_PASS` / `EXECUTED_FAIL` / `ENVIRONMENT_BLOCKED` / `NOT_RUN` / `NOT_APPLICABLE`
- **总门禁**：`ACCEPT` / `CONDITIONAL` / `REJECT` / `INCOMPLETE`

关键规则：环境/权限失败**不是**项目缺陷；`exit 0` **不是**科学通过；只有 `N/A` 项**不能** ACCEPT。

### 已强制的门禁

1. 未解决的 blocker/high FAIL → 只能 `REJECT`/`INCOMPLETE`
2. 存在 `UNVERIFIED`（findings 或 comparisons）→ 禁止 `ACCEPT`
3. `ACCEPT` 至少需一个实际执行的 `PASS`
4. `RESOLVED` 必须附命令、`exit_code=0` 与观察结果
5. **伪造 `file:line` 无法通过**（`scope.resolve_root` 会真实解析文件与行号）
6. `behavior_evidence.verdict=install` 需四者同时成立：执行证据非空、源 hash 稳定、基线隔离、with > without

---

## 三、真实证据（不是声称）

### 行为维度：真实 with / without 对比（3 条用例）

六个隔离 subagent（3 用例 × 带/不带），基线被禁止读取任何本地文件：

```
with_skill    3/3 通过
without_skill 0/3 通过
uplift        +1.0
非判别性断言   0 条
源 hash 稳定   True
```

基线自行编造了不同枚举（COMPLETED / BLOCKED / ERROR / FAIL），因此判别性断言真实生效。评分器还审计出我最初的断言中有非判别性项（5→3→0），已按建议剔除而非保留假判别。

### 触发维度：用 criticagent 自己的评分器跑本套 skill

```
8/8, accuracy = 1.0, exit = 0
```

4 条触发话术首候选均为 orchestrator；4 条近邻正确落到其他成员。

### 双向审计

criticagent 的评分器**反过来审计本套自建断言**，其 `assertion_audit` 已成为本包验收的硬检查项之一。

---

## 四、缺口处理：七项全部关闭

v3.2 曾列 6 项未解决缺口，v3.3 关闭六项，v3.4 关闭最后一项（PASS 分级）。全部有机器证据：

| 原缺口 | 修复 | 证据 |
|---|---|---|
| 无 `rejected` 出路 | `status=REJECTED`：须 `rejected_reason`、不得带 evidence、执行限 `NOT_RUN`/`ENVIRONMENT_BLOCKED` | 3 项对抗测试 |
| 无 `searched_scope` | `claim_kind=absent` 强制 `searched_scope` 非空 | 2 项对抗测试 |
| `readonly` 自报 | `readonly=true` 强制 `scope.source_hashes` 且 `stable=true`；配套 `source_fingerprint.py` | 2 项对抗测试 + 本包实跑 |
| `remediation` 自由文本 | `NAMED_FIX` 要求点名文件/守卫/测试；`EXEC_CMD` 要求 acceptance 可执行 | 3 项对抗测试 |
| 行为用例仅 1 条、5 条非判别断言 | 扩到 3 条纯任务用例，断言改词界正则，剔除 3 条弱断言 | grader `non_discriminating=0` |
| 无 in-flight 分桶 | `in_flight_fixes` 须引用存在 finding 且 `verified_against` 点名文件/diff/命令；**不豁免门禁** | 2 项对抗测试 |
| **PASS 不分级** | `finding.enforcement` 必填：`code`/`test` 须有 `file:line` 证据；`prose` 仅文档声称，不能单独支撑 ACCEPT | 5 项对抗测试 |

对应 repo-audit 的 `PRESENT = implemented and enforced in code or a test, not prose`。

另新增三条收紧：**ACCEPT 不得存在任何未解决 FAIL**；**REJECTED 不能充当 ACCEPT 所需的 PASS 证据**；**ACCEPT 至少一条 code/test 级 PASS**。

### 机器边界（v3.6）

**已机器可查**：引用锚定（所引行必须字面含观察 token，或显式声明 semantic_only 且占比 ≤30%）；`N/A`/`rejected_reason`
理由强度；新颖性必须附**真正读过**的最近工作（topic-only / summary-only 不算）；行为用例标签多样；本地 file:line
**强制** `resolve_root`（否则整份报告不可 ACCEPT）；URL 不能冒充源码证据；`RESOLVED` 必须有磁盘上存在的运行产物；
`REJECTED` 不能收纳 blocker/high；`CONDITIONAL` 也不能携带未解决 FAIL；只读声明必须由**两次独立调用**的指纹证明。

**仍完全不可机器判定**：科学正确性、创新性、理论有效性的**真伪**。

**半可查**：理由「是否成立」仍需人看——机器只挡住「没写理由 / 理由过短 / 没有可核查的搜索目标」。

## 五、council 多模型评审（2026-11-15）与修复

用 `council_review` 让三个模型独立攻击本套件。它们报出的问题里 **7 条经核验为真**，已全部关闭：

| council 指出的漏洞 | v3.6 处置 |
|---|---|
| 不写 `resolve_root` 即可跳过全部文件级与锚定检查 | **强制**：引用本地 file:line 而没有 resolve_root → 校验失败 |
| URL 冒充 file:line 满足 `enforcement=code/test` | URL 不再计入源码证据，且跳过一切文件级检查的路被堵死 |
| `CONDITIONAL` 可掩盖未解决 medium FAIL | `ACCEPT` 与 `CONDITIONAL` 都禁止任何未解决 FAIL |
| 把 high FAIL 改写成 `REJECTED` 即从统计消失 | `REJECTED` 不得携带 blocker/high |
| `RESOLVED` 只查字段、不要求任何真实运行产物 | 必须有 `acceptance_result.artifact`，且文件须存在 |
| `source_fingerprint` 同进程背靠背 → `stable` 恒真 | 新增 `--stamp before/--stamp after` 两次独立调用模式；`stable` 单次自证不再是证据 |
| 指纹可覆盖与 `scope.inputs` 无关的路径 | 强制 `source_hashes.inputs` 覆盖 `scope.inputs`（含相对路径解析） |

另外修掉两个 council 点名的**真实脚本缺陷**：`reports/real_project_eval.py` 路径写错且 schema 停留在 3.0（已重写为
相对定位、按现行合同复核）；`shared/check_convergence.py` 在共享副本下解析到 `D:\Desktop`（已加入 skills 目录回退）。

**council 有 3 条报告基于旧版本**（`semantic_only` 无限绕过、novelty 无关引用、行为产物不校验）——这些在 v3.5 已部分修复、
v3.6 进一步加固。委员会三席中一席因配额失败，最终结论未合成。

**council 没抓到、由我自己的对抗探针抓到的**：证据锚定只共享一个通用词（`value`）即算通过——已提高为「≥2 个共享 token，
或 1 个在文件中罕见」。**council 抓到的、我的探针没覆盖的**：`CONDITIONAL` 掩盖 medium、`REJECTED` 收纳 high、
`source_hashes` 不覆盖 `scope.inputs`——已补成探针，现共 **14 项，0 漏洞**。

## 六、如何验收（可执行）

```powershell
cd D:\Desktop\opt
py -3 verify.py
```

预期：`ACCEPTED: 20/20 checks passed`，退出码 0。

该脚本检查：8 个成员完整、criticagent 已接入、validator 64 项自测通过、**伪造证据被拒绝**、整合报告证据可解析、行为证据（≥3 用例）自洽且与评分器输出一致、无非判别/恒失败断言、触发记录完整、intent 正则未被截断、只读指纹稳定、PASS 分级完整（每条 PASS 有 enforcement，且至少一条 code/test）、5 份项目记录共 30 条发现且符合现行合同（外部项目根缺失时显式报告，且无单条占位）、无现行报告停留在旧 schema、**引用锚定**、**14 项对抗探针 0 漏洞**、**双次只读指纹**（非自证）、**每条 RESOLVED 有磁盘产物**、**包完整性指纹**、门禁对未解决缺陷诚实。

---

## 七、目录结构

```
opt/
├── README.md              本文件
├── verify.py              一键验收（20 项检查，退出码 0 = 通过）
├── skills/                8 个成员，各自完整（SKILL.md + manifest + 资源）
├── shared/                公共合同
│   ├── protocol.md          状态、版本冻结、来源分级、锚定与机器边界
│   ├── report.schema.json   报告结构 v3.6（含行为证据与只读指纹）
│   ├── validate_report.py   校验器（64 项自测）
│   ├── source_fingerprint.py 只读声明的双次指纹工具
│   └── check_convergence.py 八成员一致性检查
├── integration/           criticagent 引接
│   ├── suite-interface.md     接口契约（输出映射与门禁耦合）
│   ├── behavior-result-v33.json  criticagent 评分器真实输出
│   ├── out-*-with.md            带 skill 的真实产出（3 用例）
│   ├── out-*-without.md         隔离基线的真实产出（3 用例）
│   ├── router-decisions.json    真实路由触发决策（8 条）
│   ├── adversarial-probe-report.txt  14 项对抗探针全部拦截的报告
│   ├── acceptance-artifacts/    RESOLVED 对应的实际运行日志
│   ├── source-hashes-v36.json   套件只读双次指纹
│   ├── source-hashes-pack.json  本包内容完整性指纹
│   ├── intents.json             当前路由 intent 配置
│   ├── intents-evidence.json    提交相关 intent 摘录
│   └── run_*.py                 原机复现脚本（换机需改路径）
├── reports/               自审与迭代记录
│   ├── INTEGRATION-v3.2.md                整合说明
│   ├── SELF-REVIEW-AND-GITHUB-COMPARISON.md  GitHub 同类框架比对
│   ├── meta-eval/                         **现行**评审报告（integrated-review-v3.6.json）
│   ├── meta-eval-history/                 历史版本评审（保留出处，不迁移）
│   ├── records/                           5 份项目记录（已迁移至 v3.6，共 30 条发现）
│   ├── records-legacy/                    迁移前原件（刻意保留旧 schema）
│   ├── snapshots/dsh-council-a99a724/     历史评审对应的只读源码快照（0.2.0）
│   └── probes/                            伪造证据探针（修复前/后各一份）
```

**注意**：`records/` 指向的项目（`D:\Dev\Project5-6-7-8`、`dsh-council`）**不在本包内**。验收脚本在本机存在这些根时逐份校验；根缺失时**显式报告**而非假装证据已解析。

**记录规模**（`records/` 共 30 条发现，每份 ≥3 条，无单条占位）：

| 记录 | 发现数 | 最高严重度 | gate |
|---|---|---|---|
| project5-cif | 8 | high | REJECT |
| project6-condopt | 6 | high | REJECT |
| project7-relaybench | 6 | high | REJECT |
| project8-quantum | 5 | high | REJECT |
| dsh-council | 5 | high | REJECT |

这些是会话内只读审查的**完整发现集**（不是完整复审循环——没有对修复后的版本再验）。每条都有可解析 `file:line`、点名文件的修复动作和可执行验收命令；行号对应审查时快照，项目若已变更需重跑定位校验。

**历史快照例外**：`dsh-council` 当前工作树已演进到 0.2.26，评审引用的源码固定为提交 `a99a724`（0.2.0），随包附带于 `records/../snapshots/dsh-council-a99a724`（即 `reports/snapshots/dsh-council-a99a724`）。该提交不完整代表曾未提交的 CI 工作树，因此其中的 CI 与最初会话结论只标为**会话语义证据**，不宣称当前版本或全部历史文件的独立验证。

---

## 八、参考的同类框架

- [repo-audit / evidence-grading](https://github.com/conorbronsdon/repo-audit/blob/main/checklists/modules/evidence-grading.md)（已读 raw 正文）：评级须带可解析 `file:line`；无证据评级应移除而非降级
- [eval-integrity](https://github.com/conorbronsdon/eval-integrity)（经转引，未直接读取）
- `skill-criticagent`（本包成员，含 vendored 确定性 kernel 与 SHA-256 manifest）

**证据边界**：仅 repo-audit 取得正文；其余为搜索摘要。未 clone 或运行任何外部仓库。

---

## 九、边界声明

1. 行为证据仅 3 条用例，**不足以声称普遍有效**；证据提升只适用于这三个任务。
2. 触发决策由路由器首候选代理，非真实宿主激活，每查询仅 1 次重复。
3. 三层证据不可互替：静态合规、行为增量、领域学术判断。
4. `PASS` 只表示按已声明判据通过，**不表示科学正确、创新成立或理论有效**。
