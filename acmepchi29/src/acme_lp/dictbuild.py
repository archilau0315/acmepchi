"""构建英中词典：英文原版 MUI 与 Archicad 中文版 MUI 按资源结构对齐。

MUI 是资源 DLL，内部嵌有 JSON 片段（`{"STRS": [...]}`）。每个节点带 `#id`，
文本在 `text` / `name` 字段。本模块按「祖先 #id 路径 + 字段名」配对，
因此即使两个构建的资源顺序不同，也不会错位。
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from . import paths

# 打包后包内目录是只读临时解压目录，缓存改写到用户目录，便于跨次复用
BUNDLED_PATH = Path(__file__).resolve().parent / "data" / "mui_dict.json"
CACHE_PATH = paths.LOCAL_DIR / "mui_dict.json" if getattr(sys, "frozen", False) else BUNDLED_PATH

START = '{"STRS"'
ESC = re.compile(r"\\u([0-9a-fA-F]{4})")
MIN_LEN, MAX_LEN = 3, 60
TEXT_FIELDS = ("text", "name", "hint", "tooltip")


def _unescape(text: str) -> str:
    """把 JSON 里的 \\uXXXX 转义还原成真实字符。"""
    return ESC.sub(lambda m: chr(int(m.group(1), 16)), text).replace("\\/", "/")


def _payloads(path: Path) -> list[dict]:
    """解析文件内嵌的所有 `{"STRS"...}` JSON 片段。"""
    text = path.read_text("utf-8", "ignore")
    decoder = json.JSONDecoder()
    out: list[dict] = []
    pos = 0
    while True:
        pos = text.find(START, pos)
        if pos < 0:
            break
        try:
            obj, end = decoder.raw_decode(text, pos)
        except ValueError:
            pos += 1
            continue
        if isinstance(obj, dict):
            out.append(obj)
        pos = max(end, pos + 1)
    return out


def _walk(node, key: str, into: dict[tuple[str, str], str]) -> None:
    """递归把 (路径, 字段) -> 文本 收集到 into。"""
    if isinstance(node, dict):
        ident = node.get("#id")
        name = node.get("name")
        # 用 #id 作为路径锚点；没有 id 时退回 name，保证跨构建可对齐
        tag = str(ident) if ident is not None else (str(name) if isinstance(name, str) else "")
        here = f"{key}/{tag}" if tag else key
        for field in TEXT_FIELDS:
            value = node.get(field)
            if isinstance(value, str) and value:
                into.setdefault((field, here), value)
        for child_key, child in node.items():
            if child_key in TEXT_FIELDS or child_key == "#id":
                continue
            _walk(child, here, into)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            ident = child.get("#id") if isinstance(child, dict) else None
            _walk(child, key if ident is not None else f"{key}[{index}]", into)


def _entries(path: Path) -> dict[tuple[str, str], str]:
    """文件内所有 (字段, 路径) -> 文本。"""
    found: dict[tuple[str, str], str] = {}
    for payload in _payloads(path):
        _walk(payload, "", found)
    return found


def _non_ascii_ratio(directory: Path) -> float:
    """抽样估算目录内文本的中文占比，用来区分英文原版与中文版。"""
    bad = total = 0
    for file in sorted(directory.glob("*.mui"))[:2]:
        for value in _entries(file).values():
            bad += sum(1 for ch in value if ord(ch) > 127)
            total += len(value)
    return bad / total if total else 0.0


def _english_dir(cfg: dict) -> Path:
    """英文原版资源目录：优先当前安装的 en（仍是英文时），其次历史备份。"""
    candidates: list[Path] = []
    target = paths.find_product_dir(cfg, "target")
    if target and (target / cfg["target_language_dir"]).is_dir():
        candidates.append(target / cfg["target_language_dir"])
    root = paths.BACKUP_ROOT
    if root.exists():
        for item in sorted(root.iterdir(), reverse=True):
            folder = item / "en"
            if folder.is_dir() and any(folder.glob("*.mui")):
                candidates.append(folder)
    if not candidates:
        raise RuntimeError("未找到英文原版 MUI（既无安装目录也无备份）")
    english = [d for d in candidates if _non_ascii_ratio(d) < 0.05]
    if not english:
        raise RuntimeError("备份中的 en 目录已是中文，找不到英文原版；请先还原英文再重建词典")
    return english[0]


def _chinese_dir(cfg: dict) -> Path:
    source = paths.find_product_dir(cfg, "source")
    if not source:
        raise RuntimeError(f"未找到 {cfg['source_install_dir']} 安装目录")
    folder = source / cfg["source_language_dir"]
    if not folder.is_dir():
        raise RuntimeError(f"中文资源目录不存在：{folder}")
    return folder


def _build(cfg: dict) -> dict[str, str]:
    en_dir, zh_dir = _english_dir(cfg), _chinese_dir(cfg)
    table: dict[str, str] = {}
    for file in sorted(en_dir.glob("*.mui")):
        other = zh_dir / file.name
        if not other.exists():
            continue
        en_items, zh_items = _entries(file), _entries(other)
        for key, src in en_items.items():
            dst = zh_items.get(key)
            if not dst or src == dst:
                continue
            if not (MIN_LEN <= len(src) <= MAX_LEN) or not src.isascii() or not src.isprintable():
                continue
            table.setdefault(src, dst)
    return table


def _read(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text("utf-8"))
    items = data.get("items", data)
    return {k: v for k, v in items.items() if isinstance(v, str)}


def load(cfg: dict | None = None, refresh: bool = False) -> dict[str, str]:
    """读取词典缓存；优先用户缓存，其次包内预置，最后现场重建。"""
    if not refresh:
        for path in dict.fromkeys((CACHE_PATH, BUNDLED_PATH)):
            if path.exists():
                return _read(path)
    cfg = cfg or paths.load_config()
    table = _build(cfg)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "built": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(table),
        "items": table,
    }
    CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), "utf-8")
    return table
