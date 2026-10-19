# Tutor Handoff Protocol

这是 Web Tutor 在 Lesson 结束时生成 `TUTOR_HANDOFF` 的**完整运行时协议**。

本协议会被 Python 完整嵌入当前 Tutor Context。Web Tutor 只依赖当前 Context，不读取任何 Repo 内路径，也不依赖此前 Tutor 聊天历史。

## Output Rule

Lesson 结束时只输出一个完整 `TUTOR_HANDOFF` Markdown 文件。

- 下载文件名必须精确使用当前 Tutor Context frontmatter 的 `handoff_filename`；
- 不输出替换版 Repo 文件；
- 不修改 Ability Profile；
- 不重新推导 lesson/topic/gate/context identity，必须从当前 Context 原样带回；
- 语义由 Tutor 判断，结构必须严格遵守下面协议。

## Required Frontmatter

Handoff 必须以如下 frontmatter 开始：

```yaml
---
schema: tutor_handoff
delta_format: structured_json
lesson_id: <原样复制 Tutor Context 的 lesson_id>
lesson_status: <COMPLETE | INTERRUPTED>
topic: <原样复制 Tutor Context 的 topic>
gate: <原样复制 Tutor Context 的 current_gate>
master_review_required: <true | false>
master_review_reason: <见下方 enum>
context_file: <原样复制 Tutor Context 的 context_file>
context_sha256: <原样复制 Tutor Context 的 context_sha256>
fingerprint_state: <原样复制 Tutor Context>
fingerprint_gates: <原样复制 Tutor Context>
fingerprint_evidence: <原样复制 Tutor Context>
fingerprint_notes: <原样复制 Tutor Context>
fingerprint_master_outline: <原样复制 Tutor Context>
fingerprint_ability_profile: <原样复制 Tutor Context>
---
```

`lesson_status`：

```text
COMPLETE | INTERRUPTED
```

`master_review_reason`：

```text
NONE
CURRICULUM_CHECKPOINT
POSSIBLE_LEVEL_CHANGE
TOPIC_LIFECYCLE
CROSS_TOPIC_DEPENDENCY
REVALIDATION
OTHER
```

耦合规则：

- `master_review_required: false` → `master_review_reason: NONE`；
- `master_review_required: true` → reason 必须为合法且非 `NONE` 的 enum。

## Required Sections

Frontmatter 后必须各自且只出现一次以下五个二级标题；推荐按下面顺序输出：

```text
## Last Lesson
## State Delta
## Gate Delta
## Evidence To Append
## Notes Delta
```

五个 required section 各出现一次，标题名称与拼写按上面清单保持原样。Validator 按标题解析，不依赖它们的相对顺序。

## Last Lesson

Human 可读摘要，至少包含这些固定 label：

```text
Focus:
Work:
Outcome:
Gate Progress:
Evidence:
Suggested Local Next:
```

内容可以多行，并真实反映本 Lesson；未验证能力按实际状态记录。

## State Delta

State Delta 修改范围限定为当前 Topic State 的学习快照；`topic/status/current_gate` 与 Ability 保持原值。

输出一个 fenced JSON object：

```json
{
  "set": {
    "passed": [],
    "in_progress": [],
    "not_yet_verified": [],
    "blockers": [],
    "revalidation_flags": [],
    "open_questions": []
  },
  "add_evidence_anchors": []
}
```

规则：

- State Delta 顶层只允许 `set` 与 `add_evidence_anchors`；任何额外顶层 key 都是协议错误，不会被静默忽略；
- `set` 内各 key 均可省略；出现的 key 表示替换对应列表；
- list item 使用简洁 durable 文本；
- `add_evidence_anchors` 只追加 Evidence ID，不删除已有 anchor；
- `master_review_required/reason/last_lesson_id` 不在这里输出，由 Handoff identity 机械写入 State frontmatter。

## Gate Delta

只允许修改**当前 Gate** 的：

- Status；
- Criterion Progress；
- Evidence References。

输出一个 fenced JSON object：

```json
{
  "status": "OPEN",
  "criteria": {
    "C1": "PARTIAL"
  },
  "add_evidence_references": []
}
```

允许的 Gate status：

```text
OPEN | BLOCKED | PASSED
```

