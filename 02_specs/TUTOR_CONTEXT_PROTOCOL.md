# Tutor Context Protocol

本文件定义 Web Tutor 每个新 Lesson 唯一收到的 Repo 状态入口：`TUTOR_CONTEXT`。

Tutor Context 由：

```bash
python tools/learning.py start-tutor
```

间接生成。生成前必须满足：

```text
CURRENT_STATE: READY_FOR_TUTOR
```

如果存在 Pending Lesson、Pending Handoff 或尚未 review/commit 的 learning-state diff，Python 必须拒绝创建新 Context。

成功生成 Context/Prompt 时，`learning.py start-tutor` 同时原子建立 `.runtime/tutor_transaction.json`。状态机只认该显式 transaction identity；历史 Context 文件的创建/修改时间不参与 Pending Lesson 判断。

## Frontmatter

至少包含：

```text
schema: tutor_context
lesson_id: ...
topic: ...
current_gate: ...
next_evidence_id: ...
context_file: .runtime/context/TUTOR_CONTEXT_....md
handoff_filename: TUTOR_HANDOFF_<lesson_id>.md
context_sha256: ...
fingerprint_state: ...
fingerprint_gates: ...
fingerprint_evidence: ...
fingerprint_notes: ...
fingerprint_master_outline: ...
fingerprint_ability_profile: ...
```

## Body

包含：

- Teaching Contract；
- 由 Master frontmatter + 当前 Topic State 动态生成的 Current Learning Focus；
- Ability baseline；
- Topic State；
- Current Gate；
- State/Gate 引用的 Evidence + recent Evidence；
- Topic Notes；
- **完整嵌入的 Tutor Handoff Protocol**，并用明确的 BEGIN/END marker 与 Context 其他内容分隔。

不自动塞整个工程源码、所有历史 Evidence、课程 PDF 或其他 Topic 全文。

## Canonical Handoff Protocol

Web Tutor 完成本 Lesson 所必需的 Handoff 输出规则只有一个长期事实源：

```text
02_specs/TUTOR_HANDOFF_PROTOCOL.md
```

`context.py` 必须读取该文件并把其完整正文嵌入每一份 Tutor Context，并使用：

```text
<!-- BEGIN:TUTOR_HANDOFF_PROTOCOL -->
...
<!-- END:TUTOR_HANDOFF_PROTOCOL -->
```

作为明确运行时边界。Web Tutor 不需要、也不应尝试访问 Repo 内路径。

如果 canonical protocol 文件缺失、为空或缺少关键协议标题，Context 生成必须失败，而不是退化为路径引用或 Python 内硬编码协议。

## Context SHA256

`context_sha256` 保护整个 Tutor Context，而不是只保护 body。

计算规则：

1. 读取完整 Context 文本；
2. 将唯一的 `context_sha256: <实际值>` canonicalize 为固定占位值；
3. 对其余完整 frontmatter + body 的 UTF-8 文本计算 SHA256。

因此以下 metadata 的手工修改也会造成 hash mismatch：

- lesson/topic/gate；
- `next_evidence_id`；
- `context_file`；
- `handoff_filename`；
- fingerprints；
- 内嵌的 Handoff Protocol。

Validator 另外从真实 `evidence.md` 重算 `next_evidence_id`，不单独信任 Context metadata。

## Handoff 文件名

每个 Tutor Context 明确给出：

```text
handoff_filename: TUTOR_HANDOFF_<lesson_id>.md
```

Web Tutor Lesson Close 时必须使用这个精确文件名下载 Markdown Handoff。

文件名负责定位；Context hash / fingerprints 负责内容绑定。
