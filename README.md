# Engineering Learning Loop

Engineering Learning Loop 是一个以 Git Repo 为长期事实源的个人工程学习闭环。

日常不需要记状态机细节。对 Codex 直接说你想做什么；学习相关请求中，Codex 会先运行：

```bash
python tools/learning.py status
```

然后告诉你当前状态、你的请求是否符合当前 Next Action，以及接下来需要你做什么。

---

## Quick Start

### 第一次使用

把本目录作为 Codex 项目根目录。若还没有 Git：

```bash
git init
git add .
git commit -m "meta: initialize engineering learning loop"
```

然后对 Codex 说：

```text
我想开始今天的学习。
```

### Master Review

需要规划时，Codex 会给出完整中文 `MASTER PLAN`。

你可以批准、拒绝或要求重做。**只有明确批准后**，Codex 才能修改长期学习文件；修改完成后由你 review，再批准 commit。

### 开 Web Tutor

状态允许开课时，对 Codex 说：

```text
开始本课。
```

Codex 会生成 Tutor Context 和 Start Prompt。你只需要：

1. 在 Web Tutor 上传 Context；
2. 粘贴 Prompt；
3. 追加本课偏好；
4. 手动发送。

### Lesson 结束

让 Web Tutor 按 Context 中的协议输出完整 `TUTOR_HANDOFF`，下载后告诉 Codex课程结束。

Codex 会收取并 validate，然后给你 preview。你主要检查 Tutor 对课堂事实的判断是否准确，例如 Evidence、Assistance、Criterion Progress 和 Notes。

若不认可课堂语义，回原 Tutor 商议并让它重新输出完整 Handoff；不要把本地 Codex 当作第二个 Tutor改写课堂事实。

确认 preview 后批准 apply；再 review Git diff，最后批准 commit。

---

## Human 意图的三个边界

下面三句话不是同一种事务：

```text
“我今天不想学 STA。”
```

这是 **session-local 暂缓**。不需要修改长期计划；今天可以什么都不做。

```text
“我想在继续 STA 之前，先学一段时间 CDC。”
```

这是 **现有 roadmap 内的 Topic 顺序调整**。Codex 会先做只读 Master Review；Human 批准新的 MASTER PLAN 后，才允许修改 `master_outline` / Topic 状态。

```text
“我完全不想学 FPGA 了，我想改学 Java 转码。”
```

这是 **长期学习领域整体替换**。当前版本不处理这种根级迁移，也不会自动改写现有学习 Repo。

---

## 文件修改边界

### 日常可以直接修改

- 你正在学习过程中产生的工程源码、工程配置、report、实验文件；
- 明确的 Repo maintenance 任务中的 `README.md`、`AGENTS.md`、`02_specs/`、`03_templates/`、`tools/`。

这些系统文件的修改属于维护工作，不等于课程学习状态更新。

### 需要经过 Master Plan 批准后修改

- `00_global/master_outline.md`
- `00_global/ability_profile.md`
- Master 调度涉及的 `01_topics/<TOPIC>/state.md`
- Master 调度涉及的 `01_topics/<TOPIC>/gates.md`
- 新 Topic 的 `state.md / gates.md / evidence.md / notes.md`

Human 的自然语言要求不会直接写进 `master_outline.md`；它先作为 Master Planning 输入，只有批准后的规划结果才落盘。

### 普通 Lesson 不要直接手改

- 当前 Topic 的 Gate Progress / Evidence / Last Lesson：正常通过 Tutor Handoff → preview → apply 更新；
- 已存在的 `evidence.md` 历史 Entry：Evidence 是 append-only；
- `.runtime/handoff/*.md` 的课堂语义：有异议时回原 Tutor生成完整修订版；
- 已生成的 `TUTOR_CONTEXT_*.md` / Tutor Start Prompt；
- `.runtime/tutor_transaction.json`、`.runtime/incoming/` 等 runtime 内部事务文件。

`.runtime/` 是 Git ignored 的本机事务区，不是长期学习事实源。

---

## 常用命令

查看真实状态：

```bash
python tools/learning.py status
```

Human 明确要求调整**现有 roadmap 顺序**时，由 Codex使用只读入口：

```bash
python tools/learning.py master-review
```

它只生成 Master Context，不修改长期文件，也不会创建持久 review flag。

开课：

```bash
python tools/learning.py start-tutor
```

首次可同时保存 Tutor URL / Downloads 目录：

```bash
python tools/learning.py start-tutor \
  --url "https://YOUR_TUTOR_URL" \
  --downloads-dir "~/Downloads"
```

收取 Handoff：

```bash
python tools/learning.py collect-handoff
```

预览 / 应用：

```bash
python tools/handoff.py preview .runtime/handoff/TUTOR_HANDOFF_<lesson_id>.md
python tools/handoff.py apply   .runtime/handoff/TUTOR_HANDOFF_<lesson_id>.md
```

如果 Lesson 实际完全没有发生，Human 明确确认后可 Discard：

```bash
python tools/learning.py discard-lesson --confirm <LESSON_ID>
```

发生过真实学习但没有完成课程时，不要 Discard；让 Tutor 用 `lesson_status: INTERRUPTED` 正常 Close。

---

## 目录

```text
engineering_learning_loop/
├── 00_global/        # 长期路线与粗粒度能力
├── 01_topics/        # Topic State / Gates / Evidence / Notes
├── 02_specs/         # 系统协议
├── 03_templates/     # 固定结构模板
├── tools/            # CLI 与内部实现
└── .runtime/         # Git ignored；本机事务、Context、Handoff、配置
```

完整协议与 Agent 行为约束分别位于 `02_specs/` 和 `AGENTS.md`；README 不承担 changelog 或内部实现说明。
