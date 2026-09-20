"""
Engineering Learning Loop 的学习流程统一入口。

运行逻辑：
1. `status` 检查 Git、Repo audit、未提交学习状态、Pending Handoff 与 Pending Lesson，
   按固定优先级输出 CURRENT_STATE 和 NEXT_ACTION；需要 Master Review 时刷新本地 Master Context。
2. `master-review` 为 Human 明确要求调整既有 roadmap 顺序时提供只读 Master Review 入口；不会修改长期学习文件。
3. `start-tutor` 仅在 READY_FOR_TUTOR 时创建新的 Tutor Context/Start Prompt，并原子建立 `.runtime/tutor_transaction.json`。
4. `collect-handoff` 仅在 PENDING_LESSON 时，从配置的 Downloads 目录把候选文件暂存到 `.runtime/incoming/`，
   先验证，PASS 后才原子 promote 到 `.runtime/handoff/`；无效/STALE 文件不会推进为 PENDING_HANDOFF。
   Human 在 PENDING_HANDOFF preview 后拒绝 Tutor 的语义判断时，可用 `--replace --confirm <lesson_id>` 收取 Tutor 的完整修订版。
5. `discard-lesson` 仅在 Human 明确确认且当前为 PENDING_LESSON 时删除该 Lesson 的 runtime Context/Prompt/transaction pointer，不修改长期学习事实。

本脚本保证串行学习事务；它不做 Master 课程语义决策，也不自动 apply Handoff 或 commit。
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from lib.context import (
    build_master_context,
    build_tutor_context,
    tutor_prompt_filename,
)
from lib.flow import clear_tutor_transaction, create_tutor_transaction, current_flow_status
from lib.handoff import validate_handoff
from lib.local_io import (
    copy_to_system_clipboard,
    handoff_download_candidates,
    load_settings,
    open_url,
    promote_staged_handoff,
    replace_staged_handoff,
    resolve_downloads_dir,
    save_settings,
    stage_handoff_download,
)
from lib.render import render_flow_status, render_tutor_start_prompt
from lib.repo import ROOT, RUNTIME, frontmatter, rd, wr


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="学习流程统一入口：查看下一步、发起只读 Master Review、启动 Web Tutor、收取 Handoff 或显式放弃未完成 Lesson。",
        epilog=(
            "日常建议：Human 只需在 Codex 中说“我想开始/继续今天的学习”；Codex 先运行本脚本的 status。\n\n"
            "常见示例：\n"
            "  python tools/learning.py\n"
            "  python tools/learning.py status\n"
            "  python tools/learning.py master-review\n"
            "  python tools/learning.py start-tutor --url https://example.com\n"
            "  python tools/learning.py collect-handoff --downloads-dir ~/Downloads\n"
            "  python tools/learning.py collect-handoff --source '... (1).md' --replace --confirm <lesson_id>\n"
            "  python tools/learning.py discard-lesson --confirm <lesson_id>\n\n"
            "本脚本不会自动批准 Master Plan、不会自动发送 Web 消息、不会自动 apply Handoff、不会 commit。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="command", metavar="COMMAND")

    status = sub.add_parser(
        "status",
        help="显示当前串行学习状态与 NEXT_ACTION；不修改长期学习事实。",
        description="检查所有学习事务边界并显示当前唯一合法的下一步。MASTER_REVIEW 时会刷新 .runtime/context/MASTER_CONTEXT.md。",
        epilog=("谁会运行：Codex 日常学习请求的第一步；Human 也可直接排障。\n"
                "前提：Repo 已 git init 且长期文件可通过 audit。\n"
                "长期状态写入：无；仅可能刷新 .runtime/context/MASTER_CONTEXT.md。\n"
                "下一步：严格按照输出的 NEXT_ACTION 继续。"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


    master_review = sub.add_parser(
        "master-review",
        help="Human 明确要求调整现有 Topic 顺序/roadmap 时，生成只读 Master Context；不改变机械状态。",
        description=(
            "只用于 clean MASTER_REVIEW 或 READY_FOR_TUTOR。它不会写 00_global/ 或 01_topics/，"
            "也不会创建持久 review flag；Human 当前自然语言请求仍由 Codex 作为规划输入。"
        ),
        epilog=(
            "适用：Human 明确要求暂停当前 Topic 一段时间、先学另一个既有方向、调整当前 roadmap 顺序。\n"
            "不适用：仅仅‘今天不想学当前 Topic’这类 session-local 暂缓；这种情况可以什么都不改。\n"
            "不支持：把整个长期学习领域替换成无关领域；当前版本不自动迁移这类根级目标。\n"
            "前提：不能有 Pending Lesson/Handoff 或待 review/commit 的 learning changes。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    start = sub.add_parser(
        "start-tutor",
        help="在 READY_FOR_TUTOR 时创建 Tutor Context/Prompt，并准备浏览器与剪贴板。",
        description="只有没有 Pending Lesson/Handoff/学习状态 diff 且长期 route=TUTOR 时才允许创建新 Lesson。",
        epilog=("谁会运行：通常由 Codex 在 Human 明确要开课后运行。\n"
                "长期状态写入：无；只写 .runtime/context、.runtime/prompts、tutor_transaction.json 和本机配置。\n"
                "成功后：Human 上传 Context、粘贴 Prompt、追加个性化要求并手动发送。\n"
                "注意：Context 创建后立即进入 PENDING_LESSON。"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    start.add_argument("--url", help="Tutor 网页 URL；提供后保存到 .runtime/local_settings.json。")
    start.add_argument(
        "--downloads-dir",
        help="浏览器下载目录；可同时保存，供之后 collect-handoff 使用，例如 ~/Downloads。",
    )

    collect = sub.add_parser(
        "collect-handoff",
        help="从配置的 Downloads 目录精确收取当前 Lesson 的 Handoff，并自动 validate。",
        description=(
            "默认寻找 Context 指定的精确文件名；先 copy 到 .runtime/incoming/ 并 validate，PASS 后才 promote 到 .runtime/handoff/。"
        ),
        epilog=("谁会运行：通常由 Codex 在 Human 表示 Web Tutor 已结束课程后运行。\n"
                "前提：CURRENT_STATE=PENDING_LESSON，且浏览器已下载精确命名的 Handoff。\n"
                "如果浏览器生成 (1) 等修正版，Human/Codex 明确确认后可用 --source 指定该文件名；脚本不自动猜。\n"
                "如果 Handoff 已进入 PENDING_HANDOFF，但 Human preview 后发现课堂语义不准确，应先回 Tutor 商议并生成完整修正版，再使用 --replace --confirm <lesson_id> 原子替换。\n"
                "长期状态写入：无；invalid/STALE 文件不会留下正式 local Handoff。\n"
                "成功后：运行 handoff.py preview，Human review 后才 apply。"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    collect.add_argument(
        "--downloads-dir",
        help="本次指定并保存浏览器下载目录；省略时使用 .runtime/local_settings.json。",
    )
    collect.add_argument(
        "--source",
        metavar="FILENAME",
        help="显式选择 Downloads 目录中的某个候选文件名，例如浏览器生成的 '... (1).md'；不会自动猜候选。",
    )
    collect.add_argument(
        "--replace",
        action="store_true",
        help="仅在 PENDING_HANDOFF 使用：将已通过验证的 Tutor 完整修订版原子替换当前正式 Handoff；不会修改长期学习文件。",
    )
    collect.add_argument(
        "--confirm",
        metavar="LESSON_ID",
        help="配合 --replace 使用，必须精确填写当前 Pending Lesson ID，防止误替换。",
    )

    discard = sub.add_parser(
        "discard-lesson",
        help="显式放弃尚未 Close 的 Pending Lesson；不修改长期学习事实。",
        description="仅用于该 Lesson 实际没有进行或确定不保留任何结果的情况。必须用 lesson_id 明确确认。",
        epilog=("谁会运行：Codex，但必须先得到 Human 对当前 Lesson 的明确放弃指示。\n"
                "前提：CURRENT_STATE=PENDING_LESSON；PENDING_HANDOFF 不允许静默 Discard。\n"
                "写入：只删除该 Lesson 的 runtime Context/Prompt/transaction pointer，不修改 State/Gate/Evidence/Notes。\n"
                "成功后：重新运行 learning.py status。"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    discard.add_argument(
        "--confirm",
        required=True,
        metavar="LESSON_ID",
        help="必须精确填写当前 Pending Lesson ID，防止误操作。",
    )
    return ap


def show_status() -> int:
    status = current_flow_status()
    master_context = None
    if status.state == "MASTER_REVIEW":
        try:
            master_context = build_master_context(status.audit.trigger)
        except ValueError as exc:
            print("CURRENT_STATE: REPO_ERROR")
            print("\n原因：Master Context 生成失败：" + str(exc))
            print("\nNEXT_ACTION:\n先修复 Repo，再重新运行 status。")
            return 1
    print(render_flow_status(status, master_context), end="")
    return 1 if status.state == "REPO_ERROR" else 0


def request_master_review() -> int:
    """Human-requested roadmap review 的只读入口；不改变长期 route，也不持久化 Human 请求。"""
    status = current_flow_status()
    if status.state not in {"READY_FOR_TUTOR", "MASTER_REVIEW"}:
        print("BLOCKED: 当前存在更高优先级事务，不能先做 roadmap Master Review。", file=sys.stderr)
        print(render_flow_status(status), file=sys.stderr, end="")
        return 4

    trigger = status.audit.trigger if status.state == "MASTER_REVIEW" else status.audit.current_topic
    try:
        context_path = build_master_context(trigger)
    except ValueError as exc:
        print("FAIL: Master Context 生成失败：" + str(exc), file=sys.stderr)
        return 1

    print("MASTER REVIEW CONTEXT READY")
    print("source_state=" + status.state)
    print("context=" + context_path.relative_to(ROOT).as_posix())
    print("long_term_mutation=NONE")
    print("\nNEXT_ACTION:")
    print("Codex 使用该 Context + Human 当前 roadmap-order 请求进行只读 Master Review，输出完整中文 MASTER PLAN。")
    print("Human 批准前不得修改 00_global/ 或 01_topics/。")
    return 0


def start_tutor(url: str | None, downloads_dir: str | None) -> int:
    settings = save_settings({"tutor_url": url, "downloads_dir": downloads_dir}) if (url or downloads_dir) else load_settings()
    tutor_url = settings.get("tutor_url")
    if not tutor_url:
        print("BLOCKED: 尚未配置 tutor_url。", file=sys.stderr)
        print("首次运行示例：python tools/learning.py start-tutor --url https://...", file=sys.stderr)
        return 2

    status = current_flow_status()
    if status.state != "READY_FOR_TUTOR":
        print("BLOCKED: 当前状态不允许创建新的 Tutor Lesson。", file=sys.stderr)
        print(render_flow_status(status), file=sys.stderr, end="")
        return 4

    try:
        context_path = build_tutor_context()
        fm = frontmatter(rd(context_path))
        lesson_id = fm["lesson_id"]
        handoff_filename = fm["handoff_filename"]
        prompt_text = render_tutor_start_prompt(context_path, lesson_id, handoff_filename)
        prompt_path = RUNTIME / "prompts" / tutor_prompt_filename(lesson_id)
        wr(prompt_path, prompt_text)
        create_tutor_transaction(
            lesson_id=lesson_id,
            topic=fm["topic"],
            gate=fm["current_gate"],
            context_path=context_path,
            prompt_path=prompt_path,
            handoff_filename=handoff_filename,
        )
    except Exception as exc:
        print("FAIL: 无法准备 Tutor Lesson：" + str(exc), file=sys.stderr)
        return 1

    clip_ok, clip_message = copy_to_system_clipboard(prompt_text)
    browser_ok, browser_message = open_url(tutor_url)

    print("TUTOR LESSON READY")
    print("lesson_id=" + lesson_id)
    print("context=" + context_path.relative_to(ROOT).as_posix())
    print("prompt=" + prompt_path.relative_to(ROOT).as_posix())
    print("expected_handoff=" + handoff_filename)
    print("clipboard=" + ("OK" if clip_ok else "WARN"))
    print("browser=" + ("OK" if browser_ok else "WARN"))
    if not clip_ok:
        print("WARN: " + clip_message)
    if not browser_ok:
        print("WARN: " + browser_message)

    print("\nNEXT_ACTION:")
    print("1. 在 Web Tutor 中上传上面的 Context 文件。")
    print("2. Ctrl+V 粘贴标准开课 Prompt；若剪贴板不可用，从 Prompt 文件手工复制。")
    print("3. 在末尾追加本课个性化要求。")
    print("4. Human 手动发送。")
    print("5. Lesson Close 或显式 Discard 前，系统不会创建下一 Lesson。")
    return 0


def collect_handoff(downloads_dir: str | None, source: str | None, replace: bool, confirm: str | None) -> int:
    settings = save_settings({"downloads_dir": downloads_dir}) if downloads_dir else load_settings()
    configured = settings.get("downloads_dir")
    if not configured:
        print("BLOCKED: 尚未配置 downloads_dir。", file=sys.stderr)
        print("示例：python tools/learning.py collect-handoff --downloads-dir ~/Downloads", file=sys.stderr)
        return 2

    status = current_flow_status()
    if status.state == "PENDING_HANDOFF":
        if status.dirty_learning_files:
            print("BLOCKED: 当前 Lesson/Handoff 事务期间存在并行 learning-state 修改。", file=sys.stderr)
            print("先 revert/stash/另存这些修改，恢复开课时 00_global/ 与 01_topics/ 状态；不要 commit。", file=sys.stderr)
            return 4
        if not replace:
            if source is not None:
                print("BLOCKED: 当前已是 PENDING_HANDOFF；--source 不会静默覆盖正式 Handoff。", file=sys.stderr)
                print("若这是 Tutor 在 Human review 后输出的完整修订版，请同时使用 --replace --confirm <lesson_id>。", file=sys.stderr)
                return 2
            print("当前 Handoff 已经收取：" + status.handoff_path.relative_to(ROOT).as_posix())
            print("NEXT_ACTION: 运行 `python tools/handoff.py preview <handoff>`；若 Human 拒绝其课堂语义，让 Tutor 重做完整 Handoff 后用 --replace 收取。")
            return 0
        if not status.pending_lesson:
            print("BLOCKED: 无法识别当前 Pending Lesson。", file=sys.stderr)
            return 4
        lesson = status.pending_lesson
        if not source:
            print("BLOCKED: --replace 必须显式提供 Tutor 修订版 --source <FILENAME>。", file=sys.stderr)
            return 2
        if confirm != lesson.lesson_id:
            print("BLOCKED: --replace 的 --confirm 必须精确等于当前 Lesson ID。", file=sys.stderr)
            print("当前 Lesson: " + lesson.lesson_id, file=sys.stderr)
            return 2
        source_dir = resolve_downloads_dir(configured)
        staged, candidates, message = stage_handoff_download(
            source_dir,
            lesson.handoff_filename,
            RUNTIME / "incoming",
            source_filename=source,
        )
        print(message)
        if staged is None:
            if candidates:
                print("\nPossible candidates（不会自动选择）：")
                for item in candidates:
                    print("- " + item.name)
            return 3
        try:
            result = validate_handoff(staged)
        except RuntimeError as exc:
            staged.unlink(missing_ok=True)
            print(str(exc), file=sys.stderr)
            print("NEXT_ACTION: 修订版为 STALE，未替换当前正式 Handoff；先恢复/检查 Repo。", file=sys.stderr)
            return 3
        except ValueError as exc:
            staged.unlink(missing_ok=True)
            print("HANDOFF VALIDATION: FAIL", file=sys.stderr)
            print(str(exc), file=sys.stderr)
            print("NEXT_ACTION: 当前正式 Handoff 未改变；回 Tutor 修正完整 Handoff 后再 replace。", file=sys.stderr)
            return 1
        try:
            destination = replace_staged_handoff(staged, RUNTIME / "handoff", lesson.handoff_filename)
        except ValueError as exc:
            staged.unlink(missing_ok=True)
            print("HANDOFF REPLACE: FAIL", file=sys.stderr)
            print(str(exc), file=sys.stderr)
            return 1
        print("HANDOFF VALIDATION: PASS")
        print("HANDOFF REPLACE: PASS")
        print("lesson_id=" + result.meta["lesson_id"])
        print("local_handoff=" + destination.relative_to(ROOT).as_posix())
        print("\nNEXT_ACTION:")
        print(f"重新运行 `python tools/handoff.py preview {destination.relative_to(ROOT).as_posix()}`，由 Human 再次 review。")
        return 0
    if replace:
        print("BLOCKED: --replace 只允许在 PENDING_HANDOFF 使用。首次收取请去掉 --replace。", file=sys.stderr)
        return 2
    if status.state != "PENDING_LESSON" or not status.pending_lesson:
        print("BLOCKED: 当前没有可收取 Handoff 的 Pending Lesson。", file=sys.stderr)
        print(render_flow_status(status), file=sys.stderr, end="")
        return 4

    if status.dirty_learning_files:
        print("BLOCKED: Tutor Context 创建后检测到并行 learning-state 修改。", file=sys.stderr)
        print("先 revert/stash/另存这些修改，恢复开课时 00_global/ 与 01_topics/ 状态；不要 commit。", file=sys.stderr)
        return 4

    lesson = status.pending_lesson
    source_dir = resolve_downloads_dir(configured)
    staged, candidates, message = stage_handoff_download(
        source_dir,
        lesson.handoff_filename,
        RUNTIME / "incoming",
        source_filename=source,
    )
    print(message)
    if staged is None:
        if candidates:
            print("\nPossible candidates（不会自动选择）：")
            for item in candidates:
                print("- " + item.name)
        print("\nNEXT_ACTION:")
        print("确认 Web Tutor 已下载 Handoff。若要使用浏览器生成的 (1) 等候选，明确确认后用 `--source <文件名>` 重试。")
        return 3

    try:
        result = validate_handoff(staged)
    except RuntimeError as exc:
        staged.unlink(missing_ok=True)
        print(str(exc), file=sys.stderr)
        print("NEXT_ACTION: 该 Handoff 为 STALE，未进入正式 .runtime/handoff/；先重新检查当前 Repo。", file=sys.stderr)
        return 3
    except ValueError as exc:
        staged.unlink(missing_ok=True)
        print("HANDOFF VALIDATION: FAIL", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        alternatives = handoff_download_candidates(source_dir, lesson.handoff_filename)
        if alternatives:
            print("\nPossible candidates（不会自动选择）：", file=sys.stderr)
            for item in alternatives:
                print("- " + item.name, file=sys.stderr)
        print(
            "NEXT_ACTION: 该文件未进入正式 .runtime/handoff/。让 Tutor 修正/重新下载后再次 collect；若浏览器生成 (1) 文件，可明确用 --source 选择。",
            file=sys.stderr,
        )
        return 1

    try:
        destination = promote_staged_handoff(staged, RUNTIME / "handoff", lesson.handoff_filename)
    except ValueError as exc:
        staged.unlink(missing_ok=True)
        print("HANDOFF PROMOTE: FAIL", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print("HANDOFF VALIDATION: PASS")
    print("HANDOFF PROMOTE: PASS")
    print("lesson_id=" + result.meta["lesson_id"])
    print("local_handoff=" + destination.relative_to(ROOT).as_posix())
    print("\nNEXT_ACTION:")
    print(f"运行 `python tools/handoff.py preview {destination.relative_to(ROOT).as_posix()}`，由 Human review 后再 apply。")
    return 0


def discard_lesson(confirm: str) -> int:
    status = current_flow_status()
    if status.state != "PENDING_LESSON" or not status.pending_lesson:
        print("BLOCKED: 只有 PENDING_LESSON 可以显式 Discard。", file=sys.stderr)
        print(render_flow_status(status), file=sys.stderr, end="")
        return 4
    lesson = status.pending_lesson
    if confirm != lesson.lesson_id:
        print("BLOCKED: --confirm 与当前 Pending Lesson ID 不一致。", file=sys.stderr)
        print("当前 Lesson: " + lesson.lesson_id, file=sys.stderr)
        return 2

    removed: list[Path] = []
    if lesson.context_path.exists():
        lesson.context_path.unlink()
        removed.append(lesson.context_path)
    if lesson.prompt_path.exists():
        lesson.prompt_path.unlink()
        removed.append(lesson.prompt_path)
    try:
        clear_tutor_transaction(lesson.lesson_id)
    except ValueError as exc:
        print("FAIL: 无法安全清除 Tutor transaction：" + str(exc), file=sys.stderr)
        return 1

    print("PENDING LESSON DISCARDED")
    print("lesson_id=" + lesson.lesson_id)
    for path in removed:
        print("- removed " + path.relative_to(ROOT).as_posix())
    print("长期 State/Gate/Evidence/Notes 未修改。")
    print("\nNEXT_ACTION:")
    print("重新运行 `python tools/learning.py status`。")
    return 0


def main() -> int:
    args = parser().parse_args()
    command = args.command or "status"
    if command == "status":
        return show_status()
    if command == "master-review":
        return request_master_review()
    if command == "start-tutor":
        return start_tutor(args.url, args.downloads_dir)
    if command == "collect-handoff":
        return collect_handoff(args.downloads_dir, args.source, args.replace, args.confirm)
    if command == "discard-lesson":
        return discard_lesson(args.confirm)
    raise AssertionError(command)


if __name__ == "__main__":
    raise SystemExit(main())
