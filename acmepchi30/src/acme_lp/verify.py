"""资源比对与安装计划（不写盘）。"""

from __future__ import annotations

import hashlib
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def names(directory: Path) -> set[str]:
    if not directory.exists():
        return set()
    return {p.name for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".mui"}


def build_plan(source_dir: Path, target_dir: Path, exclude: tuple[str, ...] | list[str] = ()) -> dict:
    """生成安装计划：可覆盖、已相同、源缺失、目标多余。

    exclude 中的文件名永不替换（已知中文版会导致程序无法启动）。
    """
    skip = {name.lower() for name in exclude}
    all_src = names(source_dir)
    src = {name for name in all_src if name.lower() not in skip}
    dst = names(target_dir)
    to_copy, identical = [], []
    for name in sorted(src):
        target = target_dir / name
        if not target.exists():
            to_copy.append(name)
        elif _sha256(source_dir / name) == _sha256(target):
            identical.append(name)
        else:
            to_copy.append(name)
    return {
        "to_copy": to_copy,
        "identical": identical,
        "missing_in_source": sorted(dst - all_src),
        "missing_in_target": sorted(src - dst),
        "excluded": sorted(name for name in all_src if name.lower() in skip),
    }
