# Data Model

## Topic

长期能力域的 Live Instance。Base Repo 的 `01_topics/` 初始为空。

Status：`ACTIVE | PAUSED | COMPLETED`。

Machine Topic slug 同时用于 `01_topics/<slug>/`、`master_outline.current_topic` 和 Lesson/Gate/Evidence ID 前缀，只允许 ASCII 字母、数字、`_`、`-`。Human-facing 名称可以使用 `/`、空格等自然写法，但不能直接作为 path/ID。

## Gate

Tutor 的详细终端验收合同。

字段：

- ID；
- Objective；
- Prerequisites；
- Mandatory Criteria；
- Stretch Criteria；
- Allowed Assistance；
- Required Evidence；
- Pass Rule；
- Status；
- Evidence References。

Status：`DRAFT | OPEN | BLOCKED | PASSED | RETIRED`。

正式交给 Tutor 的 current Gate 必须为 `OPEN`。`DRAFT/RETIRED` 不能进入 Tutor；`BLOCKED` 必须触发/保持 Master Review；`PASSED` 由 route 进入 Master Review。

Gate 可跨多个 Lesson。历史 `PASSED` Gate 不因后续遗忘改成 FAIL；使用 Revalidation。

`Mandatory Criteria` / `Stretch Criteria` 只定义稳定验收条目，例如 `- C1 — ...`。真实进度只看 `Criterion Progress` 的 `NOT_VERIFIED | PARTIAL | VERIFIED`。普通 Lesson apply 不改写 Criteria 定义文本。

### Assistance

固定 enum：

`A0 < A1 < A2 < A3`

Gate 用：

```text
### Allowed Assistance
Maximum: `A1`
```

表达最终验收允许的最大辅助级别。

## Lesson

一次 Web Tutor 教学事务。不建立永久 Lesson ledger。

生成 Tutor Context 时同时原子建立 `.runtime/tutor_transaction.json`，由它唯一指认当前 Pending Lesson；历史 Context/Handoff 的 mtime 不参与状态判断。该 Lesson 必须通过以下之一结束：

1. `TUTOR_HANDOFF` 正常 apply；
2. Human 明确确认后显式 Discard。

在结束前禁止创建下一 Tutor Context。

Lesson Status：`COMPLETE | INTERRUPTED`。

`state.md` 只保留覆盖式 `Last Lesson`；详细历史交给 Evidence + Git。

## State

`state.md` = 当前快照。回答“新 Tutor 现在接手需要知道什么？”

允许：Master Directive、current gate、blockers、revalidation flags、Last Lesson、evidence anchors、open questions、review flag。

Master Directive 只保存当前 Topic 的语义 `Objective / Reason`；`Action / Checkpoint` 等 routing facts 不在正文重复存储。

禁止：完整实验过程、课堂流水账、长篇教材、完整复制 Evidence、历史 State 演化。

## Gates

`gates.md` = 稳定验收合同。Lesson 只增量更新 criterion/status/evidence refs。

Topic 默认完成规则：所有 mandatory Gates `PASSED` + Master Review 确认。

## Evidence

`evidence.md` = 历史事实账本。

Type：`LEARNING | ASSESSMENT | DEBUG | TRANSFER | REVALIDATION`

Result：`PASS | PARTIAL | FAIL`

Assistance：`A0 | A1 | A2 | A3`

### Append-only

新 Lesson 只能向末尾追加新的 Evidence Entry。

严禁：

- 用当前 Handoff 覆盖整个 `evidence.md`；
- 为了美化历史删除 FAIL；
- 静默重写旧观察。

旧结论被推翻：追加新的 Evidence，通过 `references` 指向旧 Evidence。

持久 Evidence Entry 使用 `evidence_entry` 字段：ID / Type / Result / Assistance / Gate / Lesson / References / Artifacts / Observation / Interpretation。

ID 只由 `### <TOPIC>-EXP-NNN` heading 定义；正文引用旧 ID 不参与 uniqueness。

## Notes

`notes.md` = 可复用个人知识库。

普通 Tutor Handoff 只能向固定 durable section 追加去重 bullet。Human/Master 在明确维护任务中可以进一步整理、合并、纠错。

一个 JSON list item 对应一个 Markdown bullet；item 内换行在落盘时归一为空格。

禁止 Lesson 流水账、Ability Level、完整复制 Evidence。

## Ability Profile

严格单值 `L0..L6`，是粗粒度排课索引。细节留在 Topic。只有 Human 批准后的 Master Plan 修改。

## Revalidation

高层学习发现旧能力似乎退化：

`TRANSFER Evidence → State flag REQUIRED → 最小短测 → REVALIDATION Evidence`

快速恢复则清 flag；确实退化则新建 `*-GATE-Rxxx`，Master 决定当前 Level 是否下降。历史 `PASSED` Gate 不篡改。

## Runtime transaction

`.runtime/` 不属于长期事实源，但承载本机尚未关闭的事务：

- `tutor_transaction.json`：唯一活跃 Tutor transaction identity；
- Tutor Context / Prompt；
- Pending Handoff 镜像；
- Master Review Context；
- `local_settings.json`。

任何新 Codex 对话通过 `learning.py status` 同时读取 Git 长期事实与 runtime Pending 状态，因此不依赖旧聊天恢复流程。

## Learning fact lifecycle

`Raw Observation → Tutor 分类 → Evidence 落账 → State 更新 → Notes 吸收可迁移知识 → 必要时 Master Review → Human review → Git 保存演进历史`
