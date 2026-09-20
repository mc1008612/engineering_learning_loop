"""
Engineering Learning Loop 的 Tutor Handoff 事务 CLI。

运行逻辑：
- `validate`：只验证 Handoff 与真实 Context/Repo 是否一致；
- `preview`：验证后显示确定性 patch，不写文件；
- `apply`：只在当前状态为 PENDING_HANDOFF 时应用 patch，随后 audit；失败自动回滚。

本 CLI 不重新解释 Tutor 的 Evidence 语义，也不自动 commit。Human 必须在 preview/apply 后审核 Git diff。
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from lib.flow import clear_tutor_transaction, current_flow_status
from lib.handoff import apply_validated_handoff, build_changes, unified_patch, validate_handoff
from lib.repo import ROOT


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="验证、预览或应用 Web Tutor 输出的结构化 TUTOR_HANDOFF。",
        epilog=(
            "典型流程：\n"
            "  python tools/handoff.py validate .runtime/handoff/TUTOR_HANDOFF_<lesson_id>.md\n"
            "  python tools/handoff.py preview  .runtime/handoff/TUTOR_HANDOFF_<lesson_id>.md\n"
            "  # Human review\n"
            "  python tools/handoff.py apply    .runtime/handoff/TUTOR_HANDOFF_<lesson_id>.md\n\n"
            "apply 只修改当前 Topic 的 state.md / gates.md / evidence.md / notes.md，不 commit。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="command", required=True, metavar="COMMAND")
    details = {
        "validate": (
            "机械验证 Handoff；不生成 patch，不写长期状态。",
            "谁会运行：collect-handoff 会自动调用；Codex/Human 也可单独排障。\n"
            "检查：schema、Context identity/hash、fingerprints、Evidence ID、Gate/Assistance 等。\n"
            "成功后：通常继续 preview。",
        ),
        "preview": (
            "机械验证并显示确定性 patch；不写长期状态。",
            "谁会运行：Codex，在 Human review Lesson Close 前运行。\n"
            "长期状态写入：无。\n"
            "成功后：Human 审核 Handoff 与 patch；明确确认后才 apply。",
        ),
        "apply": (
            "应用已经通过验证的 Handoff；失败自动回滚；不 commit。",
            "谁会运行：Codex，但必须在 CURRENT_STATE=PENDING_HANDOFF 且 Human 已 review 后运行。\n"
            "允许修改：当前 Topic 的 state.md/gates.md/evidence.md/notes.md。\n"
            "禁止：修改 Ability/Master Outline/工程源码或自动 commit。\n"
            "成功后：Human review Git diff、批准 commit，再运行 learning.py status。",
        ),
    }
    for name, (help_text, epilog) in details.items():
        sp = sub.add_parser(
            name, help=help_text, description=help_text, epilog=epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        sp.add_argument("handoff", help="Handoff Markdown 路径，通常位于 .runtime/handoff/；必须与当前 Tutor Context identity 绑定。")
    return ap


def _resolve(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


def main() -> int:
    args = parser().parse_args()
    path = _resolve(args.handoff)
    try:
        result = validate_handoff(path)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except ValueError as exc:
        print("FAIL:", exc, file=sys.stderr)
        return 1

    print("HANDOFF VALIDATED")
    print("topic=" + result.meta["topic"])
    print("gate=" + result.meta["gate"])
    print("lesson_id=" + result.meta["lesson_id"])
    print("master_review_required=" + result.meta["master_review_required"])
    print("context_file=" + str(result.context_path.relative_to(ROOT)))

    if args.command == "validate":
        print("\nNEXT_ACTION:")
        print("运行 `python tools/handoff.py preview <handoff>` 查看确定性 patch，再由 Human review。")
        return 0

    try:
        changes = build_changes(result)
    except (ValueError, RuntimeError) as exc:
        print("PATCH BUILD FAILED:", exc, file=sys.stderr)
        print("Repo/Handoff 结构不满足确定性 patch 合同；未写入任何长期学习文件。", file=sys.stderr)
        return 1
    print("\nPATCH:")
    print(unified_patch(changes))
    if args.command == "preview":
        print("\nNEXT_ACTION:")
        print("Human 审核 Handoff 与 patch；确认无误后运行 `python tools/handoff.py apply <handoff>`。")
        return 0

    flow = current_flow_status()
    if flow.state != "PENDING_HANDOFF" or not flow.handoff_path or flow.handoff_path.resolve() != path.resolve():
        print("\nBLOCKED:", file=sys.stderr)
        print(f"当前学习状态是 {flow.state}，该 Handoff 不是当前唯一待处理事务。", file=sys.stderr)
        print("先运行 `python tools/learning.py status`。", file=sys.stderr)
        return 4

    try:
        _, audit = apply_validated_handoff(result)
    except Exception as exc:
        print("APPLY FAILED; changes rolled back.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    transaction_warning = None
    try:
        clear_tutor_transaction(result.meta["lesson_id"])
    except ValueError as exc:
        transaction_warning = str(exc)

    print("\nAPPLY: PASS")
    print("POST_APPLY_ROUTE=" + str(audit.route))
    print("POST_APPLY_REASON=" + str(audit.reason))
    print("No commit was created.")
    if transaction_warning:
        print("WARN: 长期 Lesson 已 Close，但 runtime transaction pointer 清理失败：" + transaction_warning)
        print("状态机仍以 state.last_lesson_id 判定该事务已关闭；下次 start-tutor 会覆盖旧 pointer。")
    print("\nNEXT_ACTION:")
    print("Human 先审核 `git status --short` 与 `git diff`；确认后再明确批准 commit。")
    print("commit 完成后运行 `python tools/learning.py status` 恢复下一步。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
