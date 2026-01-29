import subprocess
from pathlib import Path
from typing import List


def open_local_file(path: str) -> None:
    if not path:
        return
    subprocess.Popen(["open", path])


def select_local_files() -> List[str]:
    script = "\n".join(
        [
            'set theFiles to choose file with prompt "选择文件" with multiple selections allowed',
            "set pathsText to \"\"",
            "repeat with aFile in theFiles",
            "set pathsText to pathsText & (POSIX path of aFile) & linefeed",
            "end repeat",
            "return pathsText",
        ]
    )
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def normalize_file_paths(text: str) -> List[str]:
    paths = []
    for raw in text.splitlines():
        value = raw.strip()
        if value:
            paths.append(value)
    return paths


def resolve_missing_paths(paths: List[str]) -> List[str]:
    missing = []
    for path in paths:
        if not Path(path).exists():
            missing.append(path)
    return missing


def select_local_folder() -> str:
    """使用 AppleScript 打开文件夹选择对话框"""
    script = 'set theFolder to choose folder with prompt "选择项目文件夹"\nreturn POSIX path of theFolder'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def open_folder_in_finder(path: str) -> None:
    """在 Finder 中打开文件夹"""
    if path:
        subprocess.Popen(["open", path])
