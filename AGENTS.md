# Engineering Learning Loop — Codex Instructions

本 Repo 的长期学习事实来自 Git 文件；当前未完成 Tutor Lesson 的身份来自 `.runtime/tutor_transaction.json`。不要依赖旧 Codex/Tutor 聊天历史或历史 artifact 的文件时间戳恢复状态。

## 1. 学习请求先检查状态，再核对 Human 当前意图

Human 的请求涉及开始/继续学习、课程规划、开课、Lesson Close、Handoff 或“下一步做什么”时，先运行：

```bash
python tools/learning.py status
```

随后在回复中明确：

1. `CURRENT_STATE`；
2. 当前原因；
3. Human 当前请求是否符合机械 `NEXT_ACTION`；
4. 若不符合，是合法的 Human 意图覆盖、需要先处理更高优先级事务，还是当前版本不支持；
5. Human 现在真正需要做什么。

Repo/runtime 的实际状态优先于 Human 对流程位置的假设。

## 2. Human 请求分类

不要把所有“我今天不想学当前 Topic”都当作长期计划变更。

### A. Session-local preference

例如：

```text
今天不想学 STA。
今天只有 20 分钟。
本课先让我自己判断，不要过早提示。
```

这类请求不自动修改长期 roadmap。Human 仅仅今天不想学当前 Topic 时，可以不开始任何 Lesson，长期 Repo 保持不变。

### B. Roadmap-order change

例如：

```text
接下来一段时间先暂停 STA，先学 CDC。
我想在继续 STA 前先完成另一个已有 Topic。
请重新调整现有 Topic 顺序。
```

这是现有学习领域内的调度变更。若当前有 `PENDING_LESSON / PENDING_HANDOFF / PENDING_LEARNING_CHANGES`，先解决该事务；不能跳过。

若当前 clean `READY_FOR_TUTOR` 或已经 `MASTER_REVIEW`，运行：

```bash
python tools/learning.py master-review
```

这是只读入口：使用生成的 Master Context + Human 当前消息输出完整中文 `MASTER PLAN`。Human 批准前不得修改 `00_global/`、`01_topics/` 或 `02_specs/TEACHING_MODE_ROUTE.md` 的规划映射。

Human 原话不是直接写入 `master_outline.md` 的数据。只有 Human 批准后的规划结果才落盘。

### C. Long-term domain replacement

例如：

```text
我不想再学 FPGA，改成完全不同的 Java 转码学习体系。
```

当前版本不处理根级学习领域迁移。不要把它伪装成普通 Topic reorder，也不要自动重写 Ability/Profile/Topic universe；明确告诉 Human 当前 Repo 不支持该事务。

## 3. Human 必须保留的控制权

Human 负责：真实学习行为、当次偏好、Master Plan 批准/驳回、Tutor Handoff 语义纠偏、learning-state diff 审核、commit 最终批准，以及是否 Discard 一个实际没有进行的 Pending Lesson。

任何 commit 都需要 Human 明确批准。

## 4. Master Review

机械 route 为 `MASTER_REVIEW` 时，使用 `.runtime/context/MASTER_CONTEXT.md`。Human-requested roadmap review 则使用 `learning.py master-review` 生成的同一类只读 Context。

输出固定结构中文 `MASTER PLAN`，然后停止等待 Human 批准。批准前不修改长期学习文件、不 commit。

Human提出修改但未批准时，重新规划，不落盘。

### review signal 收尾

若本次 Review 是因为 `state.master_review_required=true`，Master Plan 必须明确判断该 signal：

```text
RESOLVED
或
REMAINS
```

若 `RESOLVED`，批准后落盘时必须显式写：

```text
master_review_required: false
master_review_reason: NONE
```

若 `REMAINS`，保留合法非 `NONE` reason。不要让已解决 signal 因忘记清理而形成 sticky review loop。

### Teaching Mode 规划

Master 为将要交给 Tutor 的每个新 Gate 选择 `PROJECT` 或 `CONCEPT`，在 MASTER PLAN 说明原因，经 Human 批准后维护 `02_specs/TEACHING_MODE_ROUTE.md` 的 Gate→Mode 映射。该文件虽在 Specs，其课程配置变更仍遵守 Master Plan → diff review → Human commit approval；不要写到 master_outline frontmatter。

### Topic / Gate 修改

Topic machine slug 同时用于目录、`current_topic`、Lesson/Gate/Evidence ID 前缀，只允许：

```text
A-Z a-z 0-9 _ -
```

例如 Human-facing “STA/XDC” 使用 slug `STA_XDC`。

新建 Topic 时以 `03_templates/NEW_TOPIC/` 为固定结构骨架。`state.md / Master Directive` 只写语义 `Objective / Reason`，不要重复 `Action / Checkpoint` routing facts。

Master Plan 批准后落盘，至少运行：

```bash
python tools/audit.py --route
git status --short
git diff --stat
git diff
```

新 learning files 为 `??` 时，普通 `git diff` 看不到正文；必须额外完整展示后再请求 Human commit approval。

