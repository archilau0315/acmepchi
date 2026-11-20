"""MEP 工具名汉化：改写 MUI 内的字符串表资源。

MUI 是带资源的 PE 文件，文本放在 JSNL 资源里，内容形如 JSON 的
`"text": "Duct Route"`。这类文件不接受 UpdateResource（返回
ERROR_NOT_SUPPORTED），改写又必须保持 PE 结构不变，因此这里采用
「等长字节替换 + 尾部空格补齐」：先按字节找到原字符串，替换成中文后
用空格补足长度，JSON 仍然合法，资源大小与偏移都不变。
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from . import paths

MUI_NAME = "MEPPluginUI.dll.mui"
LANG_DIRS = ("en", "zh-CN")

# 字符串表里除工具名本身，还有固定的后缀变体（工具/默认设置/设置/ID/全选）
SUFFIXES = (
    ("", ""),
    (" Tool", "工具"),
    (" Default Settings", "默认设置"),
    (" Selection Settings", "选择设置"),
    (" Settings", "设置"),
    (" ID", " ID"),
)


class MuiTextError(RuntimeError):
    """MUI 文件缺失或不可写。"""


def _load_terms() -> dict[str, str]:
    path = paths.PACKAGE_ROOT / "data" / "mep_ui_terms.json"
    data = json.loads(path.read_text("utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def _pairs(terms: dict[str, str]) -> list[tuple[str, str]]:
    """展开出所有需要替换的英文 -> 中文对，长串优先，避免被短串截断。"""
    out: list[tuple[str, str]] = []
    for en, zh in terms.items():
        for suffix, zh_suffix in SUFFIXES:
            out.append((en + suffix, zh + zh_suffix))
        out.append((f"Select All {en}", f"全选{zh}"))
        out.append((f"Select All {en}s", f"全选{zh}"))
        out.append((f"Select All {en}es", f"全选{zh}"))
    return sorted(set(out), key=lambda kv: -len(kv[0]))


def patch_file(path: Path, pairs=None, dry_run: bool = False) -> int:
    """就地替换一个 MUI；返回替换次数。重复执行结果不变。"""
    pairs = pairs or _pairs(_load_terms())
    data = path.read_bytes()
    hits = 0
    for en, zh in pairs:
        old = f'"text": "{en}"'.encode("utf-8")
        if old not in data:
            continue
        new = f'"text": "{zh}"'.encode("utf-8")
        if len(new) > len(old):
            continue  # 中文更长时跳过，保证文件长度不变
        data = data.replace(old, new + b" " * (len(old) - len(new)))
        hits += 1
    if hits and not dry_run:
        backup = path.with_suffix(path.suffix + ".bak-zhpatch")
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_bytes(data)
    return hits


def apply(cfg: dict, logger, dry_run: bool = False) -> dict:
    """处理安装目录下各语言版本的 MEPPluginUI.dll.mui。"""
    mep = paths.find_product_dir(cfg, "target")
    if not mep:
        raise MuiTextError(f"未找到 {cfg['product_install_dir']} 安装目录")
    pairs = _pairs(_load_terms())
    result: dict[str, int] = {}
    for lang in dict.fromkeys(LANG_DIRS + (cfg.get("target_language_dir", ""),)):
        target = mep / lang / MUI_NAME
        if lang and target.is_file():
            hits = patch_file(target, pairs, dry_run)
            result[f"{lang}/{MUI_NAME}"] = hits
    if not result:
        raise MuiTextError(f"未找到 {MUI_NAME}")
    total = sum(result.values())
    if not dry_run:
        logger.info("MUI 工具名汉化：%d 处（%s）", total, ", ".join(f"{k}:{v}" for k, v in result.items()))
    return {"files": result, "total": total, "dry_run": dry_run, "time": datetime.now().strftime("%H:%M:%S")}
