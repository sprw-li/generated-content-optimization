# 项目评审框架状态机（依据 SKILL.md + protocol.md v3.2）

**1. 审查项状态**：`PASS` / `FAIL` / `UNVERIFIED` / `N/A`

**2. 执行状态**：`EXECUTED_PASS` / `EXECUTED_FAIL` / `ENVIRONMENT_BLOCKED` / `NOT_RUN` / `NOT_APPLICABLE`

**3. 总门禁**：`ACCEPT` / `CONDITIONAL` / `REJECT` / `INCOMPLETE`

**4. 只有 N/A 项时不能 ACCEPT。** 协议要求 ACCEPT 至少有一个「实际执行」的 PASS finding，只有 N/A 不算实质检查。另：findings 或 comparisons 含 `UNVERIFIED` 禁止 ACCEPT；存在未解决 blocker/high FAIL 禁止 ACCEPT 与 CONDITIONAL；必要检查未完成时门禁为 INCOMPLETE。
