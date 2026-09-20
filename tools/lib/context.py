"""
Engineering Learning Loop 的 Context 生成模块。

本模块负责：
- 生成新的 Tutor Context；
- 生成只读 Master Review Context；
- 生成 Lesson ID、Context 文件名与预期 Handoff 文件名；
- 计算覆盖 frontmatter + body 的 Context SHA256；
- 从真实 Evidence ledger 计算下一 Evidence ID。
- 从 `02_specs/TUTOR_HANDOFF_PROTOCOL.md` 读取唯一 canonical Tutor Handoff 运行时协议，
  并完整嵌入每一份 Tutor Context。

Tutor Context 的生成本身会开启一个 Pending Lesson 事务；是否允许生成由上层
`learning.py` / `lib.flow` 判断。本模块只负责确定性构造，不负责浏览器、剪贴板或课程决策。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from .repo import (
    G,
    RUNTIME,
    S,
    T,
    audit_repository,
    evidence_refs,
    extract_gate,
    frontmatter,
    next_evidence_id,
    rd,
    relevant_evidence,
    section,
    sha,
    sha_bytes,
    wr,
)

CONTEXT_DIR = RUNTIME / "context"
HASH_PLACEHOLDER = "<CONTEXT_SHA256>"
TUTOR_HANDOFF_PROTOCOL = S / "TUTOR_HANDOFF_PROTOCOL.md"
MASTER_REVIEW_PROTOCOL = S / "MASTER_REVIEW_PROTOCOL.md"


def new_lesson_id(topic: str) -> str:
    return f"{topic}-LSN-" + datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def tutor_context_filename(lesson_id: str) -> str:
    return f"TUTOR_CONTEXT_{lesson_id}.md"


def tutor_prompt_filename(lesson_id: str) -> str:
    return f"TUTOR_START_{lesson_id}.md"


def expected_handoff_filename(lesson_id: str) -> str:
    return f"TUTOR_HANDOFF_{lesson_id}.md"


def context_sha256(text: str) -> str:
    """对整个 Context 计算 hash；仅将 context_sha256 自身一行 canonicalize。"""
    normalized, count = re.subn(
        r"(?m)^context_sha256:\s*.*$",
        f"context_sha256: {HASH_PLACEHOLDER}",
        text,
        count=1,
    )
    if count != 1:
        raise ValueError("Context missing single context_sha256 field")
    return sha_bytes(normalized.encode("utf-8"))


def _finalize_context(text_with_placeholder: str) -> tuple[str, str]:
    digest = context_sha256(text_with_placeholder)
    final, count = re.subn(
        rf"(?m)^context_sha256:\s*{re.escape(HASH_PLACEHOLDER)}$",
        f"context_sha256: {digest}",
        text_with_placeholder,
        count=1,
    )
    if count != 1 or context_sha256(final) != digest:
        raise RuntimeError("internal context hash mismatch")
    return final, digest


def _without_fenced_code(text: str) -> str:
    """协议结构检查忽略 fenced code 示例，避免示例字符串掩盖真实 heading 缺失。"""
    return re.sub(r"(?ms)^```[^\n]*\n.*?^```\s*$", "", text)


def _require_exact_protocol_headings(text: str, headings: tuple[tuple[int, str], ...], label: str) -> None:
    visible = _without_fenced_code(text)
    problems: list[str] = []
    for level, heading in headings:
        hashes = "#" * level
        count = len(re.findall(rf"(?m)^{re.escape(hashes)}\s+{re.escape(heading)}\s*$", visible))
        if count != 1:
            problems.append(f"{hashes} {heading} found {count}")
    if problems:
        raise ValueError(f"{label} has invalid heading structure: " + "; ".join(problems))


def tutor_handoff_protocol_text() -> str:
    """读取 Tutor Handoff canonical runtime protocol；缺失/损坏时拒绝开课。"""
    if not TUTOR_HANDOFF_PROTOCOL.is_file():
        raise ValueError("missing canonical Tutor Handoff Protocol")
    text = rd(TUTOR_HANDOFF_PROTOCOL).strip()
    if not text:
        raise ValueError("canonical Tutor Handoff Protocol is empty")
    _require_exact_protocol_headings(
        text,
        (
            (1, "Tutor Handoff Protocol"),
            (2, "Required Frontmatter"),
            (2, "Required Sections"),
            (2, "State Delta"),
            (2, "Gate Delta"),
            (2, "Evidence To Append"),
            (2, "Notes Delta"),
        ),
        "canonical Tutor Handoff Protocol",
    )
    return text




def master_review_protocol_text() -> str:
    """读取 Master Review canonical protocol；缺失/损坏时拒绝生成 Master Context。"""
    if not MASTER_REVIEW_PROTOCOL.is_file():
        raise ValueError("missing canonical Master Review Protocol")
    text = rd(MASTER_REVIEW_PROTOCOL).strip()
    if not text:
        raise ValueError("canonical Master Review Protocol is empty")
    _require_exact_protocol_headings(
        text,
        (
            (1, "Master Review Protocol"),
            (2, "Inputs"),
            (2, "Read-only Review"),
            (2, "MASTER PLAN Format"),
            (2, "Apply Approved Plan"),
        ),
        "canonical Master Review Protocol",
    )
    return text

def current_learning_focus(master_text: str, state_text: str) -> str:
    """从唯一的 routing frontmatter + Topic State 生成 Tutor 可读的当前焦点，避免正文重复事实漂移。"""
    master_fm = frontmatter(master_text)
    topic = master_fm.get("current_topic", "NONE")
    action = master_fm.get("current_action", "MASTER_REVIEW")
    checkpoint = master_fm.get("master_checkpoint", "NONE")
    directive = section(state_text, "Master Directive") or "NONE"
    return (
        f"Topic: `{topic}`\n\n"
        f"Action: `{action}`\n\n"
        f"Checkpoint: `{checkpoint}`\n\n"
        "### Topic Master Directive\n\n"
        + directive
    )


def build_tutor_context() -> Path:
    audit = audit_repository(check_git_append_only=True)
    if audit.errors:
        raise ValueError("Repo audit failed: " + "; ".join(audit.errors))
    if audit.route != "TUTOR":
        raise ValueError(f"ROUTE={audit.route}; Tutor Context generation is not allowed: {audit.reason}")

    master_path = G / "master_outline.md"
    ability_path = G / "ability_profile.md"
    master_text = rd(master_path)
    master_fm = frontmatter(master_text)
    topic = master_fm["current_topic"]
    topic_dir = T / topic
    paths = {
        "state": topic_dir / "state.md",
        "gates": topic_dir / "gates.md",
        "evidence": topic_dir / "evidence.md",
        "notes": topic_dir / "notes.md",
        "master_outline": master_path,
        "ability_profile": ability_path,
    }
    state_text = rd(paths["state"])
    state_fm = frontmatter(state_text)
    gate_id = state_fm.get("current_gate", "NONE")
    gates_text = rd(paths["gates"])
    gate_block = extract_gate(gates_text, gate_id)
    evidence_text = rd(paths["evidence"])
    refs = evidence_refs(state_text + "\n" + gate_block, topic)

    lesson_id = new_lesson_id(topic)
    context_name = tutor_context_filename(lesson_id)
    context_rel = Path(".runtime") / "context" / context_name
    handoff_name = expected_handoff_filename(lesson_id)
    handoff_protocol = tutor_handoff_protocol_text()

    body = "\n".join(
        [
            "# Tutor Context",
            "",
            "## Teaching Contract",
            "",
            rd(S / "TEACHING_CONTRACT.md"),
            "",
            "## Current Learning Focus",
            "",
            current_learning_focus(master_text, state_text),
            "",
            "## Ability Baseline",
            "",
            rd(paths["ability_profile"]),
            "",
            "## Topic State",
            "",
            state_text,
            "",
            "## Current Gate",
            "",
            gate_block or "NONE",
            "",
            "## Relevant Evidence (Referenced + Recent)",
            "",
            relevant_evidence(evidence_text, topic, refs, recent_n=5),
            "",
            "## Topic Notes",
            "",
            rd(paths["notes"]),
            "",
            "## Embedded Tutor Handoff Protocol",
            "",
            "以下内容已经完整嵌入，是本 Lesson 输出 Handoff 的唯一协议。",
            "Web Tutor 不需要、也不应尝试访问任何 Repo 内路径。",
            "",
            "<!-- BEGIN:TUTOR_HANDOFF_PROTOCOL -->",
            handoff_protocol,
            "<!-- END:TUTOR_HANDOFF_PROTOCOL -->",
        ]
    ).rstrip() + "\n"

    lines = [
        "---",
        "schema: tutor_context",
        f"lesson_id: {lesson_id}",
        f"topic: {topic}",
        f"current_gate: {gate_id}",
        f"next_evidence_id: {next_evidence_id(evidence_text, topic)}",
        f"context_file: {context_rel.as_posix()}",
        f"handoff_filename: {handoff_name}",
        f"context_sha256: {HASH_PLACEHOLDER}",
    ]
    for key, path in paths.items():
        lines.append(f"fingerprint_{key}: {sha(path)}")
    lines += ["---"]
    text, _ = _finalize_context("\n".join(lines) + "\n" + body)

    out = CONTEXT_DIR / context_name
    wr(out, text)
    return out


def build_master_context(trigger: str | None) -> Path:
    """生成本地只读 Master Review Context；trigger 可为 NONE/None。"""
    trigger = trigger if trigger and trigger != "NONE" else "NONE"
    live: list[str] = []
    if T.exists():
        for p in sorted(T.iterdir()):
            if p.is_dir() and (p / "state.md").exists():
                x = rd(p / "state.md")
                xf = frontmatter(x)
                live.append(
                    f"### {p.name}\n"
                    f"status={xf.get('status')}\n"
                    f"current_gate={xf.get('current_gate')}\n"
                    f"master_review_required={xf.get('master_review_required')}\n\n"
                    f"{section(x, 'Last Lesson')}"
                )

    trigger_state = "NONE"
    trigger_gate = "NONE"
    trigger_evidence = "NONE"
    if trigger != "NONE":
        topic_dir = T / trigger
        if not topic_dir.exists():
            raise ValueError(f"Trigger Topic does not exist: {trigger}")
        state_text = rd(topic_dir / "state.md")
        state_fm = frontmatter(state_text)
        gate_id = state_fm.get("current_gate", "NONE")
        gates_text = rd(topic_dir / "gates.md")
        gate_block = extract_gate(gates_text, gate_id)
        ev_text = rd(topic_dir / "evidence.md")
        refs = evidence_refs(state_text + "\n" + gate_block, trigger)
        trigger_state = state_text
        trigger_gate = gate_block or "NONE"
        trigger_evidence = relevant_evidence(ev_text, trigger, refs, recent_n=8)

    text = f"""---
schema: master_review_context
trigger: {trigger}
---

# Master Review Context

## Master Outline

{rd(G / 'master_outline.md')}

## Ability Profile

{rd(G / 'ability_profile.md')}

## Live Topic Summaries

{chr(10).join(live) or 'NONE'}

## Trigger State

{trigger_state}

## Trigger Gate

{trigger_gate}

## Trigger Relevant Evidence

{trigger_evidence}

## Master Review Protocol

{master_review_protocol_text()}
"""
    out = CONTEXT_DIR / "MASTER_CONTEXT.md"
    wr(out, text)
    return out
