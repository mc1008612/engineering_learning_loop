"""
Engineering Learning Loop 的串行学习状态机模块。

本模块回答：当前学习事务停在哪里、哪些动作被允许、下一步是什么。
状态优先级固定为：
REPO_ERROR > PENDING_HANDOFF > PENDING_LESSON > PENDING_LEARNING_CHANGES > MASTER_REVIEW > READY_FOR_TUTOR。

核心约束：Tutor Context 一旦创建，就必须同时建立唯一的本机 Tutor transaction manifest。
活跃 Lesson 只由 `.runtime/tutor_transaction.json` 指认；历史 Context/Handoff 文件的 mtime
永远不参与状态判断。该事务必须通过 Handoff apply 正常 Close，或由 Human 明确 Discard。
聊天历史不参与状态判断。Teaching Mode Route 虽存于 Specs，未提交的模式变更也会阻止下一课。
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Optional

from .context import expected_handoff_filename
from .repo import RUNTIME, T, audit_repository, frontmatter, git_status, is_git_repo, rd, wr

FLOW_STATES = {
    "REPO_ERROR",
    "PENDING_LEARNING_CHANGES",
    "PENDING_HANDOFF",
    "PENDING_LESSON",
    "MASTER_REVIEW",
    "READY_FOR_TUTOR",
}

TRANSACTION_PATH = RUNTIME / "tutor_transaction.json"
TRANSACTION_SCHEMA = "tutor_transaction"
TRANSACTION_REQUIRED_KEYS = {
    "schema",
    "lesson_id",
    "topic",
    "gate",
    "context_file",
    "prompt_file",
    "handoff_filename",
}


@dataclass(frozen=True)
class PendingLesson:
    lesson_id: str
    topic: str
    gate: str
    context_path: Path
    prompt_path: Path
    handoff_filename: str


@dataclass
class FlowStatus:
    state: str
    reason: str
    audit: object
    pending_lesson: Optional[PendingLesson] = None
    handoff_path: Optional[Path] = None
    dirty_learning_files: list[str] | None = None
    warnings: list[str] | None = None


def _runtime_relative_path(value: str, expected_parent: Path) -> Path:
    """把 manifest 中的 Repo-relative runtime path 解析为绝对路径，并限制在指定目录内。"""
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Tutor transaction contains unsafe path: {value}")
    path = (RUNTIME.parent / rel).resolve()
    parent = expected_parent.resolve()
    if path.parent != parent:
        raise ValueError(f"Tutor transaction path is outside expected runtime directory: {value}")
    return path


def create_tutor_transaction(
    *,
    lesson_id: str,
    topic: str,
    gate: str,
    context_path: Path,
    prompt_path: Path,
    handoff_filename: str,
) -> Path:
    """原子写入唯一 Tutor transaction pointer；不保存学习语义，只保存当前事务身份。"""
    data = {
        "schema": TRANSACTION_SCHEMA,
        "lesson_id": lesson_id,
        "topic": topic,
        "gate": gate,
        "context_file": context_path.relative_to(RUNTIME.parent).as_posix(),
        "prompt_file": prompt_path.relative_to(RUNTIME.parent).as_posix(),
        "handoff_filename": handoff_filename,
    }
    RUNTIME.mkdir(parents=True, exist_ok=True)
    temp = TRANSACTION_PATH.with_suffix(".json.tmp")
    wr(temp, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    os.replace(temp, TRANSACTION_PATH)
    return TRANSACTION_PATH


def clear_tutor_transaction(expected_lesson_id: str | None = None) -> None:
    """清除当前 Tutor transaction pointer；可用 lesson_id 防止误清除别的事务。"""
    if not TRANSACTION_PATH.is_file():
        return
    if expected_lesson_id is not None:
        try:
            data = json.loads(rd(TRANSACTION_PATH))
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"cannot verify Tutor transaction before clearing: {exc}") from exc
        if data.get("lesson_id") != expected_lesson_id:
            raise ValueError(
                "Tutor transaction lesson_id mismatch while clearing: "
                f"{data.get('lesson_id')} != {expected_lesson_id}"
            )
    TRANSACTION_PATH.unlink(missing_ok=True)


def _active_transaction() -> PendingLesson | None:
    """读取显式 Tutor transaction；历史 artifact 的时间戳不参与任何判断。"""
    if not TRANSACTION_PATH.is_file():
        return None
    try:
        data = json.loads(rd(TRANSACTION_PATH))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"invalid .runtime/tutor_transaction.json: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Tutor transaction must be a JSON object")
    missing = sorted(TRANSACTION_REQUIRED_KEYS - set(data))
    extra = sorted(set(data) - TRANSACTION_REQUIRED_KEYS)
    if missing:
        raise ValueError("Tutor transaction missing keys: " + ", ".join(missing))
    if extra:
        raise ValueError("Tutor transaction contains unsupported keys: " + ", ".join(extra))
    if data.get("schema") != TRANSACTION_SCHEMA:
        raise ValueError("Tutor transaction has invalid schema")

    lesson_id = str(data["lesson_id"])
    topic = str(data["topic"])
    gate = str(data["gate"])
    context_path = _runtime_relative_path(str(data["context_file"]), RUNTIME / "context")
    prompt_path = _runtime_relative_path(str(data["prompt_file"]), RUNTIME / "prompts")
    handoff_filename = str(data["handoff_filename"])

    if handoff_filename != expected_handoff_filename(lesson_id):
        raise ValueError("Tutor transaction handoff_filename does not match lesson_id")

    topic_state = T / topic / "state.md"
    if not topic_state.is_file():
        raise ValueError(f"Tutor transaction Topic state missing: {topic}/state.md")
    state_fm = frontmatter(rd(topic_state))

    # apply 已把本 Lesson ID 写进长期 State 时，Lesson 语义上已经 Close。
    # 即使进程在随后清 manifest 前崩溃，也不能让旧 Lesson 复活；已关闭事务不再要求历史 artifacts 存在。
    if state_fm.get("last_lesson_id", "NONE") == lesson_id:
        return None

    if not context_path.is_file():
        raise ValueError(f"Tutor transaction Context missing: {context_path.relative_to(RUNTIME.parent)}")
    if not prompt_path.is_file():
        raise ValueError(f"Tutor transaction Prompt missing: {prompt_path.relative_to(RUNTIME.parent)}")

    context_fm = frontmatter(rd(context_path))
    if context_fm.get("schema") != "tutor_context":
        raise ValueError("Tutor transaction Context has invalid schema")
    expected_context = {
        "lesson_id": lesson_id,
        "topic": topic,
        "current_gate": gate,
        "handoff_filename": handoff_filename,
    }
    for key, expected in expected_context.items():
        if context_fm.get(key) != expected:
            raise ValueError(
                f"Tutor transaction/Context mismatch for {key}: {context_fm.get(key)} != {expected}"
            )

    return PendingLesson(
        lesson_id=lesson_id,
        topic=topic,
        gate=gate,
        context_path=context_path,
        prompt_path=prompt_path,
        handoff_filename=handoff_filename,
    )


def pending_lessons() -> list[PendingLesson]:
    """兼容旧调用接口；显式 manifest 保证最多只有一个活跃 Lesson。"""
    lesson = _active_transaction()
    return [lesson] if lesson else []


def learning_dirty_files() -> list[str]:
    # Mode Route 虽在 Specs，但决定下一节 Gate 的教学策略；其未提交变更按学习状态审核。
    return git_status(["00_global", "01_topics", "02_specs/TEACHING_MODE_ROUTE.md"])


def repo_warnings() -> list[str]:
    all_status = git_status()
    warnings: list[str] = []
    for line in all_status:
        path = line[3:].strip() if len(line) >= 4 else line
        if (path.startswith("00_global/") or path.startswith("01_topics/")
                or path == "02_specs/TEACHING_MODE_ROUTE.md"):
            continue
        warnings.append(line)
    return warnings


def current_flow_status() -> FlowStatus:
    audit = audit_repository(check_git_append_only=True)
    warnings = repo_warnings() if is_git_repo() else []

    if not is_git_repo():
        return FlowStatus(
            state="REPO_ERROR",
            reason="当前目录尚未初始化为 Git repository。",
            audit=audit,
            warnings=warnings,
        )
    if audit.errors:
        return FlowStatus(
            state="REPO_ERROR",
            reason="Repo audit failed: " + "; ".join(audit.errors),
            audit=audit,
            warnings=warnings,
        )

    try:
        pending = pending_lessons()
    except ValueError as exc:
        return FlowStatus(
            state="REPO_ERROR",
            reason="Tutor runtime transaction invalid: " + str(exc),
            audit=audit,
            warnings=warnings,
        )

    if pending:
        lesson = pending[0]
        handoff_path = RUNTIME / "handoff" / lesson.handoff_filename
        if handoff_path.is_file():
            return FlowStatus(
                state="PENDING_HANDOFF",
                reason="Tutor Handoff 已收取，但尚未完成 review/apply。",
                audit=audit,
                pending_lesson=lesson,
                handoff_path=handoff_path,
                dirty_learning_files=learning_dirty_files(),
                warnings=warnings,
            )
        return FlowStatus(
            state="PENDING_LESSON",
            reason="Tutor transaction 已建立，但该 Lesson 尚未 Close 或显式 Discard。",
            audit=audit,
            pending_lesson=lesson,
            dirty_learning_files=learning_dirty_files(),
            warnings=warnings,
        )

    dirty = learning_dirty_files()
    if dirty:
        return FlowStatus(
            state="PENDING_LEARNING_CHANGES",
            reason="学习状态或 Teaching Mode Route 存在尚未 review/commit 的修改。",
            audit=audit,
            dirty_learning_files=dirty,
            warnings=warnings,
        )

    if audit.route == "MASTER_REVIEW":
        return FlowStatus(
            state="MASTER_REVIEW",
            reason=audit.reason or "需要 Master Review。",
            audit=audit,
            warnings=warnings,
        )
    if audit.route == "TUTOR":
        return FlowStatus(
            state="READY_FOR_TUTOR",
            reason=audit.reason or "当前状态允许创建新的 Tutor Lesson。",
            audit=audit,
            warnings=warnings,
        )
    return FlowStatus(
        state="REPO_ERROR",
        reason="audit 未返回可识别 route。",
        audit=audit,
        warnings=warnings,
    )
