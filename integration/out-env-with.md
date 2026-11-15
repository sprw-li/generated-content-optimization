# 权限错误下的执行状态判定（依据 SKILL.md + protocol.md v3.2）

**执行状态：`ENVIRONMENT_BLOCKED`**（五值之一：`EXECUTED_PASS` / `EXECUTED_FAIL` / `ENVIRONMENT_BLOCKED` / `NOT_RUN` / `NOT_APPLICABLE`）。相应审查项记 `UNVERIFIED`（未完成或被环境阻塞），总门禁为 `INCOMPLETE`。

**不能据此判定项目功能失败。** 理由：

1. protocol.md：「环境权限/依赖失败不是项目逻辑失败；必要检查未完成时门禁 INCOMPLETE」。PermissionError 全部来自沙箱拒绝写系统临时目录与项目缓存目录，属环境限制，非项目逻辑缺陷。
2. SKILL.md 禁止条款明列「把权限错误当逻辑失败」。要判 `EXECUTED_FAIL`，须有实际执行的业务断言失败；本次零业务断言失败，故无 FAIL 证据。
3. 证据规则：`exit 0` 不是充分证据，`exit 1` 也不是项目失败证据——退出码须结合计数、结构化输出判读。测试根本没跑起来（收集/写缓存阶段即被拒），既未证明通过，也未证明失败。
4. 正确处置：解除沙箱写权限或指定可写 tmp/缓存目录后重跑，取得真实断言结果再定 `EXECUTED_PASS`/`EXECUTED_FAIL`；在此之前不得 ACCEPT，也不得据此 REJECT 项目功能。
