# Tutor Context Protocol

本文件定义 Web Tutor 每个新 Lesson 的 Repo 学习状态入口：`TUTOR_CONTEXT`，以及配套启动消息的教学规范装配。两者由同一次 `start-tutor` 产生。

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
teaching_mode: PROJECT | CONCEPT
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

- 当前 Gate 已选模式的只读 `teaching_mode` 标识（在 frontmatter 中）；
- 由 Master frontmatter + 当前 Topic State 动态生成的 Current Learning Focus；
- Ability baseline；
- Topic State；
- Current Gate；
- State/Gate 引用的 Evidence + recent Evidence；
- Topic Notes；
- **完整嵌入的 Tutor Handoff Protocol**，并用明确的 BEGIN/END marker 与 Context 其他内容分隔。

不自动塞整个工程源码、所有历史 Evidence、课程 PDF 或其他 Topic 全文；Shared Contract 与教学模式策略不在 Context 中重复出现。

## Tutor Start Prompt

Python 根据 `02_specs/TEACHING_MODE_ROUTE.md` 的当前 Gate 映射，选择合法的 `PROJECT` 或 `CONCEPT`：

- 启动消息自动装配 `TEACHING_CONTRACT.md` 的共同教学原则全文；
- 再装配 `TEACHING_PROJECT.md` 或 `TEACHING_CONCEPT.md` **恰好一份**；
- 最后添加 `03_templates/prompts/tutor_start.md` 中的 Lesson ID、Context 路径及 Handoff 文件名。

模式缺失、重复、非法或 Context 与路由不匹配时，Python 必须拒绝开课。Web Tutor 不需要访问本地 `02_specs/` 路径。

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

- lesson/topic/gate/teaching_mode；
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
