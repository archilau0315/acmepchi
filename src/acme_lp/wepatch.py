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
import ctypes
from datetime import datetime
from pathlib import Path

from . import dictbuild, paths

WORKENV = Path("Defaults") / "MEP Designer" / "WorkEnvironment"
TOOLS_XML = WORKENV / "Tools" / "MEP Engineering Tools.xml"
COMMANDS_XML = WORKENV / "Command Layouts" / "Standard Commands.xml"
LAYOUT_DIR = Path("LimitedWorkEnvironment") / "Command Layouts"
TERMS_PATH = Path(__file__).resolve().parent / "data" / "mep_terms.json"

# bin 扫描范围（相对用户配置目录 MEP Designer 30*）；这些文件都存放界面文案缓存
BIN_DIRS = [
    Path("LimitedWorkEnvironment") / "Command Layouts",
    Path("LimitedWorkEnvironment") / "Tools",
    Path("LimitedWorkEnvironment") / "Workspaces",
    Path("Latest WorkEnvironment") / "Workspaces",
    Path("最近的工作环境") / "工具",
    Path("最近的工作环境") / "工作空间",
]

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


def set_readonly(path: Path, readonly: bool) -> None:
    """设置/清除只读属性。

    Windows 下 os.chmod 偶发不生效（尤其是刚被程序关闭的文件），
    这里直接改文件属性，写完后再按原状态恢复。
    """
    try:
        kernel32 = ctypes.windll.kernel32
    except AttributeError:  # 非 Windows 平台
        path.chmod(0o444 if readonly else 0o666)
        return
    attrs = kernel32.GetFileAttributesW(str(path))
    if attrs == -1:
        raise OSError(0, "读取文件属性失败", str(path))
    new = (attrs | 0x01) if readonly else (attrs & ~0x01)
    if not kernel32.SetFileAttributesW(str(path), new):
        raise OSError(0, "设置文件属性失败", str(path))
    if bool(path.stat().st_mode & 0o200) == readonly:
        raise OSError(0, "文件仍不可写", str(path))


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


def _context(data: bytes, index: int, length: int, chars: int = 20) -> tuple[str, str]:
    """取命中位置前/后各 chars 个 UTF-16 字符，便于人工判断是否误替换。"""
    left = index - chars * 2
    left = left if left % 2 == 0 else left + 1
    right = index + length
    return (
        data[max(0, left):index].decode("utf-16-le", "replace"),
        data[right:right + chars * 2].decode("utf-16-le", "replace"),
    )


def _patch_bin(
    data: bytes,
    table: dict[str, str],
    trace: list[str] | None = None,
    fix_length: bool = False,
) -> tuple[bytes, int]:
    """按英文长度降序在 UTF-16LE 字节里替换。

    记录格式为「控制字节 + 长度字段(uint32 LE, 字符数) + UTF-16 文本」。
    译文更短时用 U+FFFF 补齐原字节长度；fix_length=True 时同时把长度字段
    改为中文字符数（两种写法都不改变文件总长度）。
    """
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
            # 整条记录：文本前紧邻「01 00 + 字符数(uint32)」，此时必定是完整标签
            header = b"\x01\x00" + len(en).to_bytes(4, "little")
            whole = data[index - 6:index] == header if index >= 6 else False
            if whole or (not prev.isalnum() and not nxt.isalnum()):
                if trace is not None:
                    left, right = _context(data, index, len(pattern))
                    trace.append(f"    @{index} {left!r} [{en} -> {zh}] {right!r}")
                padding = FILL * ((len(pattern) - len(new)) // 2)
                data = data[:index] + new + padding + data[end:]
                if fix_length and index >= 4:
                    data = data[:index - 4] + len(zh).to_bytes(4, "little") + data[index:]
                count += 1
            start = index + max(len(new), 2)
    return data, count


def _version_roots() -> list[Path]:
    """用户配置目录下的各版本根（%APPDATA%\\GRAPHISOFT\\MEP Designer 30*）。"""
    base = Path(os.environ.get("APPDATA", str(Path.home()))) / "GRAPHISOFT"
    if not base.is_dir():
        return []
    return [d for d in sorted(base.iterdir()) if d.is_dir() and d.name.lower().startswith("mep designer 30")]


def _bin_files() -> list[Path]:
    """所有含界面文案的用户级 bin（工具面板、命令布局、工作空间等）。"""
    files: list[Path] = []
    for root in _version_roots():
        for rel in BIN_DIRS:
            folder = root / rel
            if folder.is_dir():
                files.extend(sorted(p for p in folder.glob("*.bin") if p.is_file()))
    return files


def _bin_rel(target: Path) -> str:
    """相对版本根目录的路径，用作备份子路径和统计键。"""
    for root in _version_roots():
        try:
            return target.relative_to(root).as_posix()
        except ValueError:
            continue
    return target.name


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


def apply(cfg: dict, logger, dry_run: bool = False, fix_length: bool = False) -> dict:
    """汉化工作环境 XML 与用户级 bin；默认幂等，可重复执行。"""
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
    traces: list[str] = []
    for target in _bin_files():
        label = _bin_rel(target)
        local: list[str] = []
        data, hits = _patch_bin(target.read_bytes(), bin_table, local, fix_length)
        if hits:
            bin_plan.append((target, data, hits))
            traces.append(f"  {label}（{hits} 处）")
            traces.extend(local)

    stats = {
        "dict": len(table),
        "terms": len(terms),
        "xml": {p.name: h for p, _, h in xml_plan},
        "xml_total": sum(h for _, _, h in xml_plan),
        "bins": {_bin_rel(p): h for p, _, h in bin_plan},
        "bin_total": sum(h for _, _, h in bin_plan),
        "traces": traces,
        "strategy": "length-fixed" if not fix_length else "length-updated",
        "backup": "",
    }
    if dry_run or not (xml_plan or bin_plan):
        return stats

    snapshot = _new_backup_dir()
    entries: list[dict] = []
    for target, text, _ in xml_plan:
        _save(snapshot, target, f"install/{target.relative_to(mep_dir).as_posix()}", entries)
        set_readonly(target, False)
        target.write_text(text, encoding="utf-8", errors="surrogateescape", newline="")
    for target, data, _ in bin_plan:
        readonly = (target.stat().st_mode & 0o200) == 0
        _save(snapshot, target, f"bin/{_bin_rel(target)}", entries)
        set_readonly(target, False)
        target.write_bytes(data)
        set_readonly(target, readonly)
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
            set_readonly(target, False)
            shutil.copyfile(source, target)
            set_readonly(target, bool(entry.get("readonly")))
            count += 1
    logger.info("已还原工作环境文件 %d 个（回溯 %d 份备份）", count, len(folders))
    return {"restored": count, "backup": str(folders[0]), "scanned": len(folders)}