## 4.5 项目里程碑兼容方式

Human 想通过 FPGA→Host 等系统项目推进能力地图时，使用 `02_specs/PROJECT_GATE_WORKFLOW.md` 的“项目里程碑 → 唯一 owner Topic/Gate → Handoff Evidence → Master Ability Review”映射；不要另建一套自动 Level 或伪造 PASS。路线本身仍由 Human 批准后的 Master Plan 决定；真实学习事务先查 status，若存在 `PENDING_LEARNING_CHANGES` 不能跳过。

## 5. Tutor Lesson transaction

只有 `READY_FOR_TUTOR` 且 Human 明确开课时才运行：

```bash
python tools/learning.py start-tutor
```

成功后会建立唯一 `.runtime/tutor_transaction.json`。它只保存当前事务 identity；历史 Context/Handoff 的 mtime 不参与状态判断。

向 Human说明：上传 Context、粘贴 Prompt、追加本课偏好、手动发送。启动 Prompt 已装配共同教学合同和选中的 Project/Concept 规范；Context 已自包含 Tutor Handoff Protocol，不要求额外上传 Specs。

## 6. 收取与纠正 Tutor Handoff

`PENDING_LESSON` 正常收取：

```bash
python tools/learning.py collect-handoff
```

Downloads → `.runtime/incoming/` → validate → PASS 后 promote 到 `.runtime/handoff/`。invalid/STALE 不推进事务。

浏览器产生 `(1)` 等候选时只在 Human/Codex 明确确认后使用 `--source`；不得自动猜。

`PENDING_HANDOFF` preview 后，如果 Human 不同意 Assistance / Result / Criterion / Observation 等课堂语义：

1. 不让本地 Codex直接重写 Handoff；
2. 回原 Tutor结合完整课堂对话商议；
3. Tutor 输出完整修订版；
4. 使用：

```bash
python tools/learning.py collect-handoff \
  --source "<revised candidate>" \
  --replace \
  --confirm <LESSON_ID>
```

然后重新 preview。

## 7. Preview / Apply / commit

`PENDING_HANDOFF` 先：

```bash
python tools/handoff.py preview <handoff>
```

Human审核后才：

```bash
python tools/handoff.py apply <handoff>
```

Notes Delta 的 `Engineering Rules` 含 `DECISION:` 时，按 `LOCAL_HANDOFF_WORKFLOW.md` 在 Preview 审核 Human 已确认的决策与已有规则的一致性。

apply 只确定性修改当前 Topic 四文件并在成功 Close 后清除 Tutor transaction pointer，不自动 commit。

如果 Pending Lesson/Handoff 期间 `00_global/`、`01_topics/` 或 `TEACHING_MODE_ROUTE.md` 出现并行修改，不要 commit；先另存并恢复开课时的学习事实与 Mode Route。若 Lesson 实际从未发生，Human 仍可明确 Discard；Discard 后再处理这些并行修改。

## 8. Discard

只有 Human 明确确认 Lesson 实际没有进行、没有结果需要保存时：

```bash
python tools/learning.py discard-lesson --confirm <LESSON_ID>
```

它删除当前 Context/Prompt 和 Tutor transaction pointer，不修改长期学习事实。`PENDING_HANDOFF` 不能用 Discard 绕过 review/apply。

## 9. 文件修改边界

正常学习流中：

- Master-approved planning 才修改 `master_outline / ability_profile / Topic scheduling facts / TEACHING_MODE_ROUTE.md` 的课程映射；
- Tutor Handoff apply 才修改普通 Lesson 的 State/Gate Progress/Evidence/Notes；
- Evidence 历史 append-only；
- 不直接编辑 runtime transaction/incoming/Handoff 来推进状态；
- Human 工程源码与实验文件可正常修改，除非某个具体课程协议另有说明。

普通 Repo maintenance（README/AGENTS/其余 Specs/Templates/tools）按开发任务处理；Teaching Mode Route 的规划映射单独遵守 Master 审批。

## 10. 协议维护一致性

修改协议、脚本或模板时，同时检查：文件名/引用、schema/enum/required fields、CLI help、Context Builder、Handoff validator/apply、audit/route 和 README 真实操作。

README 面向 Human：Quick Start + 少量操作/文件边界，不写 changelog，不复制内部 Agent 协议。

## 11. 核心不变量

- Repo 是长期记忆，Chat 可替换；
- 活跃 Tutor transaction 有唯一显式 pointer，不由 mtime 推导；
- Topic 长期存在，Gate 可跨多个 Lesson；
- Lesson `COMPLETE` 不等于 Gate `PASSED`；
- Criteria 定义稳定，真实进度只存在于 `Criterion Progress`；
- Gate `PASSED` 需要当前 Gate 的 qualifying PASS Evidence 且满足 Assistance ceiling；
- Human 批准前 Master Plan 不落盘；
- Human 批准前不 commit；
- Python 执行机械合同，不替 Human/Tutor/Master做语义判断。
