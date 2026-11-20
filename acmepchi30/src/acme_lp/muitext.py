"""MEP 界面文本汉化：改写 MUI 内 JSNL 资源中的 JSON 文本。

MUI 是带资源的 PE 文件，界面文字放在 JSNL 资源里（按 2000~2004 分资源），
正文是紧凑 JSON。这类文件不接受 UpdateResource（返回 ERROR_NOT_SUPPORTED），
因此这里直接按 PE 资源表定位正文，整体重写 JSON：新内容不超过原容量时用
空格补齐，资源大小与偏移都不变；超出容量则先压缩分隔符，仍超出就跳过。
"""

from __future__ import annotations

import json
import shutil
import struct
from datetime import datetime
from pathlib import Path

from . import paths

MUI_NAME = "MEPPluginUI.dll.mui"
JSON_RIDS = (2000, 2001, 2002, 2003, 2004)

# 会显示给用户的字符串字段；name 仅在对话框/告警条目里翻译
TEXT_KEYS = {
    "text",
    "tooltipStr",
    "largeText",
    "smallText",
    "acceptButtonText",
    "cancelButtonText",
    "thirdButtonText",
    "title",
    "description",
}
NAME_KEYS = {"name"}


class MuiTextError(RuntimeError):
    """MUI 文件缺失、格式异常或不可写。"""


def _load_map() -> dict[str, str]:
    path = paths.PACKAGE_ROOT / "data" / "mep_ui_zh.json"
    data = json.loads(path.read_text("utf-8"))
    items = data.get("items", data)
    return {k: v for k, v in items.items() if isinstance(v, str) and not k.startswith("_") and k != v}


def _rva_to_offset(rva: int, sections: list[tuple[int, int, int, int]]) -> int:
    for vaddr, vsize, rawptr, rawsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            return rawptr + rva - vaddr
    raise MuiTextError(f"RVA 0x{rva:x} 不在任何节内")


def _resource_table(data: bytes) -> tuple[list[tuple[str, str, int, int]], int]:
    """解析 PE 资源表，返回 [(类型, 名称, 大小, 文件偏移)] 与资源段文件偏移。"""
    if data[:2] != b"MZ":
        raise MuiTextError("不是 PE 文件")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe : pe + 4] != b"PE\0\0":
        raise MuiTextError("缺少 PE 签名")
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    dd = opt + (112 if magic == 0x20B else 96)
    rsrc_rva = struct.unpack_from("<I", data, dd + 16)[0]
    if not rsrc_rva:
        raise MuiTextError("没有资源段")

    sections: list[tuple[int, int, int, int]] = []
    sec = opt + opt_size
    for i in range(nsec):
        off = sec + i * 40
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, off + 8)
        sections.append((vaddr, vsize, rawptr, rawsize))
    base = _rva_to_offset(rsrc_rva, sections)

    def entries(off: int) -> list[tuple[int, int]]:
        *_, named, IDs = struct.unpack_from("<IIHHHH", data, off)
        return [struct.unpack_from("<II", data, off + 16 + i * 8) for i in range(named + IDs)]

    def label(nid: int) -> str:
        if nid & 0x80000000:
            pos = base + (nid & 0x7FFFFFFF)
            length = struct.unpack_from("<H", data, pos)[0]
            return data[pos + 2 : pos + 2 + length * 2].decode("utf-16-le", "replace")
        return str(nid)

    out: list[tuple[str, str, int, int]] = []

    def walk(off: int, path: tuple[str, ...]) -> None:
        for nid, ptr in entries(off):
            if ptr & 0x80000000:
                walk(base + (ptr & 0x7FFFFFFF), path + (label(nid),))
            else:
                rva, size, _, _ = struct.unpack_from("<IIII", data, base + ptr)
                kind, name = path[0], path[1]
                out.append((kind, name, size, _rva_to_offset(rva, sections)))

    walk(base, ())
    return out, base


def _walk_text(node, mapping: dict[str, str], stats: list[int], translate_name: bool = False) -> None:
    if isinstance(node, dict):
        local = translate_name or "type" in node
        for key, value in node.items():
            if isinstance(value, str) and (key in TEXT_KEYS or (key in NAME_KEYS and local)):
                new = mapping.get(value)
                if new and new != value:
                    node[key] = new
                    stats[0] += 1
            elif isinstance(value, (dict, list)):
                _walk_text(value, mapping, stats, local)
    elif isinstance(node, list):
        for item in node:
            _walk_text(item, mapping, stats, translate_name)


