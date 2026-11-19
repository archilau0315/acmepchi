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


def build_plan(source_dir: Path, target_dir: Path) -> dict:
    """生成安装计划：可覆盖、已相同、源缺失、目标多余。"""
    src, dst = names(source_dir), names(target_dir)
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
        "missing_in_source": sorted(dst - src),
        "missing_in_target": sorted(src - dst),
    }
