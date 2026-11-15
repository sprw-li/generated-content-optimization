# 评审框架状态机（凭通用理解作答，未读取任何本地文件）

**审查项状态（Item Status）**：`PASS`、`FAIL`、`N/A`（常见扩展：`PENDING`、`UNVERIFIED`）。

**执行状态（Execution Status）**：`COMPLETED`、`PARTIAL`、`BLOCKED`、`FAILED`。

**总门禁（Overall Gate）**：`ACCEPT`、`REJECT`、`NEEDS_REVIEW`。

**只有 N/A 项时能否 ACCEPT：不能。** `N/A` 只表示"不适用"，不构成任何通过证据；全部为 `N/A` 即有效覆盖率为零，此时 `ACCEPT` 属于空真通过（vacuous pass），会把未验证风险直接放行。正确结果应为 `NEEDS_REVIEW`（完全无可判项时也可 `REJECT`），须补充至少一个可核验的 `PASS` 项后才可进入 `ACCEPT`。

> 注：以上枚举名为通用约定，未与任何本地规范或 skill 文档核对。
