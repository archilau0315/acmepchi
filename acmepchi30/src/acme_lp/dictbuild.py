"""构建英中词典：英文原版 MUI 与 Archicad 中文版 MUI 按资源 id 分段对齐。

MUI 是资源 DLL，内部文本为 JSON 片段，形如 `"#id": 123` 分段，
段内有 `"text"/"name": "..."` 字符串。同 id 段内字符串数量相等时按顺序配对，
即可得到「英文 -> 中文」对照表，结果缓存到包内 data/mui_dict.json。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from . import paths

CACHE_PATH = Path(__file__).resolve().parent / "data" / "mui_dict.json"

SEG = re.compile(r'"#id": "?(\d+)"?')
TXT = re.compile(r'"(?:text|name)": "((?:[^"\\]|\\.){2,80})"')
ESC = re.compile(r"\\u([0-9a-fA-F]{4})")
MIN_LEN, MAX_LEN = 3, 60


def _unescape(text: str) -> str:
    """把 JSON 里的 \\uXXXX 转义还原成真实字符。"""
    return ESC.sub(lambda m: chr(int(m.group(1), 16)), text).replace("\\/", "/")


def _segments(path: Path) -> dict[str, list[str]]:
    """按 `#id` 切段，返回 id -> 段内字符串列表。"""
    text = path.read_text("utf-8", "ignore")
    marks = [(m.start(), m.group(1)) for m in SEG.finditer(text)]
    out: dict[str, list[str]] = {}
    for index, (pos, cid) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(text)
        out.setdefault(cid, []).extend(TXT.findall(text[pos:end]))
    return out


def _non_ascii_ratio(directory: Path) -> float:
    """抽样估算目录内文本的中文占比，用来区分英文原版与中文版。"""
    bad = total = 0
    for file in sorted(directory.glob("*.mui"))[:2]:
        for raw in TXT.findall(file.read_text("utf-8", "ignore")):
            text = _unescape(raw)
            bad += sum(1 for ch in text if ord(ch) > 127)
            total += len(text)
    return bad / total if total else 0.0


def _english_dir(cfg: dict) -> Path:
    """英文原版资源目录：优先历史备份里的 en，其次目标安装目录的 en。"""
    candidates: list[Path] = []
    root = paths.BACKUP_ROOT
    if root.exists():
        for item in sorted(root.iterdir(), reverse=True):
            folder = item / "en"
            if folder.is_dir() and any(folder.glob("*.mui")):
                candidates.append(folder)
    target = paths.find_product_dir(cfg, "target")
    if target and (target / cfg["target_language_dir"]).is_dir():
        candidates.append(target / cfg["target_language_dir"])
    if not candidates:
        raise RuntimeError("未找到英文原版 MUI（既无备份也无安装目录）")
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
        pairs = _segments(file)
        zh_pairs = _segments(other)
        for cid, texts in pairs.items():
            zh_texts = zh_pairs.get(cid)
            if not zh_texts or len(zh_texts) != len(texts):
                continue
            for src, dst in zip(texts, zh_texts):
                src, dst = _unescape(src), _unescape(dst)
                if src == dst or not dst:
                    continue
                if not (MIN_LEN <= len(src) <= MAX_LEN) or not src.isascii() or not src.isprintable():
                    continue
                table.setdefault(src, dst)
    return table


def load(cfg: dict | None = None, refresh: bool = False) -> dict[str, str]:
    """读取词典缓存；缓存缺失或要求刷新时重建。"""
    if CACHE_PATH.exists() and not refresh:
        data = json.loads(CACHE_PATH.read_text("utf-8"))
        items = data.get("items", data)
        return {k: v for k, v in items.items() if isinstance(v, str)}
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
