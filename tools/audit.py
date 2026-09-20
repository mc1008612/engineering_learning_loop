"""
Engineering Learning Loop 的 Repo 审计 CLI。

运行逻辑：读取 00_global/ 与 01_topics/，检查核心 schema、枚举、Gate/Evidence 引用、
Evidence append-only、Gate PASS 的 Assistance 上限等机械约束；可同时输出长期 Repo 的 route。
本脚本只读，不修改 Repo，也不判断课程语义。
"""

from __future__ import annotations

import argparse

from lib.repo import audit_repository


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="检查 Engineering Learning Loop 长期 Repo 状态的一致性；只读，不修改任何文件。",
        epilog=(
            "示例：\n"
            "  python tools/audit.py\n"
            "  python tools/audit.py --route\n\n"
            "谁会运行：Codex、Human 排障或其他工具。\n"
            "注意：学习流程下一步应优先使用 `python tools/learning.py status`；audit 只看长期 Repo，不处理 Pending Lesson。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--route",
        action="store_true",
        help="除 audit 结果外，输出长期 Repo 的机械 ROUTE / TRIGGER / REASON。",
    )
    return ap


def main() -> int:
    args = parser().parse_args()
    result = audit_repository(check_git_append_only=True)
    if result.errors:
        print("REPO AUDIT: FAIL")
        for item in result.errors:
            print("- " + item)
        return 1

    print("REPO AUDIT: PASS")
    print("live_topics=" + str(len(result.live_topics)))
    print("current_topic=" + result.current_topic)
    for warning in result.warnings:
        print("WARN: " + warning)
    if args.route:
        print("\nROUTE:\n" + str(result.route))
        print("\nTRIGGER:\n" + str(result.trigger))
        print("\nREASON:\n" + str(result.reason))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
