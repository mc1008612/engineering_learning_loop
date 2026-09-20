"""
Engineering Learning Loop 的 Tutor Handoff 确定性事务模块。

本模块负责：
- 解析并验证 `TUTOR_HANDOFF`；
- 核对真实 Tutor Context identity、完整 Context hash 与 source fingerprints；
- 从真实 Evidence ledger 重算下一 Evidence ID；
- 校验 Gate Criterion、Evidence Reference 与 A0-A3 Assistance 上限；
- 生成 deterministic patch，并在 apply 后执行 audit，失败则回滚。

本模块不判断“学习者是否真的学会”；它只检查 Tutor 已给出的结构化判断是否满足 Repo 的机械合同。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import difflib
import json
import re
from typing import Any

from .context import context_sha256, expected_handoff_filename
from .repo import (
    ASSISTANCE,
    CRITERION_STATUS,
    EVIDENCE_RESULTS,
    EVIDENCE_TYPES,
    G,
    LESSON_STATUS,
    NOTES_SECTIONS,
    REVIEW_REASONS,
    ROOT,
    RUNTIME,
    T,
    audit_repository,
    evidence_entries,
    evidence_field,
    evidence_refs,
    extract_gate,
    frontmatter,
    gate_criterion_ids,
    gate_has_qualifying_pass_evidence,
    gate_mandatory_ids,
    gate_max_assistance,
    gate_progress,
    gate_status,
    next_evidence_id,
    normalize_bullet_item,
    numbered_evidence_id,
    rd,
    replace_section,
    section,
    sha,
    update_frontmatter,
)


def fenced_json(body: str) -> Any:
    m = re.fullmatch(r"\s*```json\s*\n(.*?)\n```\s*", body, flags=re.S | re.I)
    if not m:
        raise ValueError("section must contain exactly one fenced ```json block")
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc.msg} at line {exc.lineno}") from exc


def _section_json(text: str, heading: str) -> Any:
    body = section(text, heading)
    if not body:
        raise ValueError(f"missing section {heading}")
    return fenced_json(body)


@dataclass
class HandoffValidation:
    path: Path
    text: str
    meta: dict[str, str]
    state_delta: dict[str, Any]
    gate_delta: dict[str, Any]
    evidence_delta: list[dict[str, Any]]
    notes_delta: dict[str, Any]
    last_lesson: str
    context_path: Path


def _evidence_facts_from_ledger(text: str, topic: str) -> dict[str, tuple[str | None, str | None, str | None]]:
    return {
        entry.evidence_id: (
            evidence_field(entry.text, "Gate"),
            evidence_field(entry.text, "Result"),
            evidence_field(entry.text, "Assistance"),
        )
        for entry in evidence_entries(text, topic)
    }


def validate_handoff(path: Path) -> HandoffValidation:
    p = path if path.is_absolute() else ROOT / path
    p = p.resolve()
    if not p.exists():
        raise ValueError("handoff not found")
    text = rd(p)
    meta = frontmatter(text)
    required = {
        "schema",
        "delta_format",
        "lesson_id",
        "lesson_status",
        "topic",
        "gate",
        "master_review_required",
        "master_review_reason",
        "context_file",
        "context_sha256",
        "fingerprint_state",
        "fingerprint_gates",
        "fingerprint_evidence",
        "fingerprint_notes",
        "fingerprint_master_outline",
        "fingerprint_ability_profile",
    }
    missing = required - set(meta)
    if missing:
        raise ValueError("missing fields: " + ",".join(sorted(missing)))
    if meta["schema"] != "tutor_handoff":
        raise ValueError("unsupported schema")
    if meta["delta_format"] != "structured_json":
        raise ValueError("unsupported delta_format")
    if meta["lesson_status"] not in LESSON_STATUS:
        raise ValueError("invalid lesson_status")
    if meta["master_review_required"] not in {"true", "false"}:
        raise ValueError("invalid master_review_required")
    reason = meta["master_review_reason"]
    if reason not in REVIEW_REASONS:
        raise ValueError("invalid master_review_reason")
    if meta["master_review_required"] == "false" and reason != "NONE":
        raise ValueError("reason must be NONE when review=false")
    if meta["master_review_required"] == "true" and reason == "NONE":
        raise ValueError("reason must be non-NONE when review=true")

    for heading in ("Last Lesson", "State Delta", "Gate Delta", "Evidence To Append", "Notes Delta"):
        count = len(re.findall(rf"(?m)^##\s+{re.escape(heading)}\s*$", text))
        if count != 1:
            raise ValueError(f"required section {heading} must appear exactly once; found {count}")

    topic = meta["topic"]
    topic_dir = T / topic
    if not topic_dir.exists():
        raise ValueError("unknown topic")
    state_text = rd(topic_dir / "state.md")
    state_fm = frontmatter(state_text)
    if state_fm.get("current_gate") != meta["gate"]:
        raise ValueError("handoff gate != current gate")

    context_rel = Path(meta["context_file"])
    context_path = (ROOT / context_rel).resolve()
    context_root = (RUNTIME / "context").resolve()
    try:
        context_path.relative_to(context_root)
    except ValueError as exc:
        raise ValueError("context_file must be inside .runtime/context") from exc
    if not context_path.is_file():
        raise ValueError("context_file does not exist")
    context_text = rd(context_path)
    context_fm = frontmatter(context_text)
    if context_fm.get("schema") != "tutor_context":
        raise ValueError("context_file is not tutor_context")
    for handoff_key, context_key in (("lesson_id", "lesson_id"), ("topic", "topic"), ("gate", "current_gate"), ("context_file", "context_file")):
        if meta[handoff_key] != context_fm.get(context_key):
            raise ValueError(f"handoff {handoff_key} does not match context")
    expected_handoff = expected_handoff_filename(meta["lesson_id"])
    if context_fm.get("handoff_filename") != expected_handoff:
        raise ValueError("context handoff_filename does not match lesson_id")
    actual_context_hash = context_sha256(context_text)
    if meta["context_sha256"] != actual_context_hash or context_fm.get("context_sha256") != actual_context_hash:
        raise ValueError("context_sha256 mismatch")

    paths = {
        "state": topic_dir / "state.md",
        "gates": topic_dir / "gates.md",
        "evidence": topic_dir / "evidence.md",
        "notes": topic_dir / "notes.md",
        "master_outline": G / "master_outline.md",
        "ability_profile": G / "ability_profile.md",
    }
    stale: list[str] = []
    for key, q in paths.items():
        expected = meta["fingerprint_" + key]
        if context_fm.get("fingerprint_" + key) != expected:
            raise ValueError(f"handoff fingerprint_{key} does not match context")
        if sha(q) != expected:
            stale.append(str(q.relative_to(ROOT)))
    if stale:
        raise RuntimeError("STALE: " + ", ".join(stale))

    last_lesson = section(text, "Last Lesson")
    for label in ("Focus:", "Work:", "Outcome:", "Gate Progress:", "Evidence:", "Suggested Local Next:"):
        if label not in last_lesson:
            raise ValueError("Last Lesson missing label " + label)

    state_delta = _section_json(text, "State Delta")
    gate_delta = _section_json(text, "Gate Delta")
    notes_delta = _section_json(text, "Notes Delta")
    if not isinstance(state_delta, dict):
        raise ValueError("State Delta JSON must be an object")
    if not isinstance(gate_delta, dict):
        raise ValueError("Gate Delta JSON must be an object")
    if not isinstance(notes_delta, dict):
        raise ValueError("Notes Delta JSON must be an object")

    if set(state_delta) - {"set", "add_evidence_anchors"}:
        raise ValueError("State Delta contains unsupported top-level keys")

    set_obj = state_delta.get("set", {})
    if not isinstance(set_obj, dict):
        raise ValueError("State Delta.set must be an object")
    allowed_state_keys = {"passed", "in_progress", "not_yet_verified", "blockers", "revalidation_flags", "open_questions"}
    if set(set_obj) - allowed_state_keys:
        raise ValueError("State Delta.set contains unsupported keys")
    for key, value in set_obj.items():
        if not isinstance(value, list) or not all(isinstance(x, str) and x.strip() for x in value):
            raise ValueError(f"State Delta.set.{key} must be a list of non-empty strings")
    anchors = state_delta.get("add_evidence_anchors", [])
    if not isinstance(anchors, list) or not all(isinstance(x, str) for x in anchors):
        raise ValueError("State Delta.add_evidence_anchors must be a string list")

    if set(gate_delta) - {"status", "criteria", "add_evidence_references"}:
        raise ValueError("Gate Delta contains unsupported keys")
    if "status" in gate_delta and gate_delta["status"] not in {"OPEN", "BLOCKED", "PASSED"}:
        raise ValueError("Gate Delta.status must be OPEN, BLOCKED or PASSED")
    criteria = gate_delta.get("criteria", {})
    if not isinstance(criteria, dict):
        raise ValueError("Gate Delta.criteria must be an object")
    gate_text = rd(topic_dir / "gates.md")
    block = extract_gate(gate_text, meta["gate"])
    if not block:
        raise ValueError("current Gate block not found")
    resulting_gate_status = gate_delta.get("status") or gate_status(gate_text, meta["gate"])
    if resulting_gate_status == "BLOCKED" and meta["master_review_required"] != "true":
        raise ValueError("resulting Gate BLOCKED requires master_review_required=true")
    known_criteria = gate_criterion_ids(block)
    for cid, value in criteria.items():
        if cid not in known_criteria:
            raise ValueError(f"Gate Delta references unknown criterion {cid}")
        if value not in CRITERION_STATUS:
            raise ValueError(f"invalid criterion status {cid}={value}")
    gate_refs = gate_delta.get("add_evidence_references", [])
    if not isinstance(gate_refs, list) or not all(isinstance(x, str) for x in gate_refs):
        raise ValueError("Gate Delta.add_evidence_references must be a string list")

    evidence_body = section(text, "Evidence To Append")
    if evidence_body.strip().upper() == "NONE":
        evidence_delta: list[dict[str, Any]] = []
    else:
        value = fenced_json(evidence_body)
        if not isinstance(value, list):
            raise ValueError("Evidence To Append JSON must be an array or NONE")
        evidence_delta = value

    existing_text = rd(topic_dir / "evidence.md")
    existing_ids = {x.evidence_id for x in evidence_entries(existing_text, topic)}
    ledger_next = next_evidence_id(existing_text, topic)
    context_next = context_fm.get("next_evidence_id")
    if context_next != ledger_next:
        raise ValueError(f"context next_evidence_id is stale/invalid; expected {ledger_next}")
    expected_num = int(ledger_next.rsplit("-", 1)[1])
    new_ids: list[str] = []
    for idx, entry in enumerate(evidence_delta):
        if not isinstance(entry, dict):
            raise ValueError("each Evidence entry must be an object")
        required_entry = {"id", "title", "type", "result", "assistance", "gate", "lesson_id", "observation", "interpretation"}
        missing_entry = required_entry - set(entry)
        if missing_entry:
            raise ValueError("Evidence entry missing: " + ",".join(sorted(missing_entry)))
        eid = entry["id"]
        if not isinstance(eid, str) or not re.fullmatch(rf"{re.escape(topic)}-EXP-\d{{3}}", eid):
            raise ValueError("invalid Evidence id")
        if eid in existing_ids or eid in new_ids:
            raise ValueError("duplicate Evidence ID: " + eid)
        expected_id = numbered_evidence_id(topic, expected_num + idx)
        if eid != expected_id:
            raise ValueError(f"non-sequential Evidence ID: expected {expected_id}")
        if entry["type"] not in EVIDENCE_TYPES:
            raise ValueError(f"{eid}: invalid type")
        if entry["result"] not in EVIDENCE_RESULTS:
            raise ValueError(f"{eid}: invalid result")
        if entry["assistance"] not in ASSISTANCE:
            raise ValueError(f"{eid}: invalid assistance")
        if entry["gate"] != meta["gate"]:
            raise ValueError(f"{eid}: gate must equal handoff gate")
        if entry["lesson_id"] != meta["lesson_id"]:
            raise ValueError(f"{eid}: lesson_id must equal handoff lesson_id")
        if not isinstance(entry["title"], str) or not entry["title"].strip():
            raise ValueError(f"{eid}: title required")
        for key in ("observation", "interpretation"):
            if not isinstance(entry[key], str) or not entry[key].strip():
                raise ValueError(f"{eid}: {key} required")
        refs = entry.get("references", [])
        if not isinstance(refs, list) or not all(isinstance(x, str) for x in refs):
            raise ValueError(f"{eid}: references must be a string list")
        # 当前 eid 尚未加入 new_ids：references 只能指向历史 Evidence 或本数组更早定义的 Evidence。
        if any(ref not in existing_ids and ref not in new_ids for ref in refs):
            raise ValueError(f"{eid}: references unknown Evidence")
        artifacts = entry.get("artifacts", [])
        if not isinstance(artifacts, list):
            raise ValueError(f"{eid}: artifacts must be a list")
        new_ids.append(eid)

    all_known = existing_ids | set(new_ids)
    for ref in anchors + gate_refs:
        if ref not in all_known:
            raise ValueError("Delta references unknown Evidence: " + ref)

    append = notes_delta.get("append", {})
    if set(notes_delta) - {"append"}:
        raise ValueError("Notes Delta only supports append")
    if not isinstance(append, dict):
        raise ValueError("Notes Delta.append must be an object")
    if set(append) - NOTES_SECTIONS:
        raise ValueError("Notes Delta.append contains unsupported section")
    for heading, items in append.items():
        if not isinstance(items, list) or not all(isinstance(x, str) and x.strip() for x in items):
            raise ValueError(f"Notes Delta.append[{heading}] must be a non-empty string list")

    # Gate PASSED 的机械一致性检查：criteria + refs + PASS Evidence + Assistance ceiling。
    resulting_status = gate_delta.get("status", gate_status(gate_text, meta["gate"]))
    if resulting_status == "PASSED":
        final_progress = gate_progress(block)
        final_progress.update(criteria)
        missing_criteria = sorted(
            cid for cid in gate_mandatory_ids(block) if final_progress.get(cid) != "VERIFIED"
        )
        if missing_criteria:
            raise ValueError("cannot set Gate PASSED; mandatory criteria not VERIFIED: " + ", ".join(missing_criteria))
        final_refs = evidence_refs(section(block, "Evidence References", level=3), topic)
        for eid in gate_refs:
            if eid not in final_refs:
                final_refs.append(eid)
        if not final_refs:
            raise ValueError("cannot set Gate PASSED without Evidence References")
        evidence_by_id = _evidence_facts_from_ledger(existing_text, topic)
        for entry in evidence_delta:
            evidence_by_id[entry["id"]] = (entry["gate"], entry["result"], entry["assistance"])
        maximum = gate_max_assistance(block)
        if maximum not in ASSISTANCE:
            raise ValueError("current Gate has invalid/missing Allowed Assistance Maximum")
        if not gate_has_qualifying_pass_evidence(meta["gate"], maximum, final_refs, evidence_by_id):
            raise ValueError(
                f"cannot set Gate PASSED; need referenced PASS Evidence for current Gate with Assistance <= {maximum}"
            )

    return HandoffValidation(
        path=p,
        text=text,
        meta=meta,
        state_delta=state_delta,
        gate_delta=gate_delta,
        evidence_delta=evidence_delta,
        notes_delta=notes_delta,
        last_lesson=last_lesson,
        context_path=context_path,
    )


def _bullet_items(body: str) -> list[str]:
    items = [m.group(1).strip() for m in re.finditer(r"(?m)^-\s+(.*?)\s*$", body)]
    return [x for x in items if x and x.upper() != "NONE"]


def _bullets(items: list[str]) -> str:
    cleaned = [normalize_bullet_item(x) for x in items]
    cleaned = [x for x in cleaned if x and x.upper() != "NONE"]
    return "\n".join(f"- {x}" for x in cleaned) if cleaned else "- NONE"


def _parse_snapshot(body: str) -> dict[str, list[str]]:
    labels = [
        ("passed", "Passed"),
        ("in_progress", "In Progress"),
        ("not_yet_verified", "Not Yet Verified"),
    ]
    out: dict[str, list[str]] = {}
    for idx, (key, label) in enumerate(labels):
        next_label = labels[idx + 1][1] if idx + 1 < len(labels) else None
        if next_label:
            pat = rf"(?ms)^{re.escape(label)}:\s*\n(.*?)(?=^{re.escape(next_label)}:\s*$)"
        else:
            pat = rf"(?ms)^{re.escape(label)}:\s*\n(.*?)\Z"
        m = re.search(pat, body)
        if not m:
            raise ValueError(f"Current Snapshot missing {label}")
        out[key] = _bullet_items(m.group(1))
    return out


def _render_snapshot(values: dict[str, list[str]]) -> str:
    return (
        "Passed:\n" + _bullets(values["passed"]) + "\n\n"
        "In Progress:\n" + _bullets(values["in_progress"]) + "\n\n"
        "Not Yet Verified:\n" + _bullets(values["not_yet_verified"])
    )


def _replace_gate_block(gates_text: str, gate_id: str, new_block: str) -> str:
    pat = re.compile(rf"(?ms)^##\s+{re.escape(gate_id)}\b.*?(?=^##\s+|\Z)")
    if not pat.search(gates_text):
        raise ValueError("current Gate block not found")
    return pat.sub(new_block.strip() + "\n\n", gates_text, count=1).rstrip() + "\n"


def _render_evidence(entry: dict[str, Any]) -> str:
    refs = entry.get("references", [])
    artifacts = entry.get("artifacts", [])
    lines = [
        f"### {entry['id']} — {entry['title'].strip()}",
        "",
        "Schema: `evidence_entry`",
        f"Type: `{entry['type']}`",
        f"Result: `{entry['result']}`",
        f"Assistance: `{entry['assistance']}`",
        f"Gate: `{entry['gate']}`",
        f"Lesson: `{entry['lesson_id']}`",
    ]
    if entry.get("observed_at"):
        lines.append(f"Observed At: `{entry['observed_at']}`")
    lines += ["", "References:"]
    lines += [f"- {x}" for x in refs] if refs else ["- NONE"]
    lines += ["", "Artifacts:"]
    if artifacts:
        for artifact in artifacts:
            lines.append(f"- {artifact}" if isinstance(artifact, str) else "- " + json.dumps(artifact, ensure_ascii=False, sort_keys=True))
    else:
        lines.append("- NONE")
    lines += [
        "",
        "#### Observation",
        entry["observation"].strip(),
        "",
        "#### Interpretation",
        entry["interpretation"].strip(),
    ]
    return "\n".join(lines).strip()


def build_changes(result: HandoffValidation) -> dict[Path, str]:
    meta = result.meta
    topic = meta["topic"]
    td = T / topic
    state_path = td / "state.md"
    gates_path = td / "gates.md"
    evidence_path = td / "evidence.md"
    notes_path = td / "notes.md"

    state_text = rd(state_path)
    snapshot = _parse_snapshot(section(state_text, "Current Snapshot"))
    state_set = result.state_delta.get("set", {})
    for key in ("passed", "in_progress", "not_yet_verified"):
        if key in state_set:
            snapshot[key] = [normalize_bullet_item(x) for x in state_set[key]]
    state_text = replace_section(state_text, "Current Snapshot", _render_snapshot(snapshot))

    state_section_map = {
        "blockers": "Current Blockers",
        "revalidation_flags": "Revalidation Flags",
        "open_questions": "Open Questions / Deferred",
    }
    for key, heading in state_section_map.items():
        if key in state_set:
            state_text = replace_section(state_text, heading, _bullets(state_set[key]))

    anchors = _bullet_items(section(state_text, "Evidence Anchors"))
    for eid in result.state_delta.get("add_evidence_anchors", []):
        if eid not in anchors:
            anchors.append(eid)
    state_text = replace_section(state_text, "Evidence Anchors", _bullets(anchors))

    last_lesson = (
        f"Lesson ID: `{meta['lesson_id']}`\n"
        f"Status: `{meta['lesson_status']}`\n"
        f"Gate: `{meta['gate']}`\n\n"
        + result.last_lesson.strip()
    )
    state_text = replace_section(state_text, "Last Lesson", last_lesson)
    state_text = update_frontmatter(
        state_text,
        {
            "master_review_required": meta["master_review_required"],
            "master_review_reason": meta["master_review_reason"],
            "last_lesson_id": meta["lesson_id"],
        },
    )

    gates_text = rd(gates_path)
    gate_block = extract_gate(gates_text, meta["gate"])
    progress = gate_progress(gate_block)
    progress.update(result.gate_delta.get("criteria", {}))
    progress_body = "\n".join(f"- {cid}: `{status}`" for cid, status in progress.items())
    gate_block = replace_section(gate_block, "Criterion Progress", progress_body, level=3)

    refs = evidence_refs(section(gate_block, "Evidence References", level=3), topic)
    for eid in result.gate_delta.get("add_evidence_references", []):
        if eid not in refs:
            refs.append(eid)
    gate_block = replace_section(gate_block, "Evidence References", _bullets(refs), level=3)

    if "status" in result.gate_delta:
        gate_block, count = re.subn(
            r"(?m)^Status:\s*`?[A-Z_]+`?\s*$",
            f"Status: `{result.gate_delta['status']}`",
            gate_block,
            count=1,
        )
        if count != 1:
            raise ValueError("current Gate has no single Status field")
    gates_text = _replace_gate_block(gates_text, meta["gate"], gate_block)

    evidence_text = rd(evidence_path).rstrip()
    if result.evidence_delta:
        evidence_text += "\n\n" + "\n\n".join(_render_evidence(x) for x in result.evidence_delta)
    evidence_text = evidence_text.rstrip() + "\n"

    notes_text = rd(notes_path)
    for heading, new_items in result.notes_delta.get("append", {}).items():
        existing = _bullet_items(section(notes_text, heading))
        normalized_existing = {normalize_bullet_item(x) for x in existing}
        for item in new_items:
            normalized = normalize_bullet_item(item)
            if normalized and normalized not in normalized_existing:
                existing.append(normalized)
                normalized_existing.add(normalized)
        notes_text = replace_section(notes_text, heading, _bullets(existing))

    return {
        state_path: state_text,
        gates_path: gates_text,
        evidence_path: evidence_text,
        notes_path: notes_text,
    }


def unified_patch(changes: dict[Path, str]) -> str:
    parts: list[str] = []
    for path, new in changes.items():
        old = rd(path)
        if old == new:
            continue
        rel = path.relative_to(ROOT).as_posix()
        parts.extend(
            difflib.unified_diff(
                old.splitlines(), new.splitlines(), fromfile="a/" + rel, tofile="b/" + rel, lineterm=""
            )
        )
    return "\n".join(parts) if parts else "(no changes)"


def apply_validated_handoff(result: HandoffValidation) -> tuple[dict[Path, str], object]:
    changes = build_changes(result)
    originals = {path: rd(path) for path in changes}
    try:
        for path, text in changes.items():
            path.write_text(text, encoding="utf-8")
        audit = audit_repository(check_git_append_only=True)
        if audit.errors:
            raise ValueError("post-apply audit failed:\n- " + "\n- ".join(audit.errors))
    except Exception:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")
        raise
    return changes, audit
