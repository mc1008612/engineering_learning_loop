# Role Protocol

本文件只定义任务边界，不要求为 Codex 固定一个永久“角色身份”。

## Human

学习者 + 最终批准者。

Human：

- 完成 Gate 所要求的独立工程判断、理解验证及实践任务；AI 可辅助编写实现；
- 提供真实观察和实验结果；
- 提供当次时间、兴趣与暂缓要求；
- 提出现有 roadmap 内的 Topic 顺序调整；
- 对超出当前系统范围的长期领域替换做最终决定；
- 审核 Tutor 判断、Master Plan、Git diff 与 commit。

### Human intent boundary

- “今天不想学当前 Topic”属于 session-local 暂缓，不自动改长期 Repo；
- “接下来一段时间先学另一个既有 Topic”属于 roadmap-order change，应进入只读 Master Review；
- “完全更换长期学习领域”当前版本不支持自动迁移，不应伪装成普通 Topic reorder。

## Web Tutor

只负责当前 Topic/Gate 的教学、实验设计、Gate 进展、Evidence 语义与 `TUTOR_HANDOFF`。

不排全局课程，不直接写 Repo，不修改 Ability Profile。

## Local Codex

Codex 是具有 CLI + Repo 文件权限的执行环境。具体行为由 Human 当前任务 + `AGENTS.md` + Repo/runtime 状态决定。

学习相关任务首先运行：

```bash
python tools/learning.py status
```

若为机械 `MASTER_REVIEW`：读取 `.runtime/context/MASTER_CONTEXT.md`（其中嵌入 `MASTER_REVIEW_PROTOCOL.md`），只读规划，输出中文 MASTER PLAN，等待 Human 批准。

若当前 clean `READY_FOR_TUTOR` 但 Human 明确要求调整现有 roadmap 顺序：运行 `python tools/learning.py master-review`，使用生成的 Master Context + Human 当前消息做同样的只读规划。该命令不改变长期 route。

若为 `PENDING_HANDOFF`：使用 `handoff.py preview/apply`，不要自由解释 Delta 后手改 Topic 四文件。

Human preview 后若不同意 Tutor 的课堂语义判断，应回原 Web Tutor 基于完整 Lesson 对话商议，让 Tutor 输出完整修正版，再通过 `learning.py collect-handoff --replace --confirm <lesson_id>` 收取；本地 Codex 不代替 Tutor 重写课堂事实。

若为 Repo maintenance：按普通开发任务修改工具/文档，不需要强行套用课程 Master 概念。

## Deterministic tools

Python 负责：

- Repo audit / route；
- 由 `.runtime/tutor_transaction.json` 唯一指认的串行 Pending Lesson 状态；
- Context identity/hash/fingerprint；
- Handoff schema/enum/Delta；
- Evidence ID 连续性；
- Gate PASS 的 Assistance ceiling；
- 已获 Handoff 授权范围内的确定性 mutation。

Python 不判断：

- Human 是否真正掌握内容；
- 下一门课程应该是什么；
- Ability 是否应该升级；
- Human 今天是否想临时换方向。

这些语义由 Tutor/Master + Human 决策。
