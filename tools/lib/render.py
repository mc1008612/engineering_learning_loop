"""
Engineering Learning Loop 的人类可读文本渲染模块。

本模块只负责把已经确定的状态与模板渲染成：
- Tutor Start Prompt；
- `learning.py status` 的 CURRENT STATE / NEXT ACTION 输出。

它不读取课程语义、不决定 route、不修改长期学习状态。
"""

from __future__ import annotations

from pathlib import Path

from .flow import FlowStatus
from .repo import ROOT, TEMPLATES, rd


def render_tutor_start_prompt(context_path: Path, lesson_id: str, handoff_filename: str) -> str:
    template = rd(TEMPLATES / "prompts" / "tutor_start.md")
    rel = context_path.relative_to(ROOT).as_posix()
    replacements = {
        "{{CONTEXT_FILE}}": rel,
        "{{LESSON_ID}}": lesson_id,
        "{{HANDOFF_FILENAME}}": handoff_filename,
    }
    text = template
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text.rstrip() + "\n"


def render_flow_status(status: FlowStatus, master_context: Path | None = None) -> str:
    lines = [f"CURRENT_STATE: {status.state}", "", f"原因：{status.reason}"]

    if status.pending_lesson:
        lesson = status.pending_lesson
        lines += [
            "",
            f"Lesson: {lesson.lesson_id}",
            f"Topic: {lesson.topic}",
            f"Gate: {lesson.gate}",
            f"Context: {lesson.context_path.relative_to(ROOT).as_posix()}",
            f"Expected Handoff: {lesson.handoff_filename}",
        ]
    if status.handoff_path:
        lines.append(f"Local Handoff: {status.handoff_path.relative_to(ROOT).as_posix()}")
    if status.dirty_learning_files:
        label = (
            "开课/收件事务期间出现的并行 learning-state 修改："
            if status.state in {"PENDING_LESSON", "PENDING_HANDOFF"}
            else "待审核学习状态修改："
        )
        lines += ["", label] + [f"- {x}" for x in status.dirty_learning_files]
    if master_context:
        lines += ["", f"Master Context: {master_context.relative_to(ROOT).as_posix()}"]

    lines += ["", "NEXT_ACTION:"]
    if status.state == "REPO_ERROR":
        lines.append("先修复上面的 Repo/Git 错误；在错误消失前不要继续学习流程。")
    elif status.state == "PENDING_LEARNING_CHANGES":
        lines += [
            "先 review 当前 learning-state diff。确认无误后由 Human 明确批准 commit；",
            "如果 `git status --short` 中存在 `??` 新 learning files，普通 `git diff` 看不到它们；必须额外完整展示/读取这些新文件后再请求 Human 批准。",
            "commit 完成后重新运行 `python tools/learning.py status`。",
        ]
    elif status.state == "PENDING_HANDOFF":
        if status.dirty_learning_files:
            lines += [
                "先不要 preview/apply，也不要 commit 上面的并行 learning-state 修改。",
                "这些修改发生在本 Lesson Context 之后，会让已收取 Handoff 变成 STALE；先 revert/stash/另存，使 00_global/ 与 01_topics/ 恢复到开课时状态。",
                "恢复干净后重新运行 `python tools/learning.py status`，再继续 Handoff review。",
            ]
            return "\n".join(lines).rstrip() + "\n"
        lines += [
            "先预览 Handoff 将造成的确定性修改：",
            f"`python tools/handoff.py preview {status.handoff_path.relative_to(ROOT).as_posix()}`",
            "Human review 无误后再执行 `python tools/handoff.py apply <handoff>`。",
            "如果 Human 对 Assistance / Result / Criterion / Observation 等课堂语义不认可，不要手改 runtime Handoff；回 Web Tutor 商议并让 Tutor 输出完整修正版，再用 `learning.py collect-handoff --source <修正版> --replace --confirm <lesson_id>` 替换后重新 preview。",
        ]
    elif status.state == "PENDING_LESSON":
        if status.dirty_learning_files:
            lines += [
                "如果本 Lesson 已经发生学习：先不要 collect 或 commit 上面的并行 learning-state 修改；先 revert/stash/另存，使 00_global/ 与 01_topics/ 恢复到开课时状态。",
                "如果 Human 明确确认本 Lesson 实际从未发生：仍可显式 `discard-lesson --confirm <lesson_id>`；Discard 后再处理这些并行修改。",
                "恢复或 Discard 后重新运行 `python tools/learning.py status`。",
            ]
            return "\n".join(lines).rstrip() + "\n"
        lines += [
            "如果课程正在进行：继续原 Web Tutor 对话。",
            "如果课程已经完成：运行 `python tools/learning.py collect-handoff`。",
            "如果该 Lesson 实际没有进行且确定不保留任何结果：Human 明确确认后运行 `python tools/learning.py discard-lesson`。",
            "在 Close 或 Discard 前禁止创建下一 Lesson。",
        ]
    elif status.state == "MASTER_REVIEW":
        lines += [
            "结合 Master Context、Repo 当前事实和 Human 本次偏好/限制，进行只读 Master Review。",
            "输出中文 `MASTER PLAN` 后停止，等待 Human 批准；批准前不得修改长期学习状态。",
        ]
    elif status.state == "READY_FOR_TUTOR":
        lines += [
            "当前可以创建下一 Tutor Lesson。",
            "Human 确认开课时运行 `python tools/learning.py start-tutor`。",
        ]

    if status.warnings:
        lines += ["", "WARNINGS（不阻塞学习流程）："] + [f"- {x}" for x in status.warnings]
    return "\n".join(lines).rstrip() + "\n"