Criterion status：

```text
NOT_VERIFIED | PARTIAL | VERIFIED
```

只能使用 Current Gate 中真实存在的 criterion ID。

`Mandatory Criteria` / `Stretch Criteria` 是稳定 Gate 定义，不携带 checkbox 状态；实际进度只通过 `Criterion Progress` 表达。Tutor Handoff 不改写 Criteria 定义文本。

如果本次 Delta 的 resulting Gate status 为 `BLOCKED`：

- `master_review_required` 必须为 `true`；
- `master_review_reason` 必须使用合法且非 `NONE` 的原因；
- `Suggested Local Next` 应说明需要 Master/Human 决策的 blocker，而不是继续下一 Lesson。

### Gate PASSED 语义

只有在 Tutor 判断本 Gate 已满足验收语义时才请求 `PASSED`。Python 还会机械检查：

1. Mandatory Criteria 全部 `VERIFIED`；
2. Evidence References 非空且真实存在；
3. 至少一条被引用 Evidence 属于当前 Gate；
4. 该 Evidence `Result=PASS`；
5. 该 Evidence 的 Assistance 不高于 Gate `Allowed Assistance / Maximum`。

Assistance 顺序：

```text
A0 < A1 < A2 < A3
```

高辅助学习过程 Evidence 可以存在；最终验收必须至少有一条满足 Assistance ceiling 的 PASS Evidence。

## Evidence To Append

如果本 Lesson 没有值得进入长期历史的新 Evidence，输出：

```text
NONE
```

有新 Evidence 时输出一个 fenced JSON array。第一条 ID 必须使用当前 Tutor Context 的 `next_evidence_id`，后续 ID 连续递增。

```json
[
  {
    "id": "<使用 Context 的 next_evidence_id>",
    "title": "<简短标题>",
    "type": "ASSESSMENT",
    "result": "PASS",
    "assistance": "A0",
    "gate": "<当前 gate>",
    "lesson_id": "<当前 lesson_id>",
    "observed_at": "<可选 ISO 时间>",
    "references": [],
    "artifacts": [],
    "observation": "<本 Lesson 实际观察到的表现/实验结果>",
    "interpretation": "<这条 Evidence 支撑什么判断，以及不支撑什么>"
  }
]
```

Enum：

```text
Type       = LEARNING | ASSESSMENT | DEBUG | TRANSFER | REVALIDATION
Result     = PASS | PARTIAL | FAIL
Assistance = A0 | A1 | A2 | A3
```

规则：

- `id/title/type/result/assistance/gate/lesson_id/observation/interpretation` 必填；
- `gate` 必须等于当前 Gate；
- `lesson_id` 必须等于当前 Lesson；
- `references` 指向已经存在的 Evidence，或本数组中**更早定义**的新 Evidence；引用顺序保持时间先后（自引用与后向引用视为无效）；
- `artifacts` 是可选列表；
- PASS Evidence 以真实观察为依据；Lesson COMPLETE 只记录课程完成状态。

## Notes Delta

普通 Tutor Handoff 只允许向固定 durable section append 去重条目：

```json
{
  "append": {
    "Durable Mental Models": [],
    "Engineering Rules": [],
    "Debug Checklist": [],
    "Common Failure Modes": [],
    "References Worth Reusing": []
  }
}
```

一个 JSON item 对应一个 Markdown bullet；多个独立知识点分别成 item，每个字符串保持单条 bullet 的粒度。

## Final Checklist

输出前自检：

- frontmatter identity/hash/fingerprints 是否从当前 Context 原样带回；
- `lesson_status` 与实际 Lesson 是否一致；
- `master_review_required/reason` 是否符合耦合规则；
- resulting Gate 为 `BLOCKED` 时是否已经请求 Master Review；
- 五个 required section 是否齐全、标题完全一致且各自只出现一次；
- State/Gate/Notes 是否只用了允许字段；
- Evidence ID 是否从 Context 的 `next_evidence_id` 开始连续；
- Evidence references 是否只指向更早 Evidence；
- Gate PASS 是否有符合 Assistance ceiling 的真实 PASS Evidence；
- 未验证内容是否仍保留为 PARTIAL / NOT_VERIFIED，而不是为了推进流程强行通过。
