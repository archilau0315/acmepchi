"""工作环境汉化：工具面板分组名、菜单标题 XML 与用户级命令布局 bin。

MEP Designer 的菜单/工具面板文字不来自 MUI，而来自两处：
1. 安装目录 `Defaults\\MEP Designer\\WorkEnvironment\\` 下的 XML（分组名、菜单标题）；
2. 用户目录 `%APPDATA%\\GRAPHISOFT\\MEP Designer 30*\\LimitedWorkEnvironment\\Command Layouts\\*.bin`
   ——UTF-16LE 二进制快照，字符串为「GUID + 控制字节 + 长度 + 文本 + 两个 U+FFFF」。
   bin 长度固定，译文更短时用 U+FFFF 补齐，不能删除该文件。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from . import dictbuild, paths

WORKENV = Path("Defaults") / "MEP Designer" / "WorkEnvironment"
TOOLS_XML = WORKENV / "Tools" / "MEP Engineering Tools.xml"
COMMANDS_XML = WORKENV / "Command Layouts" / "Standard Commands.xml"
LAYOUT_DIR = Path("LimitedWorkEnvironment") / "Command Layouts"
TERMS_PATH = Path(__file__).resolve().parent / "data" / "mep_terms.json"

NAME_TAG = re.compile(r"(<Name\b[^>]*>)([^<]*)(</Name>)")
TITLE_ATTR = re.compile(r'(\btitle=")([^"]*)(")')
FILL = "\uffff".encode("utf-16-le")
ENTITIES = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&apos;": "'"}


class WorkEnvError(RuntimeError):
    """工作环境汉化前置条件不满足。"""


def app_running(exe_name: str) -> bool:
    """目标程序运行中时其工作环境文件被占用，必须先退出。"""
    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}"],
            capture_output=True,
            text=True,
            errors="ignore",
        ).stdout
        return exe_name.lower() in out.lower()
    except OSError:
        return False


def _xml_unescape(text: str) -> str:
    for entity, char in ENTITIES.items():
        text = text.replace(entity, char)
    return text


def _xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _load_terms() -> dict[str, str]:
    data = json.loads(TERMS_PATH.read_text("utf-8"))
    return {k: v for k, v in data.items() if isinstance(v, str) and not k.startswith("_")}


def _lookup(text: str, tables: tuple[dict[str, str], ...]) -> str | None:
    """查译文：先词表后词典，兼容 & 快捷键前缀。只接受纯 ASCII 原文。"""
    if not text or not text.isascii() or text != text.strip():
        return None
    for table in tables:
        if text in table:
            return table[text]
        if text.startswith("&"):
            hit = table.get(text[1:])
            if hit:
                return "&" + hit
        else:
            hit = table.get("&" + text)
            if hit:
                return hit[1:] if hit.startswith("&") else hit
    return None


def _patch_xml(path: Path, pattern: re.Pattern, tables: tuple[dict[str, str], ...]) -> tuple[str, int]:
    """替换 XML 中命中词表的纯 ASCII 文本，返回新文本与命中数。"""
    raw = path.read_text("utf-8", errors="surrogateescape")
    hits = 0

    def repl(match: re.Match) -> str:
        nonlocal hits
        zh = _lookup(_xml_unescape(match.group(2)), tables)
        if not zh:
            return match.group(0)
        hits += 1
        return match.group(1) + _xml_escape(zh) + match.group(3)

    return pattern.sub(repl, raw), hits


def _patch_bin(data: bytes, table: dict[str, str]) -> tuple[bytes, int]:
    """按英文长度降序在 UTF-16LE 字节里替换，长度不足处用 U+FFFF 补齐。"""
    count = 0
    for en, zh in sorted(table.items(), key=lambda kv: -len(kv[0])):
        if not zh:
            continue
        pattern, new = en.encode("utf-16-le"), zh.encode("utf-16-le")
        if len(new) > len(pattern):
            continue
        start = 0
        while True:
            index = data.find(pattern, start)
            if index < 0:
                break
            end = index + len(pattern)
            prev = data[index - 2:index].decode("utf-16-le", "ignore") if index >= 2 else ""
            nxt = data[end:end + 2].decode("utf-16-le", "ignore") if end + 2 <= len(data) else ""
            if not prev.isalnum() and not nxt.isalnum():
                padding = FILL * ((len(pattern) - len(new)) // 2)
                data = data[:index] + new + padding + data[end:]
                count += 1
            start = index + max(len(new), 2)
    return data, count


def _bin_files() -> list[Path]:
    """用户级命令布局 bin（各版本目录下的 Command Layouts/*.bin）。"""
    base = Path(os.environ.get("APPDATA", str(Path.home()))) / "GRAPHISOFT"
    if not base.is_dir():
        return []
    files: list[Path] = []
    for folder in sorted(base.iterdir()):
        layout = folder / LAYOUT_DIR
        if folder.is_dir() and folder.name.lower().startswith("mep designer 30") and layout.is_dir():
            files.extend(sorted(layout.glob("*.bin")))
    return files


def _new_backup_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = paths.BACKUP_ROOT / f"we-{stamp}"
    suffix = 1
    while folder.exists():
        suffix += 1
        folder = paths.BACKUP_ROOT / f"we-{stamp}-{suffix}"
    folder.mkdir(parents=True)
    return folder


def _save(backup: Path, target: Path, rel: str, entries: list[dict]) -> None:
    dest = backup / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, dest)
    readonly = (target.stat().st_mode & 0o200) == 0
    entries.append({"target": str(target), "backup": rel, "readonly": readonly})


def _write_manifest(backup: Path, entries: list[dict]) -> None:
    payload = {"created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "entries": entries}
    (backup / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")


def apply(cfg: dict, logger, dry_run: bool = False) -> dict:
    """汉化工作环境 XML 与命令布局 bin；默认幂等，可重复执行。"""
    if not dry_run and app_running(cfg["product_exe"]):
        raise WorkEnvError(f"{cfg['product_exe']} 正在运行，请先完全退出")
    mep_dir = paths.find_product_dir(cfg, "target")
    if not mep_dir:
        raise WorkEnvError(f"未找到 {cfg['product_install_dir']} 安装目录")

    terms = _load_terms()
    table = dictbuild.load(cfg)
    tables = (terms, table)
    # bin 用精确字节替换，词表优先覆盖词典（补充顶栏与工具面板的常用词）
    bin_table = {**table, **terms}

    xml_plan: list[tuple[Path, str, int]] = []
    for rel, pattern in ((TOOLS_XML, NAME_TAG), (COMMANDS_XML, TITLE_ATTR)):
        target = mep_dir / rel
        if not target.exists():
            continue
        text, hits = _patch_xml(target, pattern, tables)
        if hits:
            xml_plan.append((target, text, hits))

    bin_plan: list[tuple[Path, bytes, int]] = []
    for target in _bin_files():
        data, hits = _patch_bin(target.read_bytes(), bin_table)
        if hits:
            bin_plan.append((target, data, hits))

    stats = {
        "dict": len(table),
        "terms": len(terms),
        "xml": {p.name: h for p, _, h in xml_plan},
        "xml_total": sum(h for _, _, h in xml_plan),
        "bins": {p.name: h for p, _, h in bin_plan},
        "bin_total": sum(h for _, _, h in bin_plan),
        "backup": "",
    }
    if dry_run or not (xml_plan or bin_plan):
        return stats

    snapshot = _new_backup_dir()
    entries: list[dict] = []
    for target, text, _ in xml_plan:
        _save(snapshot, target, f"install/{target.relative_to(mep_dir).as_posix()}", entries)
        target.chmod(0o666)
        target.write_text(text, encoding="utf-8", errors="surrogateescape", newline="")
    for target, data, _ in bin_plan:
        _save(snapshot, target, f"bin/{target.name}", entries)
        target.chmod(0o666)
        target.write_bytes(data)
    _write_manifest(snapshot, entries)

    logger.info("工作环境汉化：XML %d 处，bin %d 处", stats["xml_total"], stats["bin_total"])
    stats["backup"] = str(snapshot)
    return stats


def restore_latest(cfg: dict, logger) -> dict:
    """从最近的 we-* 备份逐个回溯还原；同一文件只取最近一份原始副本。"""
    if app_running(cfg["product_exe"]):
        raise WorkEnvError(f"{cfg['product_exe']} 正在运行，请先完全退出")
    if not paths.BACKUP_ROOT.exists():
        raise WorkEnvError("没有可用的备份")
    folders = sorted(
        (d for d in paths.BACKUP_ROOT.iterdir()
         if d.is_dir() and d.name.startswith("we-") and (d / "manifest.json").exists()),
        reverse=True,
    )
    if not folders:
        raise WorkEnvError("没有工作环境汉化备份")
    done: set[str] = set()
    count = 0
    for folder in folders:
        manifest = json.loads((folder / "manifest.json").read_text("utf-8"))
        for entry in manifest.get("entries", []):
            target, source = Path(entry["target"]), folder / entry["backup"]
            if str(target).lower() in done or not source.exists():
                continue
            done.add(str(target).lower())
            target.chmod(0o666)
            shutil.copyfile(source, target)
            target.chmod(0o444 if entry.get("readonly") else 0o666)
            count += 1
    logger.info("已还原工作环境文件 %d 个（回溯 %d 份备份）", count, len(folders))
    return {"restored": count, "backup": str(folders[0]), "scanned": len(folders)}
