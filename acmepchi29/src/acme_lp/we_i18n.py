"""菜单标题汉化：用 Archicad 中文版的工作环境 XML 按 GUID 对齐翻译。

MEP Designer 的菜单分组标题（如 Architectural Tools）来自
`Defaults\\MEP Designer\\WorkEnvironment\\Command Layouts\\*.xml` 的 title 属性；
Archicad 中文版同名文件里同一 GUID 的 title 就是官方中文译法。
只改 title 文本，不动结构，因此不会引发资源不匹配导致的启动崩溃。
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from . import paths

MENU_TAG = re.compile(r"<Menu\b[^>]*>", re.IGNORECASE)
ATTR = re.compile(r'(\bID|title)="([^"]*)"')

AC_LAYOUT = Path("默认值") / "Archicad" / "工作环境" / "命令布置" / "标准命令.xml"
MEP_LAYOUT_DIR = Path("Defaults") / "MEP Designer" / "WorkEnvironment" / "Command Layouts"


def _titles(text: str) -> dict[str, str]:
    """提取 <Menu ID=... title=...> 的 GUID -> 标题映射。"""
    out = {}
    for tag in MENU_TAG.findall(text):
        attrs = dict(ATTR.findall(tag))
        guid, title = attrs.get("ID", "").lower(), attrs.get("title")
        if guid and title:
            out[guid] = title
    return out


def build_map(ac_dir: Path) -> dict[str, str]:
    layout = ac_dir / AC_LAYOUT
    if not layout.exists():
        return {}
    return _titles(layout.read_text(encoding="utf-8", errors="ignore"))


def _translate(text: str, mapping: dict[str, str]) -> tuple[str, int]:
    changed = 0

    def repl(match: re.Match) -> str:
        nonlocal changed
        tag = match.group(0)
        attrs = dict(ATTR.findall(tag))
        guid = attrs.get("ID", "").lower()
        zh = mapping.get(guid)
        if not zh or attrs.get("title") == zh:
            return tag
        changed += 1
        return re.sub(r'(\btitle=")[^"]*(")', lambda m: m.group(1) + zh + m.group(2), tag, count=1)

    return MENU_TAG.sub(repl, text), changed


def _we_files(mep_dir: Path) -> list[Path]:
    root = mep_dir / MEP_LAYOUT_DIR
    return sorted(root.glob("*.xml")) if root.exists() else []


def apply(cfg: dict, logger, dry_run: bool = False) -> dict:
    """把 MEP Designer 菜单标题替换为官方中文，返回统计信息。"""
    ac_dir = paths.find_product_dir(cfg, "source")
    mep_dir = paths.find_product_dir(cfg, "target")
    if not ac_dir or not mep_dir:
        raise RuntimeError("未找到 Archicad（来源）或 MEP Designer（目标）安装目录")

    mapping = build_map(ac_dir)
    if not mapping:
        raise RuntimeError(f"未找到中文工作环境文件：{ac_dir / AC_LAYOUT}")

    files = _we_files(mep_dir)
    if not files:
        raise RuntimeError(f"未找到 MEP 菜单定义目录：{mep_dir / MEP_LAYOUT_DIR}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = paths.BACKUP_ROOT / f"we-{stamp}"
    total = 0
    touched = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="surrogateescape")
        new_text, changed = _translate(text, mapping)
        if not changed:
            continue
        total += changed
        touched.append(f.name)
        if dry_run:
            continue
        dest = backup_dir / f.relative_to(mep_dir)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(f, dest)
        f.write_text(new_text, encoding="utf-8", errors="surrogateescape", newline="")

    if total:
        logger.info("菜单标题汉化 %d 处（%s）", total, ", ".join(touched))
    else:
        logger.info("菜单标题无需修改")
    return {"changed": total, "files": touched, "backup": str(backup_dir) if total and not dry_run else "", "map": len(mapping)}


def restore_latest(cfg: dict, logger) -> dict:
    """还原最近一次菜单汉化备份。"""
    if not paths.BACKUP_ROOT.exists():
        raise RuntimeError("没有可用的备份")
    dirs = sorted((d for d in paths.BACKUP_ROOT.iterdir() if d.is_dir() and d.name.startswith("we-")), reverse=True)
    if not dirs:
        raise RuntimeError("没有菜单汉化备份")
    mep_dir = paths.find_product_dir(cfg, "target")
    if not mep_dir:
        raise RuntimeError("未找到 MEP Designer 安装目录")
    latest = dirs[0]
    count = 0
    for f in latest.rglob("*.xml"):
        shutil.copy2(f, mep_dir / f.relative_to(latest))
        count += 1
    logger.info("已还原菜单文件 %d 个（%s）", count, latest.name)
    return {"restored": count, "backup": str(latest)}
