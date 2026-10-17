# Local Handoff Workflow

本文件定义 Web Tutor 下载 Handoff 后，本地 Codex/Python 如何收取、验证、预览、应用和恢复。

它**不会嵌入 Web Tutor Context**；Web Tutor 不需要知道本地文件搬运和 Git 审批流程。

## Collect

正常收取：

```bash
python tools/learning.py collect-handoff
```

默认只查找当前 Pending Lesson 的精确 `handoff_filename`。

如果浏览器因重复下载产生 `(1)` 等文件，脚本不自动猜。Human/Codex 明确确认候选后可指定：

```bash
python tools/learning.py collect-handoff --source "TUTOR_HANDOFF_... (1).md"
```

`--source` 只接受配置的 Downloads 目录中的文件名。

## Validate Before Promote

收件顺序固定为：

```text
Downloads source
→ copy 到 .runtime/incoming/ 临时文件
→ validate
→ PASS 后原子 promote 到 .runtime/handoff/<expected filename>
```

如果 validate FAIL 或 STALE：

- 删除临时 incoming 文件；
- 不创建正式 `.runtime/handoff/<expected>`；
- 状态继续保持 `PENDING_LESSON`；
- Human 可以让 Tutor 重做 Handoff 后再次 collect；
- 不需要手工删除 runtime 正式 Handoff 才能恢复。

正式 Handoff 一旦 promote，状态变成：

```text
PENDING_HANDOFF
```

## Human Semantic Review / Tutor Revision

`PENDING_HANDOFF` 进入 `preview` 后，Human 如果不同意 Tutor 对课堂事实的语义判断，例如：

- Assistance 等级；
- Result；
- Criterion Progress；
- Observation / Interpretation；
- Notes 是否准确；

不要把本地 Codex 当作第二个 Tutor，也不要把手工编辑 `.runtime/handoff/` 作为正常流程。

Human 应回到原 Web Tutor，结合完整课堂对话讨论并让 Tutor 输出**完整修正版 Handoff**。浏览器通常会得到 `(1)` 等文件名。

当 Notes Delta 的 `Engineering Rules` 含 `DECISION:` 条目时，本地 Master/Codex 在 Preview 阶段辅助核对：该决定是否经过 Human 明确认可、是否与既有决定冲突。由 Human 审核后才允许 Apply；若记录失实，通过上面的 Tutor 修订路径纠正。无需增加 Handoff 字段或状态。

确认候选确实是当前 Lesson 的 Tutor 修订版后，用：

```bash
python tools/learning.py collect-handoff \
  --source "TUTOR_HANDOFF_... (1).md" \
  --replace \
  --confirm <lesson_id>
```

规则：

- 只允许在 `PENDING_HANDOFF`；
- 必须显式指定 `--source`；
- `--confirm` 必须精确匹配当前 Lesson ID；
- 修订版仍先进入 `.runtime/incoming/` 并重新 validate；
- validate PASS 后才原子替换正式 Handoff；
- Context/Prompt 与长期 State/Gate/Evidence/Notes 都不改变；
- 状态仍保持 `PENDING_HANDOFF`，Human 必须重新 preview。

修订版 validate FAIL / STALE 时，当前正式 Handoff 保持不变。

## Validate / Preview / Apply

独立验证：

```bash
python tools/handoff.py validate .runtime/handoff/TUTOR_HANDOFF_<lesson_id>.md
```

预览确定性 patch：

```bash
python tools/handoff.py preview .runtime/handoff/TUTOR_HANDOFF_<lesson_id>.md
```

Human review 后实际落盘：

```bash
python tools/handoff.py apply .runtime/handoff/TUTOR_HANDOFF_<lesson_id>.md
```

`apply` 只修改当前 Topic：

- `state.md`；
- `gates.md`；
- `evidence.md`；
- `notes.md`。

不会修改 `ability_profile.md`、`master_outline.md`、工程源码，也不会 commit。

post-apply audit 失败时自动回滚本次写入。

## Pending State

正常状态链：

```text
READY_FOR_TUTOR
→ start-tutor（创建 Context/Prompt + tutor_transaction.json）
→ PENDING_LESSON
→ collect-handoff
→ PENDING_HANDOFF
→ preview / Human review / apply
→ PENDING_LEARNING_CHANGES
→ Human diff review / commit
→ status
```

Pending Lesson 只有两个结束出口：

1. Handoff 正常 apply：长期 `state.last_lesson_id` 写入本 Lesson ID，并清除 `tutor_transaction.json`；
2. Human 明确确认后 `discard-lesson --confirm <lesson_id>`：删除当前 Context/Prompt 与 transaction pointer，不改长期学习事实。

活跃事务只由 `.runtime/tutor_transaction.json` 指认；历史 Context/Handoff 的 mtime 不参与判断。在结束前 `start-tutor` 必须拒绝生成下一 Context。

## Pending Transaction 与并行 learning-state 修改

Tutor Context 创建后，`00_global/`、`01_topics/` 参与 fingerprint 的学习事实，以及当前 Gate 的 Teaching Mode Route，不应在本 Lesson Close 前并行更改。

如果 `PENDING_LESSON` / `PENDING_HANDOFF` 期间检测到这些 learning files 或 Mode Route 的未提交变化：

- Pending Lesson/Handoff 状态优先，不把它误报成普通 `PENDING_LEARNING_CHANGES`；
- 不要 commit 这些并行修改；
- 若 Lesson 已经发生，先另存并恢复开课时的长期学习事实与 Mode Route，再 collect / preview / apply 当前 Handoff；
- 若 Human 明确确认 Lesson 实际从未发生，仍允许显式 Discard；Discard 后再处理这些并行修改。

否则当前 Context/Handoff 会因为 fingerprint 改变而 `STALE`。

## Fingerprint / Stale

Tutor Context 对参与判断的长期学习文件记录 SHA256 fingerprint；Handoff 原样带回。

Validator：

- identity/context/hash/fingerprint/schema/enum/Delta 合法 → PASS；
- 相关学习状态文件在开课后发生变化 → `STALE`；
- 其他协议错误 → FAIL。

工程源码变化本身不让 Handoff stale。
