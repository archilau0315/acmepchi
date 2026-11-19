"""检测、安装与还原编排。"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import backup, paths, verify, wepatch


def _app_running(cfg: dict) -> bool:
    """目标版本运行时资源文件会被占用，安装前必须先退出。"""
    return paths.app_running(cfg)


class GuardError(RuntimeError):
    """前置条件不满足（路径、版本、语言包缺失）。"""


def detect(cfg: dict) -> dict:
    target = paths.find_product_dir(cfg, "target")
    source = paths.find_product_dir(cfg, "source")
    info = {
        "target_dir": target,
        "source_dir": source,
        "target_version": paths.file_version(target / cfg["product_exe"]) if target else "",
        "source_version": paths.file_version(source / cfg["source_exe"]) if source else "",
        "target_uilanguage": paths.read_uilanguage(target) if target else "",
        "source_language_dir": (source / cfg["source_language_dir"]) if source else None,
        "target_language_dir": (target / cfg["target_language_dir"]) if target else None,
    }
    info["errors"] = []
    if not target:
        info["errors"].append(f"未找到 {cfg['product_install_dir']} 安装目录")
    if not source:
        info["errors"].append(f"未找到 {cfg['source_install_dir']}（中文资源来源）")
    elif not (source / cfg["source_language_dir"]).exists():
        info["errors"].append(f"来源目录 {cfg['source_language_dir']} 不存在")
    else:
        src_uilang = paths.read_uilanguage(source)
        if src_uilang != cfg["source_language_dir"]:
            info["errors"].append(f"来源 Archicad 当前语言为 {src_uilang or '未知'}，请先装中文版")
    # 本项目按「MEP 与 Archicad 构建号不同步」处理：不一致时禁止整文件替换 MUI
    if cfg.get("replace_mui", True) and target and source and info["target_version"] and info["source_version"]:
        if info["target_version"] != info["source_version"]:
            info["errors"].append(
                f"构建号不一致：{cfg['product_install_dir']} 为 {info['target_version']}，"
                f"{cfg['source_install_dir']} 为 {info['source_version']}；整文件替换 MUI 会导致程序退出，"
                "请将 replace_mui 设为 false（仅汉化工作环境）"
            )
    if target and _app_running(cfg):
        info["errors"].append(f"{cfg['product_exe']} 正在运行，请先完全退出后再安装")
    return info


def preview(cfg: dict) -> dict:
    info = detect(cfg)
    if info["errors"]:
        return {"info": info, "plan": None}
    return {
        "info": info,
        "plan": verify.build_plan(info["source_language_dir"], info["target_language_dir"], cfg.get("exclude", [])),
    }


def install(cfg: dict, logger, mode: str | None = None) -> dict:
    info = detect(cfg)
    if info["errors"]:
        raise GuardError("；".join(info["errors"]))

    mode = mode or cfg.get("mode", "replace")
    exclude = cfg.get("exclude", [])
    if not cfg.get("replace_mui", True):
        # 构建号无法对齐时只动工作环境：菜单标题、工具面板分组名、命令布局缓存
        logger.info("配置为仅汉化工作环境（不替换 MUI）")
        workenv = wepatch.apply(cfg, logger)
        return {
            "backup": "",
            "copied": [],
            "remaining": [],
            "mode": "workenv",
            "workenv": workenv,
        }
    source_dir: Path = info["source_language_dir"]
    target_dir: Path = info["target_language_dir"]
    plan = verify.build_plan(source_dir, target_dir, exclude)
    logger.info("来源 %s -> 目标 %s，待复制 %d 个", source_dir, target_dir, len(plan["to_copy"]))

    snapshot = backup.create_backup(target_dir, Path(info["target_dir"]) / "uilanguage.dat")
    logger.info("已备份到 %s", snapshot)

    if mode == "switch":
        skip = {name.lower() for name in exclude}
        target_dir = info["target_dir"] / cfg["source_language_dir"]
        target_dir.mkdir(parents=True, exist_ok=True)
        copied = []
        for item in sorted(source_dir.iterdir()):
            if item.is_file() and item.name.lower() not in skip:
                shutil.copy2(item, target_dir / item.name)
                copied.append(item.name)
        paths.write_uilanguage(info["target_dir"], cfg["source_language_dir"])
    else:
        copied = []
        for name in plan["to_copy"]:
            shutil.copy2(source_dir / name, target_dir / name)
            copied.append(name)

    while_after = verify.build_plan(source_dir, target_dir, exclude)
    logger.info("安装完成：复制 %d 个，剩余差异 %d 个", len(copied), len(while_after["to_copy"]))

    # 资源就位后同步汉化工作环境（菜单标题、工具面板分组名、命令布局 bin）
    try:
        workenv = wepatch.apply(cfg, logger)
    except (OSError, wepatch.WorkEnvError) as exc:
        logger.warning("工作环境汉化失败：%s", exc)
        workenv = {"error": str(exc)}
    return {
        "backup": str(snapshot),
        "copied": copied,
        "remaining": while_after["to_copy"],
        "mode": mode,
        "workenv": workenv,
    }


def restore_latest(cfg: dict, logger) -> dict:
    info = detect(cfg)
    if not info["target_dir"]:
        raise GuardError(f"未找到 {cfg['product_install_dir']} 安装目录")
    if _app_running(cfg):
        raise GuardError(f"{cfg['product_exe']} 正在运行，请先完全退出后再还原")
    if not cfg.get("replace_mui", True):
        return wepatch.restore_latest(cfg, logger)
    snapshot = backup.latest_backup(Path(info["target_language_dir"]).name)
    if not snapshot:
        raise GuardError("没有可用的 MUI 备份")
    result = backup.restore(snapshot, info["target_language_dir"], info["target_dir"] / "uilanguage.dat")
    logger.info("已从 %s 还原 %d 个文件", snapshot, result["restored"])
    return result