def _encode(obj, capacity: int) -> bytes:
    """优先保持原排版，超出容量时再压缩分隔符。"""
    for separators in ((", ", ": "), (",", ":")):
        raw = json.dumps(obj, ensure_ascii=False, separators=separators).encode("utf-8")
        if len(raw) <= capacity:
            return raw
    return b""


def _patch_resource(data: bytearray, off: int, size: int, mapping: dict[str, str], rid: int) -> tuple[int, bool]:
    """替换单个 JSNL 资源；返回 (替换次数, 是否写入)。"""
    if size <= 4:
        return 0, False
    length = struct.unpack_from("<I", data, off)[0]
    if length > size - 4:
        return 0, False
    try:
        obj = json.loads(bytes(data[off + 4 : off + 4 + length]).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MuiTextError(f"资源 {rid} 不是合法 JSON：{exc}") from exc
    stats = [0]
    _walk_text(obj, mapping, stats, rid == 2004)
    if not stats[0]:
        return 0, False
    raw = _encode(obj, size - 4)
    if not raw:
        return 0, False
    padding = b" " * (size - 4 - len(raw))
    struct.pack_into("<I", data, off, len(raw) + len(padding))
    data[off + 4 : off + size] = raw + padding
    return stats[0], True


def patch_file(path: Path, mapping: dict[str, str] | None = None, dry_run: bool = False) -> dict:
    """就地汉化一个 MUI；返回替换次数与跳过的资源。"""
    mapping = mapping or _load_map()
    data = bytearray(path.read_bytes())
    resources, _ = _resource_table(data)
    total, skipped = 0, []
    for kind, name, size, off in resources:
        if kind != "JSNL" or not name.isdigit() or int(name) not in JSON_RIDS:
            continue
        hits, written = _patch_resource(data, off, size, mapping, int(name))
        total += hits
        if hits and not written:
            skipped.append(f"{name}({size}B)")
    if total and not dry_run:
        backup = path.with_suffix(path.suffix + ".bak-zhpatch")
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_bytes(data)
    return {"hits": total, "skipped": skipped}


def apply(cfg: dict, logger, dry_run: bool = False, langs: tuple[str, ...] | None = None) -> dict:
    """处理安装目录下指定语言目录的 MEPPluginUI.dll.mui（默认只改目标语言）。

    en 目录保持英文原版，这样切换回英文时无需重新安装资源。
    """
    mep = paths.find_product_dir(cfg, "target")
    if not mep:
        raise MuiTextError(f"未找到 {cfg['product_install_dir']} 安装目录")
    if langs is None:
        langs = (cfg.get("target_language_dir") or "zh-CN",)
    mapping = _load_map()
    files: dict[str, dict] = {}
    for lang in dict.fromkeys(langs):
        target = mep / lang / MUI_NAME
        if lang and target.is_file():
            files[f"{lang}/{MUI_NAME}"] = patch_file(target, mapping, dry_run)
    if not files:
        raise MuiTextError(f"未找到 {MUI_NAME}")
    total = sum(item["hits"] for item in files.values())
    if not dry_run:
        logger.info("MUI 文本汉化：%d 处（%s）", total, ", ".join(f"{k}:{v['hits']}" for k, v in files.items()))
        for name, item in files.items():
            if item["skipped"]:
                logger.warning("%s 内容超长已跳过：%s", name, ", ".join(item["skipped"]))
    return {"files": files, "total": total, "dry_run": dry_run, "time": datetime.now().strftime("%H:%M:%S")}


def restore_english(cfg: dict) -> int:
    """把 en 目录被汉化过的 MUI 还原为英文原版（使用同目录 .bak-zhpatch）。"""
    mep = paths.find_product_dir(cfg, "target")
    if not mep:
        return 0
    target = mep / "en" / MUI_NAME
    backup = target.with_suffix(target.suffix + ".bak-zhpatch")
    if not (target.is_file() and backup.is_file()):
        return 0
    if target.read_bytes() == backup.read_bytes():
        return 0
    shutil.copy2(backup, target)
    return 1
