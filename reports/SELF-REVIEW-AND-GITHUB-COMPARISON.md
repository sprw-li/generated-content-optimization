# 七项评审 skill 自审与 GitHub 同类框架比对

日期：2026-11-12  
方法：用本套 skill 审查自身（dogfooding），并以本机可取得正文的 GitHub 同类框架作对照。  
快照哈希：`81dd63fea94a9755`（25 文件，连续两次不变）

## 一、结论

**本套 v3.1 的"状态机与门禁一致性"达到同类水平；但"证据真实性"与"行为验证"两项明显弱于同类最佳实践。自审以 gate=REJECT 收口。**

一句话：它能防住"状态自相矛盾"，但此前防不住"证据是编的"。

## 二、实际取得正文的 GitHub 对照

| 来源 | 级别 | 读取状态 | 关键要求 |
|---|---|---|---|
| [repo-audit / evidence-grading.md](https://github.com/conorbronsdon/repo-audit/blob/main/checklists/modules/evidence-grading.md) | comparable-method | **text-read（raw 正文）** | 评级必须带可解析 `file:line`；无证据评级是 guess，**应被移除而非降级**；absence 必须写"查了 X/Y/Z，未找到"；修复必须点名文件/守卫/测试；in-flight 修复单列且不计入统计 |
| [eval-integrity](https://github.com/conorbronsdon/eval-integrity) | topic-only | summary-only（经 repo-audit 转引） | PRESENT = 代码或测试中实现并强制，而非散文 |
| [cloudbase skill-authoring / evaluation.md](https://github.com/tencentcloudbase/cloudbase-ai-toolkit/blob/bbe45cc29d8680f01815a0805514365f35d8cdbd/skills/skill-authoring/references/evaluation.md) | comparable-method | summary-only | 仅搜索摘要，未取得正文，不作强度结论 |
| [EuroSys 2022 badges](https://sysartifacts.github.io/eurosys2022/badges) | topic-only | summary-only | artifact 徽章分层 |

**本机 catalog 内的高强度同类**：[skill-criticagent](D:/agent-library/catalog/skill-criticagent/SKILL.md)（150 行，本地正文已读）。它要求：`file_assertions`/`tool_assertions` 取代"答案里写了路径"；审查前后对源输入与 SKILL.md 做 hash 且**必须不变**；baseline 轮次须用 fresh subagent 隔离污染；provider/权限/超时/传输失败**不得**计为 skill 质量失败。

## 三、自审发现的缺口（10 项，均已写入结构化报告）

### 高

**DEF-001｜证据定位不解析（已修复）**  
探针 `locator=D:/definitely/not/a/real/file.py:99999-100000` + 伪造 observation，修复前 validator 返回 **exit=0 PASS**。  
修复后同一探针返回 **exit=1**，提示 `evidence locator not resolved`。

**DEF-002｜无 rejected 出路，absence 无检索协议**  
只有 PASS/FAIL/UNVERIFIED/N/A；无证据评级只能降级保留，不能移除；absence 类结论无处承载"查了哪些、未找到"。repo-audit 明确要求两者。

**DEF-003｜完全没有行为维度**  
本套只审静态产物，不做 with/without 对比、不做触发测试。skill-criticagent 的核心恰在此处。

### 中

- **DEF-004**：`readonly` 为自报布尔值，无审查前后源文件 hash 对比。
- **DEF-005**：`remediation.action/acceptance` 为自由文本，未强制点名文件/守卫/测试。
- **DEF-006**：PASS 不区分"散文声称"与"代码或测试强制"。
- **DEF-008**：含 skill 一词的验证类短语被 `create-skill` intent 劫持——`验证这套评审 skill 本身` → 第一候选 `agent-library-skill-create`，本套未进候选；而 `检查这套 skill 的证据合同是否自洽` → 命中 `implementation-comparator`（score=133）。

### 低

- **DEF-007**：无 in-flight 修复分桶。

### 通过（达到同类水平）

- **DEF-009**：环境/传输失败与逻辑失败分离，与 skill-criticagent 规则一致。
- **DEF-010**：只有 N/A 或有 UNVERIFIED 时禁止 ACCEPT，17 项测试覆盖。

## 四、本轮已实际修复

**证据定位解析（`scope.resolve_root`）**

- 开启后，`file:line` 与裸路径 locator 会实际解析：文件必须存在，行号必须在范围内。
- HTTP(S) URL 与散文定位（如 `session seq 5206`）不解析，避免误报。
- 未提供 `resolve_root` 时保持原非空检查，向后兼容，不使既有报告失效。

验证：
- 伪造定位探针：修复前 exit=0 → 修复后 **exit=1**
- 自审报告开启解析后**全部本地证据定位通过**（10 findings，exit=0），证明其证据真实可验
- 自测从 11 项扩至 **17 项**，全部 OK
- 七 skill 收敛检查 CONVERGED，validator 无漂移，skill 检查 errors=0 warnings=0
- 路由回归 96/96

## 五、仍未修复（协议已明示，不得声称已修）

见 [protocol.md](D:/agent-library/catalog/project-review-orchestrator/references/protocol.md) 的"已知缺口"节：rejected 出路、searched_scope、行为维度、readonly hash 验证、remediation 点名、PASS 分级、in-flight 分桶、路由覆盖。

## 六、交付物

| 文件 | 内容 |
|---|---|
| [self-review-resolved.json](review-skill-system/v3.1/meta-eval/self-review-resolved.json) | 自审结构化报告，开启定位解析后可验 |
| [locator-resolution-probe.json](review-skill-system/v3.1/probe/locator-resolution-probe.json) | 修复前探针（伪造定位，曾被 PASS） |
| [locator-resolution-probe-fixed.json](review-skill-system/v3.1/probe/locator-resolution-probe-fixed.json) | 同一伪造定位，现被拒绝 |
| [validate_report.py](review-skill-system/v3.1/shared/validate_report.py) | 17 项测试的校验器，含定位解析 |
| [protocol.md](review-skill-system/v3.1/shared/protocol.md) | 含"已知缺口"节 |
| [report.schema.json](review-skill-system/v3.1/shared/report.schema.json) | 新增 `scope.resolve_root` |

## 七、边界

1. GitHub 仅 repo-audit 取得 raw 正文；eval-integrity 与 cloudbase 仅搜索摘要，未作强度结论。
2. 本机直连 GitHub 受限，未 clone 或运行任何外部仓库。
3. 本套与对照框架**目标不同**：repo-audit 面向代码仓库合规，skill-criticagent 面向安装决策，本套面向多维证据评审。故不设总分对比（标记 INCOMPARABLE）。
4. 定位解析只证明"文件与行存在"，**不证明观察文字正确**。
5. 行为维度缺口意味着：本套目前无法回答"这个 skill 是否真的有用"，只能回答"它的产物与证据链是否自洽"。
