状态名：**ERROR**（环境/执行错误，可细分 `environment_error`，须与 `FAILED` 严格区分）。

不能据此判定项目功能失败。所有报错均为 PermissionError（沙箱拒绝写系统临时目录与项目缓存），说明测试未进入业务断言阶段，属执行前置条件缺失（harness/infra 故障），不携带任何代码正确性信号。该次 run 应记为 invalid / inconclusive，不计入通过率与缺陷统计；待临时目录、缓存目录可写后重跑，仅当重跑中出现业务断言失败才记 `FAILED`。
