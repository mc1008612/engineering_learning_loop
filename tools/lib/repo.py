"""
Engineering Learning Loop 的 Repo 基础读写与一致性检查模块。

本模块负责：
- 定位 Repo 根目录与核心目录；
- 解析 Markdown frontmatter、固定 section、Gate、Evidence；
- 提供 SHA256、Evidence ID、Git 状态等通用函数；
- 执行长期学习状态的 Repo audit 与机械 route 判断。

本模块不负责：
- 课程内容决策；
- Tutor Context / Prompt 的生成；
- Handoff 的落盘事务；
- Web 浏览器、剪贴板等本机 UI 操作。

长期学习事实只来自 00_global/ 与 01_topics/。`.runtime/` 只保存本机临时事务。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import re
import subprocess
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
G = ROOT / "00_global"
T = ROOT / "01_topics"
S = ROOT / "02_specs"
TEMPLATES = ROOT / "03_templates"
RUNTIME = ROOT / ".runtime"

TOPIC_STATUS = {"ACTIVE", "PAUSED", "COMPLETED"}
GATE_STATUS = {"DRAFT", "OPEN", "BLOCKED", "PASSED", "RETIRED"}
CRITERION_STATUS = {"NOT_VERIFIED", "PARTIAL", "VERIFIED"}
LESSON_STATUS = {"COMPLETE", "INTERRUPTED"}
REVIEW_REASONS = {
    "NONE",
    "CURRICULUM_CHECKPOINT",
    "POSSIBLE_LEVEL_CHANGE",
    "TOPIC_LIFECYCLE",
    "CROSS_TOPIC_DEPENDENCY",
    "REVALIDATION",
    "OTHER",
}
EVIDENCE_TYPES = {"LEARNING", "ASSESSMENT", "DEBUG", "TRANSFER", "REVALIDATION"}
EVIDENCE_RESULTS = {"PASS", "PARTIAL", "FAIL"}
ASSISTANCE = {"A0", "A1", "A2", "A3"}
ASSISTANCE_RANK = {"A0": 0, "A1": 1, "A2": 2, "A3": 3}
MASTER_ACTIONS = {"TUTOR", "MASTER_REVIEW"}
TOPIC_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
NOTES_SECTION_ORDER = (
    "Durable Mental Models",
    "Engineering Rules",
    "Debug Checklist",
    "Common Failure Modes",
    "References Worth Reusing",
)
NOTES_SECTIONS = set(NOTES_SECTION_ORDER)

STATE_REQUIRED_SECTIONS = (
    "Master Directive",
    "Current Objective",
    "Current Snapshot",
    "Current Blockers",
    "Revalidation Flags",
    "Last Lesson",
    "Evidence Anchors",
    "Open Questions / Deferred",
)

GATE_REQUIRED_SECTIONS = (
    "Objective",
    "Mandatory Criteria",
    "Allowed Assistance",
    "Required Evidence",
    "Pass Rule",
    "Criterion Progress",
    "Evidence References",
)


def rd(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def wr(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    out: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip().strip("'\"")
    return out


def update_frontmatter(text: str, updates: dict[str, str]) -> str:
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    lines = text[4:end].splitlines()
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        if ":" not in line:
            result.append(line)
            continue
        key, _ = line.split(":", 1)
        k = key.strip()
        if k in updates:
            result.append(f"{k}: {updates[k]}")
            seen.add(k)
        else:
            result.append(line)
    for k, v in updates.items():
        if k not in seen:
            result.append(f"{k}: {v}")
    return "---\n" + "\n".join(result) + text[end:]


def section(text: str, heading: str, level: int = 2, include_heading: bool = False) -> str:
    hashes = "#" * level
    m = re.search(
        rf"(?ms)^{re.escape(hashes)}\s+{re.escape(heading)}\s*\n(.*?)(?=^{re.escape(hashes)}\s+|\Z)",
        text,
    )
    if not m:
        return ""
    return m.group(0).strip() if include_heading else m.group(1).strip()


def heading_count(text: str, heading: str, level: int = 2) -> int:
    """计算固定 Markdown heading 精确出现次数；用于 audit parser 真正依赖的结构。"""
    hashes = "#" * level
    return len(re.findall(rf"(?m)^{re.escape(hashes)}\s+{re.escape(heading)}\s*$", text))


def _audit_required_headings(
    text: str,
    headings: Iterable[str],
    *,
    level: int,
    label: str,
    errors: list[str],
) -> None:
    for heading in headings:
        count = heading_count(text, heading, level=level)
        if count != 1:
            errors.append(f"{label}: required section {heading!r} must appear exactly once; found {count}")


def _audit_master_directive(text: str, *, label: str, errors: list[str]) -> None:
    directive = section(text, "Master Directive")
    if not directive:
        return
    if re.search(r"(?m)^\s*(Action|Checkpoint):", directive):
        errors.append(
            f"{label}: Master Directive must not duplicate routing facts Action/Checkpoint; keep semantic Objective/Reason only"
        )
    for required_label in ("Objective:", "Reason:"):
        if required_label not in directive:
            errors.append(f"{label}: Master Directive missing {required_label}")



def _audit_current_snapshot(text: str, *, label: str, errors: list[str]) -> None:
    """校验 deterministic Handoff patch parser 真正依赖的 Current Snapshot 子结构。"""
    body = section(text, "Current Snapshot")
    labels = ("Passed", "In Progress", "Not Yet Verified")
    positions: list[int] = []
    for item in labels:
        matches = list(re.finditer(rf"(?m)^{re.escape(item)}:\s*$", body))
        if len(matches) != 1:
            errors.append(f"{label}: Current Snapshot label {item!r} must appear exactly once; found {len(matches)}")
            continue
        positions.append(matches[0].start())
    if len(positions) == len(labels) and positions != sorted(positions):
        errors.append(f"{label}: Current Snapshot labels must stay in Passed / In Progress / Not Yet Verified order")


def replace_section(text: str, heading: str, new_body: str, level: int = 2) -> str:
    hashes = "#" * level
    pat = re.compile(
        rf"(?ms)^{re.escape(hashes)}\s+{re.escape(heading)}\s*\n.*?(?=^{re.escape(hashes)}\s+|\Z)"
    )
    replacement = f"{hashes} {heading}\n\n{new_body.strip()}\n\n"
    if not pat.search(text):
        raise ValueError(f"missing section: {heading}")
    return pat.sub(replacement, text, count=1).rstrip() + "\n"


def extract_gate(text: str, gate_id: str) -> str:
    m = re.search(rf"(?ms)^##\s+{re.escape(gate_id)}\b.*?(?=^##\s+|\Z)", text)
    return m.group(0).strip() if m else ""


def gate_ids(text: str) -> list[str]:
    return re.findall(r"(?m)^##\s+([A-Za-z0-9_-]+-GATE-[A-Za-z0-9_-]+)\b", text)


def gate_status(text: str, gate_id: str) -> str | None:
    block = extract_gate(text, gate_id)
    if not block:
        return None
    m = re.search(r"(?m)^Status:\s*`?([A-Z_]+)`?\s*$", block)
    return m.group(1) if m else None


def _criterion_ids_from_definition(body: str) -> set[str]:
    """Criteria 是稳定定义，不使用 Markdown checkbox；进度只存在于 Criterion Progress。"""
    return set(re.findall(r"(?m)^-\s*([A-Za-z]\d+)\s+(?:—|-)\s+\S.*$", body))


def gate_criterion_ids(block: str) -> set[str]:
    mandatory = section(block, "Mandatory Criteria", level=3)
    stretch = section(block, "Stretch Criteria", level=3)
    return _criterion_ids_from_definition(mandatory + "\n" + stretch)


def gate_mandatory_ids(block: str) -> set[str]:
    mandatory = section(block, "Mandatory Criteria", level=3)
    return _criterion_ids_from_definition(mandatory)


def gate_progress(block: str) -> dict[str, str]:
    body = section(block, "Criterion Progress", level=3)
    out: dict[str, str] = {}
    for cid, status in re.findall(r"(?m)^-\s*([A-Za-z]\d+):\s*`?([A-Z_]+)`?\s*$", body):
        out[cid] = status
    return out


def gate_max_assistance(block: str) -> str | None:
    body = section(block, "Allowed Assistance", level=3)
    m = re.search(r"(?mi)^Maximum:\s*`?(A[0-3])`?\s*$", body)
    return m.group(1) if m else None


def evidence_refs(text: str, topic: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for eid in re.findall(rf"\b{re.escape(topic)}-EXP-\d{{3}}\b", text):
        if eid not in seen:
            seen.add(eid)
            out.append(eid)
    return out


@dataclass(frozen=True)
class EvidenceEntry:
    evidence_id: str
    title: str
    text: str


def evidence_entries(text: str, topic: str) -> list[EvidenceEntry]:
    pat = re.compile(
        rf"(?ms)^###\s+({re.escape(topic)}-EXP-\d{{3}})\b(?:\s*[—-]\s*(.*?))?\s*\n(.*?)(?=^###\s+{re.escape(topic)}-EXP-\d{{3}}\b|\Z)"
    )
    out: list[EvidenceEntry] = []
    for m in pat.finditer(text):
        out.append(EvidenceEntry(m.group(1), (m.group(2) or "").strip(), m.group(0).strip()))
    return out


def evidence_field(entry_text: str, name: str) -> str | None:
    m = re.search(rf"(?mi)^{re.escape(name)}:\s*`?([^`\n]+?)`?\s*$", entry_text)
    return m.group(1).strip() if m else None


def evidence_references(entry_text: str, topic: str) -> list[str]:
    """读取单条 persisted Evidence 的 References 列表，不把 Evidence 自身 heading 当成引用。"""
    m = re.search(r"(?ms)^References:\s*\n(.*?)(?=^Artifacts:\s*$|^####\s+|\Z)", entry_text)
    if not m:
        return []
    return evidence_refs(m.group(1), topic)


def numbered_evidence_id(topic: str, number: int) -> str:
    return f"{topic}-EXP-{number:03d}"


def next_evidence_id(text: str, topic: str) -> str:
    nums = [int(x.evidence_id.rsplit("-", 1)[1]) for x in evidence_entries(text, topic)]
    return numbered_evidence_id(topic, max(nums) + 1 if nums else 1)


def relevant_evidence(text: str, topic: str, refs: Iterable[str], recent_n: int = 5) -> str:
    entries = evidence_entries(text, topic)
    by_id = {x.evidence_id: x for x in entries}
    selected: list[EvidenceEntry] = []
    seen: set[str] = set()
    for eid in refs:
        if eid in by_id and eid not in seen:
            selected.append(by_id[eid])
            seen.add(eid)
    for entry in entries[-recent_n:]:
        if entry.evidence_id not in seen:
            selected.append(entry)
            seen.add(entry.evidence_id)
    return "\n\n".join(x.text for x in selected) or "NONE"


def normalize_bullet_item(value: str) -> str:
    """将列表项内部换行/重复空白归一为单行，保留长正文给 Evidence 使用。"""
    value = value.replace("\\r\\n", " ").replace("\\n", " ").replace("\\r", " ")
    return re.sub(r"\s+", " ", value).strip()


def _git_show_head(relative_path: Path) -> str | None:
    try:
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if probe.returncode != 0:
            return None
        p = subprocess.run(
            ["git", "show", f"HEAD:{relative_path.as_posix()}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        return p.stdout if p.returncode == 0 else None
    except (OSError, UnicodeError):
        return None


def is_git_repo() -> bool:
    try:
        p = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return p.returncode == 0
    except OSError:
        return False


def git_status(paths: Iterable[str] | None = None) -> list[str]:
    if not is_git_repo():
        return []
    cmd = ["git", "status", "--porcelain", "--untracked-files=all"]
    if paths:
        cmd += ["--", *paths]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
    return [line.rstrip() for line in p.stdout.splitlines() if line.strip()]


def _validate_evidence_ledger(topic: str, text: str, errors: list[str]) -> None:
    entries = evidence_entries(text, topic)
    ids = [x.evidence_id for x in entries]
    if len(ids) != len(set(ids)):
        errors.append(f"{topic}: duplicate Evidence IDs")
    earlier_ids: set[str] = set()
    for entry in entries:
        schema = evidence_field(entry.text, "Schema")
        typ = evidence_field(entry.text, "Type")
        result = evidence_field(entry.text, "Result")
        assistance = evidence_field(entry.text, "Assistance")
        gate = evidence_field(entry.text, "Gate")
        lesson = evidence_field(entry.text, "Lesson")
        if schema != "evidence_entry":
            errors.append(f"{topic}: {entry.evidence_id} invalid/missing Evidence Schema")
        if typ not in EVIDENCE_TYPES:
            errors.append(f"{topic}: {entry.evidence_id} invalid/missing Evidence Type")
        if result not in EVIDENCE_RESULTS:
            errors.append(f"{topic}: {entry.evidence_id} invalid/missing Evidence Result")
        if assistance not in ASSISTANCE:
            errors.append(f"{topic}: {entry.evidence_id} invalid/missing Assistance")
        if not gate:
            errors.append(f"{topic}: {entry.evidence_id} missing Gate")
        if not lesson:
            errors.append(f"{topic}: {entry.evidence_id} missing Lesson")
        if not section(entry.text, "Observation", level=4):
            errors.append(f"{topic}: {entry.evidence_id} missing Observation")
        if not section(entry.text, "Interpretation", level=4):
            errors.append(f"{topic}: {entry.evidence_id} missing Interpretation")
        for ref in evidence_references(entry.text, topic):
            if ref not in earlier_ids:
                errors.append(
                    f"{topic}: {entry.evidence_id} references non-earlier Evidence {ref}"
                )
        earlier_ids.add(entry.evidence_id)


def _append_only_check(topic: str, current_text: str, errors: list[str]) -> None:
    rel = Path("01_topics") / topic / "evidence.md"
    old = _git_show_head(rel)
    if old is None:
        return
    old_entries = evidence_entries(old, topic)
    cur_entries = evidence_entries(current_text, topic)
    if len(cur_entries) < len(old_entries):
        errors.append(f"{topic}: Evidence history deleted; ledger is append-only")
        return
    for idx, old_entry in enumerate(old_entries):
        cur = cur_entries[idx]
        if cur.evidence_id != old_entry.evidence_id:
            errors.append(f"{topic}: Evidence history reordered/inserted before existing entries")
            return
        if cur.text.strip() != old_entry.text.strip():
            errors.append(f"{topic}: existing Evidence {old_entry.evidence_id} was rewritten")
            return


def gate_has_qualifying_pass_evidence(
    gate_id: str,
    max_assistance: str,
    refs: Iterable[str],
    evidence_by_id: dict[str, tuple[str | None, str | None, str | None]],
) -> bool:
    if max_assistance not in ASSISTANCE_RANK:
        return False
    ceiling = ASSISTANCE_RANK[max_assistance]
    for eid in refs:
        gate, result, assistance = evidence_by_id.get(eid, (None, None, None))
        if (
            gate == gate_id
            and result == "PASS"
            and assistance in ASSISTANCE_RANK
            and ASSISTANCE_RANK[assistance] <= ceiling
        ):
            return True
    return False


@dataclass
class AuditResult:
    errors: list[str]
    warnings: list[str]
    live_topics: list[str]
    current_topic: str
    route: str | None
    trigger: str | None
    reason: str | None


def audit_repository(check_git_append_only: bool = True) -> AuditResult:
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        "README.md",
        "AGENTS.md",
        ".gitignore",
        "00_global/master_outline.md",
        "00_global/ability_profile.md",
        "02_specs/TEACHING_CONTRACT.md",
        "02_specs/ROLE_PROTOCOL.md",
        "02_specs/DATA_MODEL.md",
        "02_specs/TUTOR_CONTEXT_PROTOCOL.md",
        "02_specs/TUTOR_HANDOFF_PROTOCOL.md",
        "02_specs/LOCAL_HANDOFF_WORKFLOW.md",
        "02_specs/MASTER_REVIEW_PROTOCOL.md",
        "02_specs/FILE_CONTRACTS.md",
        "02_specs/PROJECT_GATE_WORKFLOW.md",
        "03_templates/NEW_TOPIC/state.md",
        "03_templates/NEW_TOPIC/gates.md",
        "03_templates/NEW_TOPIC/evidence.md",
        "03_templates/NEW_TOPIC/notes.md",
        "03_templates/prompts/tutor_start.md",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            errors.append("missing " + rel)
    if errors:
        return AuditResult(errors, warnings, [], "NONE", None, None, None)

    # Base Repo 也要保证 Topic Bootstrap 模板本身可被后续 parser/apply 使用。
    template_state = rd(TEMPLATES / "NEW_TOPIC" / "state.md")
    template_gates = rd(TEMPLATES / "NEW_TOPIC" / "gates.md")
    template_notes = rd(TEMPLATES / "NEW_TOPIC" / "notes.md")
    _audit_required_headings(
        template_state,
        STATE_REQUIRED_SECTIONS,
        level=2,
        label="NEW_TOPIC/state.md",
        errors=errors,
    )
    _audit_master_directive(template_state, label="NEW_TOPIC/state.md", errors=errors)
    _audit_required_headings(
        template_notes,
        NOTES_SECTION_ORDER,
        level=2,
        label="NEW_TOPIC/notes.md",
        errors=errors,
    )
    _audit_required_headings(
        template_gates,
        GATE_REQUIRED_SECTIONS,
        level=3,
        label="NEW_TOPIC/gates.md",
        errors=errors,
    )

    master_text = rd(G / "master_outline.md")
    master = frontmatter(master_text)
    if master.get("schema") != "master_outline":
        errors.append("master_outline: invalid schema")
    current = master.get("current_topic", "NONE")
    checkpoint = master.get("master_checkpoint", "NONE")
    action = master.get("current_action", "MASTER_REVIEW")
    if action not in MASTER_ACTIONS:
        errors.append(f"master_outline: invalid current_action={action}")
    if current != "NONE" and not TOPIC_SLUG_RE.fullmatch(current):
        errors.append(
            f"master_outline: invalid current_topic slug={current!r}; use only letters, digits, '_' or '-'"
        )
    if re.search(r"(?m)^##\s+Current Learning Focus\s*$", master_text):
        errors.append(
            "master_outline: Current Learning Focus must not duplicate frontmatter routing facts; remove the body section"
        )

    ability_text = rd(G / "ability_profile.md")
    ability_fm = frontmatter(ability_text)
    if ability_fm.get("schema") != "ability_profile":
        errors.append("ability_profile: invalid schema")
    baseline = section(ability_text, "Current Baseline")
    allowed_levels = {f"L{i}" for i in range(7)}
    for line in baseline.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] == "Ability" or set(cells[0]) <= {"-", ":"}:
            continue
        level = cells[1].strip("`")
        if set(level) <= {"-", ":"}:
            continue
        if level not in allowed_levels:
            errors.append(f"ability_profile: invalid level {level} for {cells[0]}")

    live: list[str] = []
    states: dict[str, dict[str, str]] = {}
    gates_texts: dict[str, str] = {}
    if T.exists():
        for topic_dir in sorted(T.iterdir()):
            if not topic_dir.is_dir():
                continue
            topic = topic_dir.name
            live.append(topic)
            if not TOPIC_SLUG_RE.fullmatch(topic):
                errors.append(
                    f"{topic}: invalid Topic directory slug; use only letters, digits, '_' or '-'"
                )
            missing = [name for name in ("state.md", "gates.md", "evidence.md", "notes.md") if not (topic_dir / name).exists()]
            for name in missing:
                errors.append(f"{topic}: missing {name}")
            if missing:
                continue

            state_text = rd(topic_dir / "state.md")
            gates_text = rd(topic_dir / "gates.md")
            evidence_text = rd(topic_dir / "evidence.md")
            notes_text = rd(topic_dir / "notes.md")
            state = frontmatter(state_text)
            states[topic] = state
            gates_texts[topic] = gates_text

            if state.get("schema") != "topic_state":
                errors.append(f"{topic}: invalid state schema")
            if state.get("topic") != topic:
                errors.append(f"{topic}: state.topic mismatch")
            if state.get("status") not in TOPIC_STATUS:
                errors.append(f"{topic}: invalid Topic status={state.get('status')}")
            if state.get("master_review_required") not in {"true", "false"}:
                errors.append(f"{topic}: invalid master_review_required")
            reason = state.get("master_review_reason", "NONE")
            if reason not in REVIEW_REASONS:
                errors.append(f"{topic}: invalid master_review_reason={reason}")
            if state.get("master_review_required") == "false" and reason != "NONE":
                errors.append(f"{topic}: review=false requires reason=NONE")
            if state.get("master_review_required") == "true" and reason == "NONE":
                errors.append(f"{topic}: review=true requires non-NONE reason")

            _audit_required_headings(
                state_text,
                STATE_REQUIRED_SECTIONS,
                level=2,
                label=f"{topic}/state.md",
                errors=errors,
            )
            _audit_master_directive(state_text, label=f"{topic}/state.md", errors=errors)
            _audit_current_snapshot(state_text, label=f"{topic}/state.md", errors=errors)

            gates_fm = frontmatter(gates_text)
            if gates_fm.get("schema") != "topic_gates":
                errors.append(f"{topic}: invalid gates schema")
            if gates_fm.get("topic") != topic:
                errors.append(f"{topic}: gates.topic mismatch")

            ev_fm = frontmatter(evidence_text)
            if ev_fm.get("schema") != "topic_evidence" or ev_fm.get("topic") != topic or ev_fm.get("mutation") != "APPEND_ONLY":
                errors.append(f"{topic}: invalid evidence ledger frontmatter")
            notes_fm = frontmatter(notes_text)
            if notes_fm.get("schema") != "topic_notes" or notes_fm.get("topic") != topic:
                errors.append(f"{topic}: invalid notes frontmatter")
            _audit_required_headings(
                notes_text,
                NOTES_SECTION_ORDER,
                level=2,
                label=f"{topic}/notes.md",
                errors=errors,
            )

            _validate_evidence_ledger(topic, evidence_text, errors)
            entries = evidence_entries(evidence_text, topic)
            evidence_by_id = {
                x.evidence_id: (
                    evidence_field(x.text, "Gate"),
                    evidence_field(x.text, "Result"),
                    evidence_field(x.text, "Assistance"),
                )
                for x in entries
            }
            ids = set(evidence_by_id)

            gids = gate_ids(gates_text)
            gid = state.get("current_gate", "NONE")
            if gid != "NONE" and gid not in gids:
                errors.append(f"{topic}: current_gate missing")
            for gate_id in gids:
                block = extract_gate(gates_text, gate_id)
                _audit_required_headings(
                    block,
                    GATE_REQUIRED_SECTIONS,
                    level=3,
                    label=f"{topic}: {gate_id}",
                    errors=errors,
                )
                status_fields = re.findall(r"(?m)^Status:\s*`?[A-Z_]+`?\s*$", block)
                if len(status_fields) != 1:
                    errors.append(f"{topic}: {gate_id} must contain exactly one Status field; found {len(status_fields)}")
                status = gate_status(gates_text, gate_id)
                if status not in GATE_STATUS:
                    errors.append(f"{topic}: {gate_id} invalid Gate status={status}")
                criteria = gate_criterion_ids(block)
                mandatory = gate_mandatory_ids(block)
                progress = gate_progress(block)
                if set(progress) - criteria:
                    errors.append(f"{topic}: {gate_id} Criterion Progress contains unknown criteria")
                for cid in mandatory:
                    if cid not in progress:
                        errors.append(f"{topic}: {gate_id} missing progress for mandatory {cid}")
                for cid, value in progress.items():
                    if value not in CRITERION_STATUS:
                        errors.append(f"{topic}: {gate_id} invalid progress {cid}={value}")
                maximum = gate_max_assistance(block)
                if maximum not in ASSISTANCE:
                    errors.append(f"{topic}: {gate_id} invalid/missing Allowed Assistance Maximum")
                refs = evidence_refs(section(block, "Evidence References", level=3), topic)
                missing_gate_refs = sorted(set(refs) - ids)
                if missing_gate_refs:
                    errors.append(f"{topic}: {gate_id} missing Evidence refs: {', '.join(missing_gate_refs)}")
                if status == "PASSED":
                    if any(progress.get(cid) != "VERIFIED" for cid in mandatory):
                        errors.append(f"{topic}: {gate_id} PASSED but mandatory criteria not all VERIFIED")
                    if not refs:
                        errors.append(f"{topic}: {gate_id} PASSED without Evidence References")
                    elif maximum in ASSISTANCE and not gate_has_qualifying_pass_evidence(gate_id, maximum, refs, evidence_by_id):
                        errors.append(
                            f"{topic}: {gate_id} PASSED without PASS Evidence within Assistance <= {maximum}"
                        )

            refs = set(evidence_refs(state_text + "\n" + gates_text, topic))
            missing_refs = sorted(refs - ids)
            if missing_refs:
                errors.append(f"{topic}: missing Evidence refs: {', '.join(missing_refs)}")
            if check_git_append_only:
                _append_only_check(topic, evidence_text, errors)

    if current != "NONE" and current not in live:
        errors.append("current_topic has no live Topic")
    if current != "NONE" and current in states and action == "TUTOR":
        current_state = states[current]
        current_gate = current_state.get("current_gate", "NONE")
        if current_state.get("status") != "ACTIVE":
            errors.append(f"current Topic must be ACTIVE for TUTOR route: {current_state.get('status')}")
        if current_gate == "NONE":
            errors.append("current_action=TUTOR requires a current_gate")
        if checkpoint == "NONE":
            errors.append("current_action=TUTOR requires a master_checkpoint")
        elif current_gate != "NONE" and checkpoint != current_gate:
            errors.append(f"master_checkpoint/current_gate drift: {checkpoint} != {current_gate}")
        if current_gate != "NONE" and current in gates_texts:
            current_gate_status = gate_status(gates_texts[current], current_gate)
            if current_gate_status in {"DRAFT", "RETIRED"}:
                errors.append(
                    f"current_action=TUTOR cannot use current Gate status={current_gate_status}: {current_gate}"
                )
            if current_gate_status == "BLOCKED" and current_state.get("master_review_required") != "true":
                errors.append(
                    f"current Gate BLOCKED requires master_review_required=true before routing away from Tutor: {current_gate}"
                )

    route = trigger = reason = None
    if not errors:
        if current == "NONE":
            route, trigger, reason = "MASTER_REVIEW", "NONE", "no current learning topic"
        else:
            state = states[current]
            gates_text = gates_texts[current]
            current_gate = state.get("current_gate", "NONE")
            if checkpoint != "NONE" and checkpoint not in gate_ids(gates_text):
                errors.append(f"master_checkpoint does not exist in current Topic: {checkpoint}")
            elif current_gate != "NONE" and gate_status(gates_text, current_gate) == "PASSED":
                route, trigger, reason = "MASTER_REVIEW", current, f"current Gate already PASSED: {current_gate}"
            elif state.get("master_review_required") == "true":
                route, trigger, reason = "MASTER_REVIEW", current, "master_review_required=true"
            elif checkpoint != "NONE" and gate_status(gates_text, checkpoint) == "PASSED":
                route, trigger, reason = "MASTER_REVIEW", current, "master checkpoint reached: " + checkpoint
            elif action == "MASTER_REVIEW":
                route, trigger, reason = "MASTER_REVIEW", current, "master_outline current_action=MASTER_REVIEW"
            else:
                route, trigger, reason = "TUTOR", current, "continue current Master Directive"

    return AuditResult(errors, warnings, live, current, route, trigger, reason)
