"""
Engineering Learning Loop 的本机 I/O 辅助模块。

本模块只处理不进入 Git 的本机便利功能：
- `.runtime/local_settings.json`；
- 系统剪贴板；
- 默认浏览器；
- 浏览器 Downloads 目录中的 Handoff 查找、临时 staging、原子 promote，以及 Human review 后 Tutor 修订版的显式原子 replace。

它不判断课程状态，也不修改 00_global/ 或 01_topics/。
"""

from __future__ import annotations

from pathlib import Path
import base64
import json
import os
import platform
import shutil
import subprocess
import webbrowser

from .repo import RUNTIME, rd, sha, wr

SETTINGS_PATH = RUNTIME / "local_settings.json"


def load_settings() -> dict[str, str]:
    if not SETTINGS_PATH.is_file():
        return {}
    try:
        value = json.loads(rd(SETTINGS_PATH))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"无法读取 {SETTINGS_PATH}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("local_settings.json 必须是 JSON object")
    return {str(k): str(v) for k, v in value.items() if v is not None}


def save_settings(updates: dict[str, str | None]) -> dict[str, str]:
    settings = load_settings()
    for key, value in updates.items():
        if value is not None:
            settings[key] = str(value)
    wr(SETTINGS_PATH, json.dumps(settings, ensure_ascii=False, indent=2) + "\n")
    return settings


def copy_to_system_clipboard(text: str) -> tuple[bool, str]:
    """仅使用系统命令；失败时返回 warning，不抛出异常。"""
    system = platform.system().lower()
    # 每个候选为 (命令, stdin 内容, stdin 编码)；编码为 None 表示不写 stdin。
    candidates: list[tuple[list[str], str | None, str | None]] = []
    if system == "windows":
        # PowerShell 把管道 stdin 按系统代码页（中文 Windows 为 GBK）解码，直接传
        # UTF-8 文本会变成乱码；经 base64 传输再按 UTF-8 还原，与代码页完全无关。
        b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
        candidates = [
            (
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Set-Clipboard -Value ([Text.Encoding]::UTF8.GetString"
                    f"([Convert]::FromBase64String('{b64}')))",
                ],
                None,
                None,
            ),
            # clip.exe 只认带 BOM 的 Unicode 文本；Python 的 "utf-16" 编码会自带 BOM。
            (["clip"], text, "utf-16"),
        ]
    elif system == "darwin":
        candidates = [(["pbcopy"], text, "utf-8")]
    else:
        candidates = [
            (["wl-copy"], text, "utf-8"),
            (["xclip", "-selection", "clipboard"], text, "utf-8"),
            (["xsel", "--clipboard", "--input"], text, "utf-8"),
        ]

    for cmd, payload, encoding in candidates:
        if shutil.which(cmd[0]) is None:
            continue
        try:
            p = subprocess.run(
                cmd, input=payload, text=encoding is not None, encoding=encoding, check=False
            )
            if p.returncode == 0:
                return True, cmd[0]
        except OSError:
            continue
    return False, "系统剪贴板命令不可用；Prompt 已保存为文件，可手工复制。"


def open_url(url: str) -> tuple[bool, str]:
    try:
        ok = webbrowser.open(url, new=2)
        return (ok, "已请求默认浏览器打开 Tutor URL。" if ok else "默认浏览器未确认打开；请手工打开配置的 Tutor URL。")
    except webbrowser.Error as exc:
        return False, f"浏览器打开失败：{exc}"


def resolve_downloads_dir(value: str) -> Path:
    return Path(os.path.expandvars(value)).expanduser().resolve()


def handoff_download_candidates(downloads_dir: Path, expected_filename: str) -> list[Path]:
    """返回与 expected handoff 同 stem 的浏览器重复下载候选，不自动选择。"""
    if not downloads_dir.is_dir():
        return []
    stem = Path(expected_filename).stem
    suffix = Path(expected_filename).suffix
    exact = downloads_dir / expected_filename
    return [p for p in sorted(downloads_dir.glob(stem + "*" + suffix)) if p != exact]


def stage_handoff_download(
    downloads_dir: Path,
    expected_filename: str,
    incoming_dir: Path,
    source_filename: str | None = None,
) -> tuple[Path | None, list[Path], str]:
    """把明确的 Downloads 源文件 copy 到 incoming；正式 Handoff 只有 validate PASS 后才能 promote。"""
    if not downloads_dir.is_dir():
        return None, [], f"Downloads 目录不存在：{downloads_dir}"

    if source_filename is not None:
        source_name = Path(source_filename)
        if source_name.name != source_filename or source_name.is_absolute():
            return None, [], "--source 只接受配置 Downloads 目录中的单个文件名，不接受路径。"
        source = downloads_dir / source_filename
    else:
        source = downloads_dir / expected_filename

    if not source.is_file():
        candidates = handoff_download_candidates(downloads_dir, expected_filename)
        if source_filename:
            return None, candidates, f"指定的 Downloads 文件不存在：{source_filename}"
        return None, candidates, f"未找到精确文件：{expected_filename}"

    incoming_dir.mkdir(parents=True, exist_ok=True)
    staged = incoming_dir / expected_filename
    if staged.exists():
        staged.unlink()
    shutil.copy2(source, staged)
    return staged, handoff_download_candidates(downloads_dir, expected_filename), (
        f"Handoff 已从 Downloads 暂存到 .runtime/incoming/：{source.name}；正式收取前必须先通过 validate。"
    )


def promote_staged_handoff(staged: Path, destination_dir: Path, expected_filename: str) -> Path:
    """validate PASS 后把 incoming 原子 promote 为正式 local Handoff。"""
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / expected_filename
    if destination.exists():
        if sha(destination) == sha(staged):
            staged.unlink(missing_ok=True)
            return destination
        raise ValueError("正式 local Handoff 已存在但内容不同；拒绝覆盖。")
    os.replace(staged, destination)
    return destination


def replace_staged_handoff(staged: Path, destination_dir: Path, expected_filename: str) -> Path:
    """Human 拒绝已 promote 的语义内容后，用通过 validate 的 Tutor 修订版原子替换正式 Handoff。"""
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / expected_filename
    if not destination.is_file():
        raise ValueError("当前没有可替换的正式 local Handoff。")
    os.replace(staged, destination)
    return destination
