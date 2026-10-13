# Master Review Protocol

本文件定义本地 Codex 在 `MASTER_REVIEW` 状态下的课程规划协议，以及 Human 批准后的落盘边界。

Master Review 只负责全局语义规划；Python 只提供当前事实和 route，不替 Master 决定“下一步学什么”。

## Inputs

Master Review 必须同时考虑：

- `.runtime/context/MASTER_CONTEXT.md` 中的 Repo 当前事实；
- `00_global/master_outline.md`；
- `00_global/ability_profile.md`；
- 当前/历史 Topic、Gate、Evidence；
- Human 当前消息中的时间、兴趣、session-local 暂缓和现有 roadmap 顺序调整。

Human 当次偏好是有效规划输入，但不能隐式跳过尚未关闭的 Lesson / Handoff / learning-state transaction。

Human intent 分层：

- 仅“今天不想学当前 Topic”属于 session-local 暂缓，不要求长期 mutation；
- “接下来一段时间先学另一个既有 Topic”属于 roadmap-order change，可由 `learning.py master-review` 从 clean READY_FOR_TUTOR 发起只读 Review；
- 完全替换长期学习领域当前版本不支持自动迁移，不在本协议内处理。

## Read-only Review

在 Human 明确批准 MASTER PLAN 前：

- 不修改 `00_global/`；
- 不修改 `01_topics/`；
- 不修改 Human 工程源码；
- 不 commit。

只读 Review 结束后必须输出计划并停止，等待 Human 审批。

## MASTER PLAN Format

默认使用中文，固定结构如下：

```text
MASTER PLAN

触发原因
当前学习状态
Human 本次偏好 / 限制
规划决策
能力变化
Topic / Gate 变化
下一阶段目标
下一检查点
复验安排
决策理由
预计修改文件
```

没有变化的字段写“无”。

## Project-first planning

Human 要求改为项目驱动路线时，Master 仍使用相同固定 `MASTER PLAN`，只是要在 `规划决策` / `Topic / Gate 变化` 内明确系统里程碑的唯一 owner Gate、前置依赖、交付证据与 Ability 候选影响。

不要创建与 Gate 并行的 PASS 状态；不自动提升 `ability_profile`。旧 Topic 可 `PAUSED`、Gate 保留 `OPEN`，但新里程碑不得假装已经满足依赖。操作细节见 `PROJECT_GATE_WORKFLOW.md`。本扩展不削弱 **Read-only Review → Human Plan approval → diff review → Human commit approval**。

## Human Revision

Human 可以拒绝或调整计划，例如：

```text
这个方案先不批准。
今天不想开新 Topic，继续当前 Topic，但把 Lesson 控制在 30 分钟以内。
重新规划。
```

收到这种反馈后，Master 必须重新输出 MASTER PLAN；不能把反馈视为批准。

## Apply Approved Plan

只有 Human 明确批准后，Codex 才能应用刚刚批准的计划。

应用后必须：

1. 运行 `python tools/audit.py --route`；
2. 运行 `git status --short`；
3. 展示已跟踪 learning files 的真实 diff；
4. 如果出现 `??` 的新 `00_global/` / `01_topics/` 文件，普通 `git diff` 不会显示正文，必须额外完整展示这些新文件；
5. 等待 Human 审核；
6. 只有 Human 明确批准 commit 后才能提交；
7. commit 后重新运行 `python tools/learning.py status`。

Master Apply 不自动批准自己的计划，也不自动 commit。

## Review Signal Resolution

如果本次 Review 由 `state.master_review_required=true` 触发，MASTER PLAN 必须明确判定该 signal 为：

```text
RESOLVED
或
REMAINS
```

若 Human 批准的计划判定 `RESOLVED`，落盘时必须显式设置：

```text
master_review_required: false
master_review_reason: NONE
```

若为 `REMAINS`，保留合法非 `NONE` reason。不要让已处理的 signal 因遗漏清理形成 sticky Master Review。

## Topic Bootstrap

Base Repo 没有 Live Topic 时，第一次 MASTER PLAN 应至少明确：

- 首个 Topic；
- 第一条详细 Gate（通常为 `OPEN`）；
- 后续预建 Gate 是否为 `DRAFT`；
- 当前 Master Directive；
- `current_topic / current_action / master_checkpoint`；
- 预计创建/修改的文件。

Topic machine slug 同时用于目录、`current_topic` 和 Lesson/Gate/Evidence ID 前缀，只允许 ASCII 字母、数字、`_`、`-`；Human-facing 概念名如 `STA/XDC` 应使用 slug `STA_XDC`。

新 Topic 的四个长期文件为：

```text
01_topics/<TOPIC>/state.md
01_topics/<TOPIC>/gates.md
01_topics/<TOPIC>/evidence.md
01_topics/<TOPIC>/notes.md
```

`state.md / Master Directive` 只保存语义指令，例如：

```text
Objective:
...

Reason:
...
```

不要在 Master Directive 正文重复维护 `Action` / `Checkpoint`。这些机械 routing facts 的唯一来源分别是 `master_outline.current_action`、`master_outline.master_checkpoint` 与 `state.current_gate`；Tutor Context 需要展示时由 Python 动态组合。

Topic Bootstrap 应以 `03_templates/NEW_TOPIC/` 为结构骨架填值，不从零自由手写固定 section。落盘后的 `audit.py` 会检查后续 parser/apply 真正依赖的固定 section 是否存在且唯一。

## Gate Transition

Master 把 `state.current_gate` / `master_checkpoint` 推进到新 Gate 时，必须同步确认该 Gate 的状态适合下一步：

- 正式交给 Tutor 的 Gate 应为 `OPEN`；
- `DRAFT` / `RETIRED` 不能作为 Tutor 当前 Gate；
- `BLOCKED` 应保持/触发 Master Review，而不是继续开课；
- `PASSED` Gate 会由 route 重新进入 Master Review。
