# 真实项目记录回放：v3 补充验收

日期：2026-11-12。

## 为什么做

前一轮 11 项测试是合成状态合同；本轮用此前五个真实项目审查中实际观察到的失败，检验报告能否保持项目隔离、快照边界和未修复状态，而不是继续润色 skill。

## 输入

`real_project_eval.py` 生成五份独立记录到 `records/`：

- dsh-council：最后验证无归档结果；
- Project5：斜金刚石超胞被错误视为 conventional；
- Project6：qNEHVI baseline 不走 X_baseline 后验；
- Project7：主入口不产出协议 H1/H3；
- Project8：P-G2-6 budget=False 与通过叙述冲突。

这些是此前实际审查证据的最小机器可读摘录，不是重新运行五项目，也不是完整审查报告。

## 发现与修复

首次运行因 harness 将 validator 错定位为 `v3/../shared` 而非 `v3/shared`，五条均 exit 2。修复 `real_project_eval.py` 的 `VALIDATOR` 路径后重跑。这是验收脚本路径错误，不是被评项目失败，也不是正式 skill 的缺陷。

## 最终实测

命令：`D:\App\Python3.14\python.exe review-skill-system\v3\real_project_eval.py`

结果：五份记录分别 exit 0，findings=1、gate=REJECT；最终 exit 0。所有 remediation.verification=NOT_RUN，无 RESOLVED。

## 结论与边界

- 本轮没有暴露需要修改七 skill 公共合同的新 blocker/high，因此不制造 v4。
- 现有 11 项对抗测试和本次五项目最小记录共同构成当前可执行验收。
- 每项目仅一条代表性发现，未覆盖全部缺陷、权限错误、GitHub 参照和正向证据。
- 结构 PASS 仅表示记录满足 v3 合同，不表示项目通过；五项目记录总门禁仍 REJECT。
- 无新真实失败前停止自我修改。
