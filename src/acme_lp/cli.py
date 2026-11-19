"""命令行入口：python -m acme_lp.cli <status|preview|install|restore|backups>"""

from __future__ import annotations

import argparse

from . import backup, installer, paths


def _print_detect(info: dict) -> None:
    print(f"目标：{info['target_dir']}  版本 {info['target_version'] or '未知'}  语言 {info['target_uilanguage'] or '未知'}")
    print(f"来源：{info['source_dir']}  版本 {info['source_version'] or '未知'}")
    for err in info["errors"]:
        print(f"  [!] {err}")


def main() -> int:
    parser = argparse.ArgumentParser(prog="acmepchi", description="MEP Designer 30 中文资源移植工具")
    parser.add_argument("command", choices=["status", "preview", "install", "restore", "backups"])
    parser.add_argument("--mode", choices=["replace", "switch"], default=None, help="replace=覆盖 en 目录；switch=新建 zh-CN 并切换语言")
    args = parser.parse_args()

    cfg = paths.load_config()
    logger = paths.get_logger()

    if args.command == "status":
        info = installer.detect(cfg)
        _print_detect(info)
        plan = installer.preview(cfg)["plan"]
        if plan:
            print(f"待复制 {len(plan['to_copy'])} 个，已相同 {len(plan['identical'])} 个，源缺失 {len(plan['missing_in_source'])} 个")
        return 0

    if args.command == "preview":
        result = installer.preview(cfg)
        _print_detect(result["info"])
        plan = result["plan"]
        if plan:
            print(f"将覆盖 {len(plan['to_copy'])} 个文件：")
            for name in plan["to_copy"][:10]:
                print(f"  - {name}")
            if len(plan["to_copy"]) > 10:
                print(f"  ... 共 {len(plan['to_copy'])} 个")
        return 0

    if args.command == "install":
        result = installer.install(cfg, logger, args.mode)
        print(f"备份：{result['backup']}")
        print(f"复制：{len(result['copied'])} 个，剩余差异：{len(result['remaining'])} 个")
        return 0

    if args.command == "restore":
        result = installer.restore_latest(cfg, logger)
        print(f"已从 {result['backup']} 还原 {result['restored']} 个文件，语言标识 {result['uilanguage']}")
        return 0

    latest = backup.latest_backup()
    print(f"最近备份：{latest or '无'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
