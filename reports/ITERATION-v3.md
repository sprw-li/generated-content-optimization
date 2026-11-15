# v3 迭代记录：七项证据评审 skill

日期：2026-11-11。目标：实际修复自审发现的问题，而非通过重复自评制造“收敛”。

## 保留旧档

- v1 设计稿：`review-skill-system/v1-archive/`
- v2 七目录完整快照：`review-skill-system/v2-catalog-archive/`
- v2 导出：`D:\agent-library\exports\review-skills-v2/`
- v3 新档：`review-skill-system/v3/` 及 `D:\agent-library\exports\review-skills-v3/`

## 本轮新发现

1. v2 schema 声明了 scope 必填，Python 校验器却没有检查 inputs/exclusions。
2. v2 `RESOLVED` 只需任意 acceptance_result 字符串，无法表达命令、exit code、观察结果。
3. v2 不阻止未解决 blocker/high FAIL 配 ACCEPT。
4. GitHub 来源分级、INCOMPARABLE 和 MATCH 的执行要求只有正文，没有机器合同。
5. 七 skill 的公共协议/校验器复制可能漂移；v2 只有两目录有校验器。
6. 初次安装资源时目标目录不存在，PowerShell 将脚本复制成名为 scripts/schemas 的文件。已保留错误副本到 `v2-copy-failures/`，修正为目录后复验。这个失败不计为质量测试通过。

## v3 修复

- report schema 升级 3.0；project.type、evidence_scope、scope.inputs/exclusions/readonly/coverage_note 强制校验。
- 状态与执行强一致：PASS/FAIL/N/A/UNVERIFIED 各有允许执行状态。
- RESOLVED 需要 command、exit_code=0、observed。
- 未解决 blocker/high FAIL 只能 REJECT/INCOMPLETE；UNVERIFIED 禁止 ACCEPT；空 findings 禁止 ACCEPT。
- GitHub 来源强制 level/url/version/retrieved/read_status，summary-only 不得称 independent-reproduction。
- 比较强制 contract/execution/result；INCOMPARABLE 需 reason，MATCH/DIFF 需相应实际执行。
- 七目录均有同一 validator、schema、protocol 和聚合检查；validator SHA256 必须一致。

## 验证证据

- `validate_report.py --self-test`：9 项 unittest OK。
- 七个 skill 目录逐一运行：均 9 项 OK。
- `check_convergence.py`：7 skills 资源齐、版本 v3、validator 无漂移，exit 0。
- 七个 `check_skill.py`：errors=0、warnings=0。
- 全库 router eval：96/96 intent top1、96/96 skill top1/top5。
- 前两路独立审查均失败，没有形成审查结论；不能宣称其通过。
- 后续窄范围独立 subagent 成功只读复核，发现两个 high：仅 N/A 可 ACCEPT、comparison UNVERIFIED 可 ACCEPT。已补回归测试并修复，现共 11 项 unittest OK；协议和 validator 同步。独立审查未执行脚本，因此执行证据仍以主流程实测为准。
- council_review 未获得目标文件附件且部分席位失败，其输出不作为缺陷或通过证据。

## 收敛定义与边界

这里的收敛是**已声明机器合同和资源一致性收敛**，不是语义评审能力、科研正确性或对所有项目的适用性已被证明。validator 只能检查结构和门禁一致性，不能判断证据是否真实、理论是否正确或新颖性是否成立。

不以文档字数、修改轮数或单次 PASS 宣称普遍质量提升。无新的可复现高优先级问题时停止机器结构迭代；新的真实项目失败应开启新版本。
