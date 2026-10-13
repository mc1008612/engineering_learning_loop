# File Contracts

## Root

### README.md

面向 Human 的入口：系统用途、目录结构、从打开 Codex 开始的 Quick Start、日常学习与恢复操作。

README 是使用指南，不是 changelog，不维护当前 Topic/Gate 动态索引，也不承载完整协议细节。

### AGENTS.md

面向 Repo-local Codex：学习请求先检查 `learning.py status`、Human approval 边界、Next Action 引导、Master/Tutor Handoff 的正确入口与 commit 规则。

## 00_global

### master_outline.md

长期路线 + frontmatter 中唯一的全局路由事实：

```text
current_topic
current_action
master_checkpoint
```

不在正文重复维护第二份 Current Learning Focus。Master 提议、Human 批准后落盘；不记录 Lesson 历史。

### ability_profile.md

严格 `L0..L6` 粗索引。不记录半级、范围、置信度或 capability dimensions。

## 01_topics/<TOPIC>

长期学习事实固定分为：

```text
state.md
gates.md
evidence.md
notes.md
```

### state.md

Mutable snapshot。`Last Lesson` 每次正常 Close 覆盖；历史交给 Evidence + Git。

`Master Directive` 只保存语义 `Objective / Reason`。不要重复 `Action / Checkpoint` 等可由 frontmatter/current_gate 机械生成的 routing facts。

### gates.md

稳定详细 Gate 定义 + 增量 criterion/status/evidence refs。Mandatory/Stretch Criteria 只保存稳定定义文本；实际进度唯一由 `Criterion Progress` 表达。

### evidence.md

**Append-only ledger**。新 Handoff 只能追加。Amendment / Revalidation 也通过新 Entry + references 表达。

### notes.md

Curated knowledge。普通 Tutor Handoff 只向固定 durable section append 去重 bullet；明确维护任务可进一步整理。

## 02_specs

系统协议与数据合同，按职责拆分：

```text
DATA_MODEL.md                数据模型与 enum
FILE_CONTRACTS.md            文件职责
ROLE_PROTOCOL.md             Human / Tutor / Codex / Python 边界
TEACHING_CONTRACT.md         Web Tutor 教学原则
MASTER_REVIEW_PROTOCOL.md    Master Review / Human approval / Topic Bootstrap
TUTOR_CONTEXT_PROTOCOL.md    Tutor Context 的生成与自包含要求
TUTOR_HANDOFF_PROTOCOL.md    Web Tutor Handoff 的完整 runtime canonical protocol
LOCAL_HANDOFF_WORKFLOW.md    Downloads → validate → preview → apply 的本地流程
```

其中只有 `TUTOR_HANDOFF_PROTOCOL.md` 会被 Python 完整嵌入 Web Tutor Context。Web Tutor 不需要读取其他 Repo 路径。

### PROJECT_GATE_WORKFLOW.md

项目里程碑如何映射到既有 Topic/Gate/Evidence/Ability，且不突破 Master 审批与 Handoff 边界。

## 03_templates

### NEW_TOPIC

只用于 Human 已批准 Master Plan 后的 Topic Bootstrap，不是真实 Live State。

### prompts/tutor_start.md

Web Tutor 新会话的固定开课模板。`learning.py start-tutor` 填入 Context / Lesson / Handoff 文件名后复制到系统剪贴板。

## tools

### learning.py

学习流程入口：

- `status`；
- `master-review`（Human-requested roadmap reorder 的只读入口）；
- `start-tutor`；
- `collect-handoff`；
- `discard-lesson`。

`collect-handoff` 在 `PENDING_HANDOFF` 下还支持显式 `--replace --confirm <lesson_id>`，用于 Human 拒绝 Tutor 语义后收取 Tutor 的完整修订版；不会直接让本地 Codex改写课堂事实。

### handoff.py

Tutor Handoff 确定性事务：

- `validate`；
- `preview`；
- `apply`。

### audit.py

长期 Repo 一致性检查与机械 route；不处理 Pending Lesson。

### lib/

内部共享模块，不作为日常 CLI。统一实现 Repo parser、flow、Context、Handoff、render、本机 I/O。

## .runtime

Git ignored。本机临时事务与 convenience settings：

```text
.runtime/tutor_transaction.json
.runtime/context/
.runtime/prompts/
.runtime/incoming/
.runtime/handoff/
.runtime/local_settings.json
```

不是长期学习事实源。
