# v3.2：整合 skill-criticagent 为第八名成员

日期：2026-11-12。用户要求："把 critic 放进这一套，再整合"。

## 一、整合方式：引接，不是复制

`skill-criticagent` 是成熟的独立 skill（18 文件，含 vendored 确定性 kernel 与 SHA-256 manifest，以及 evals/evals.json、grade_runs.py、grade_triggers.py）。**复制其正文会造成双份真源和漂移**，因此采用引接：

- 新增接口契约：`catalog/skill-criticagent/references/suite-interface.md`
- 它仍是自己的 skill，只是被定义为套件的 skill 领域专家
- 七项缺的正是行为与触发维度；criticagent 缺的正是统一报告与多维门禁。互补，不重叠

| 成员 | 负责 | 不负责 |
|---|---|---|
| 七项评审 skill | 概念、实质、证据链、等效性、学术、来源、缺点、改进、门禁 | skill 的行为增量与触发准确率 |
| skill-criticagent（第 8） | 合规/安全、with/without 行为对比、触发测试、安装裁决 | 科研方向、文献、规划、多维学术评审 |

## 二、四层整合改动

### 1. 报告合同（schema v3.2）

新增 `behavior_evidence`：`cases_total`、`with_skill_pass`、`without_skill_pass`、`trigger_correct`、`trigger_total`、`source_hashes_stable`、`baseline_isolated`、`execution_evidence`、`evaluator`、`verdict`、`verdict_reason`。

### 2. 门禁耦合（validator 强制）

- `install` 需四者同时成立：`execution_evidence` 非空、`source_hashes_stable=true`、`baseline_isolated=true`、`with_skill_pass > without_skill_pass`
- `reject` → gate 必须 `REJECT`/`INCOMPLETE`
- `fix-first` 禁止 `ACCEPT`
- `not_applicable` 必须有 `verdict_reason`
- 计数不得超出总数

这直接编码了 criticagent 的规则：**"答案里写了文件路径"不算证据**。

### 3. 调度（orchestrator）

对象是 Agent Skill 时派发到 criticagent；并把 `behavior_evidence.verdict` 与 gate 的一致性写成显式步骤。

### 4. 路由（修根因）

发现并修复：`create-skill` intent 把 `skill-criticagent` 收进自己的 skills 列表，导致"验证/审查 skill"类请求被创建类独占。

- 新建 `skill-evaluation` intent，owner 为 `skill-criticagent` + `project-review-orchestrator`
- `skill-criticagent` 移出 `create-skill`，manifest 的 `intents` 改为 `skill-evaluation`
- 修复其占位 `whenNot`

## 三、真实端到端证据（非人工声称）

### 触发维度：criticagent 的评分器跑本套 skill

```
py -3 review-skill-system/v3.2/integration/run_trigger_integration.py
→ project-review-orchestrator: 8/8, accuracy=1.0, exit=0
```

4 条触发话术首候选均为 orchestrator；4 条近邻正确落到 skill-criticagent / implementation-comparator / equivalence-scholarship-reviewer。

### 行为维度：真实 with/without 对比

为 orchestrator 建立 `evals/evals.json`（断言**预声明**，不按输出调参），跑两个隔离 subagent：

```
py -3 review-skill-system/v3.2/integration/run_behavior_integration.py
→ with_skill 1/1, without_skill 0/1, uplift +1.0
→ source_hashes_stable = True, exit=0
→ assertion_audit: non_discriminating=5, always_failing=0
```

基线 subagent 被明确限制不读本地文件，故 `baseline_isolated=true`。它自行编造了不同枚举名（PENDING/NOT_STARTED/ERROR），因此判别性断言真实生效。

**criticagent 反过来审计了我的断言，指出 5 条非判别性**（PASS/FAIL/N/A/ACCEPT/REJECT 在两种模式下都通过）——双向整合生效。

## 四、自审发现并修复的问题

| ID | 问题 | 状态 |
|---|---|---|
| DEF-001 | 伪造 file:line 曾被判 PASS | ✅ 已修，探针现在 exit=1 |
| DEF-003 | 缺行为维度 | ✅ 已修，真实 with/without 证据 |
| DEF-004 | 路由劫持 | ✅ 已修，8/8 触发 |
| DEF-008 | 6 个 skill 的正则被逗号截断（首轮只修 5 个） | ✅ 已修，remaining broken=0 |
| DEF-002 | 无 rejected 出路 / 无 searched_scope | ❌ 未修（high，故 gate=REJECT） |
| DEF-005 | 5 条断言非判别性 | ❌ 未修 |
| DEF-006 | readonly 自报，无前后 hash | ❌ 未修 |
| DEF-007 | remediation 自由文本 | ❌ 未修 |

**一个值得记录的细节**：我自己的整合报告首次校验时被定位解析抓住 4 处错误定位（写了 `catalog/...` 相对工作区，实际在 `D:/agent-library`）。工具在抓自己人的错。

## 五、验证汇总

| 检查 | 结果 |
|---|---|
| validator 自测 | **26 项 OK**（含 9 项行为证据规则） |
| 收敛检查 | CONVERGED：7 review skills + criticagent specialist，无 validator 漂移 |
| 路由回归 | 96/96 intent top1、96/96 skill top1/top5 |
| 触发集成 | 8/8 accuracy=1.0 |
| 行为集成 | uplift +1.0，源 hash 稳定 |
| 整合报告 | 9 findings，gate=REJECT，定位全部解析通过 |
| broken patterns | 0 |

## 六、裁决与边界

`behavior_evidence.verdict = fix-first`：行为增量明确、触发满分，**但行为用例仅 1 条、13 条断言中 5 条非判别性**，不足以支撑完整 `install` 裁决。这与 gate=REJECT 一致（另有 DEF-002 未解决的 high）。

边界：
1. 行为证据 n=1，单用例不足以声称普遍有效。
2. 触发决策由 router 首候选代理，非真实宿主激活，且每查询仅 1 次重复；criticagent 本身也声明该限制。
3. GitHub 仅 repo-audit 取得 raw 正文，其余为搜索摘要。
4. 三层证据不可互替：静态合规、行为增量、领域学术判断。
5. 未 clone 或运行任何外部仓库。
