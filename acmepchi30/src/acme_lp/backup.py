"""备份、还原与清单校验。"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from . import paths


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_backup(language_dir: Path, uilanguage_dat: Path) -> Path:
    """整目录备份语言资源与 uilanguage.dat，返回备份目录。"""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = paths.BACKUP_ROOT / stamp
    dest.mkdir(parents=True, exist_ok=True)

    shutil.copytree(language_dir, dest / language_dir.name, dirs_exist_ok=True)
    if uilanguage_dat.exists():
        shutil.copy2(uilanguage_dat, dest / uilanguage_dat.name)

    manifest = {
        "created": stamp,
        "language_dir": str(language_dir),
        "uilanguage": paths.read_uilanguage(language_dir.parent),
        "files": {
            p.relative_to(dest).as_posix(): {"size": p.stat().st_size, "sha256": _sha256(p)}
            for p in sorted(dest.rglob("*"))
            if p.is_file() and p.name != "manifest.json"
        },
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def latest_backup(language_dir_name: str | None = None) -> Path | None:
    """最近一份备份；给定语言目录名时只认含该目录的备份（如 en）。"""
    if not paths.BACKUP_ROOT.exists():
        return None
    items = [p for p in paths.BACKUP_ROOT.iterdir() if p.is_dir() and (p / "manifest.json").exists()]
    if language_dir_name:
        items = [p for p in items if (p / language_dir_name).is_dir()]
    return max(items, key=lambda p: p.name) if items else None


def restore(backup_dir: Path, language_dir: Path, uilanguage_dat: Path) -> dict:
    """按备份还原，返回统计信息。"""
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    restored, mismatched = 0, []
    src_root = backup_dir / language_dir.name
    if src_root.exists():
        language_dir.mkdir(parents=True, exist_ok=True)
        for item in sorted(src_root.iterdir()):
            if item.is_file():
                shutil.copy2(item, language_dir / item.name)
                restored += 1

    backup_dat = backup_dir / uilanguage_dat.name
    if backup_dat.exists():
        shutil.copy2(backup_dat, uilanguage_dat)

    for rel, info in manifest.get("files", {}).items():
        actual = backup_dir / rel
        if actual.exists() and _sha256(actual) != info["sha256"]:
            mismatched.append(rel)

    return {"backup": str(backup_dir), "restored": restored, "uilanguage": manifest.get("uilanguage", ""), "mismatched": mismatched}
