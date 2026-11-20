"""中英界面一键切换。

切换只动三样东西：`uilanguage.dat`、zh-CN 卫星目录、工作环境（菜单/面板）快照，
不重复复制 85 个 MUI，也不重新生成词典，因此中英互切通常在 1 秒内完成。
"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import muitext, paths, verify, wepatch


class LangSwitchError(RuntimeError):
    """安装目录缺失、程序运行中或中文资源未就绪。"""


def normalize(lang: str) -> str:
    """把 en / zh / 中文 等写法统一成 en 或 zh-CN。"""
    key = (lang or "").strip().lower().replace("_", "-")
    if key in ("en", "en-us", "english", "英文"):
        return "en"
    if key in ("zh", "zh-cn", "cn", "chinese", "中文", "简体中文"):
        return "zh-CN"
    raise LangSwitchError(f"不支持的语言：{lang}")


def current(cfg: dict) -> str:
    target = paths.find_product_dir(cfg, "target")
    return paths.read_uilanguage(target) if target else ""


def zh_files(cfg: dict) -> int:
    target = paths.find_product_dir(cfg, "target")
    folder = target / cfg["target_language_dir"] if target else None
    if not folder or not folder.is_dir():
        return 0
    return len([p for p in folder.glob("*.mui") if p.is_file()])


def status(cfg: dict) -> dict:
    """当前语言、中文资源是否就绪、en 是否仍被汉化。"""
    target = paths.find_product_dir(cfg, "target")
    en_mui = target / "en" / muitext.MUI_NAME if target else None
    en_backup = en_mui.with_suffix(en_mui.suffix + ".bak-zhpatch") if en_mui else None
    en_patched = bool(
        en_mui and en_backup and en_mui.is_file() and en_backup.is_file()
        and en_mui.read_bytes() != en_backup.read_bytes()
    )
    return {
        "current": paths.read_uilanguage(target) if target else "",
        "target_dir": str(target) if target else "",
        "zh_ready": zh_files(cfg) > 0,
        "zh_files": zh_files(cfg),
        "en_patched": en_patched,
    }


def _guard(cfg: dict) -> Path:
    target = paths.find_product_dir(cfg, "target")
    if not target:
        raise LangSwitchError(f"未找到 {cfg['product_install_dir']} 安装目录")
    if wepatch.app_running(cfg["product_exe"]):
        raise LangSwitchError(f"{cfg['product_exe']} 正在运行，请先完全退出")
    return target


def _ensure_zh_files(cfg: dict, target: Path) -> int:
    """补齐 zh-CN 卫星资源（已存在且相同的不再复制）。"""
    lang = cfg.get("target_language_dir") or "zh-CN"
    source = paths.find_product_dir(cfg, "source")
    source_dir = source / cfg["source_language_dir"] if source else None
    if not source_dir or not source_dir.is_dir():
        raise LangSwitchError(f"未找到 {cfg['source_install_dir']} 中文版，无法准备中文资源")
    plan = verify.build_plan(source_dir, target / lang, cfg.get("exclude", []))
    copied = 0
    for name in plan["to_copy"]:
        (target / lang).mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_dir / name, target / lang / name)
        copied += 1
    return copied


def switch(cfg: dict, logger, lang: str) -> dict:
    """切到指定语言；返回步骤统计，已是目标语言时不做任何写入。"""
    lang = normalize(lang)
    target = _guard(cfg)
    before = paths.read_uilanguage(target)
    result = {"from": before, "to": lang, "changed": before != lang, "copied": 0}

    if before == lang:
        logger.info("当前已是 %s，无需切换", lang)
        return result

    if lang == "zh-CN":
        result["copied"] = _ensure_zh_files(cfg, target)
        try:
            result["muitext"] = muitext.apply(cfg, logger)["total"]
        except (OSError, muitext.MuiTextError) as exc:
            raise LangSwitchError(f"MUI 文本汉化失败：{exc}") from exc
        try:
            result["workenv"] = wepatch.apply(cfg, logger)["backup"]
        except (OSError, wepatch.WorkEnvError) as exc:
            logger.warning("工作环境汉化失败：%s", exc)
            result["workenv"] = f"error: {exc}"
        if muitext.restore_english(cfg):
            logger.info("已把 en 目录的 MUI 还原为英文原版")
    else:
        muitext.restore_english(cfg)
        try:
            result["workenv"] = wepatch.restore_latest(cfg, logger)["backup"]
        except (OSError, wepatch.WorkEnvError) as exc:
            logger.warning("工作环境还原失败：%s", exc)
            result["workenv"] = f"error: {exc}"

    paths.write_uilanguage(target, lang)
    logger.info("界面语言已切换：%s -> %s", before, lang)
    return result


def toggle(cfg: dict, logger) -> dict:
    """中文 ⇄ 英文。"""
    return switch(cfg, logger, "en" if current(cfg) == "zh-CN" else "zh-CN")
