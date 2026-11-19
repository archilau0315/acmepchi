"""图形界面：双击即用，三步完成检测/安装/还原。"""

from __future__ import annotations

import os
import subprocess
import tkinter as tk
from tkinter import messagebox, scrolledtext

from . import __version__, backup, installer, paths


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.cfg = paths.load_config()
        self.logger = paths.get_logger()
        root.title(f"ACMEPCHI · MEP Designer 30 汉化 v{__version__}")
        root.geometry("760x540")
        root.minsize(680, 460)

        head = tk.Label(
            root,
            text="把 Archicad 30 的官方中文界面资源移植到 MEP Designer 30",
            font=("Microsoft YaHei UI", 12, "bold"),
            anchor="w",
        )
        head.pack(fill="x", padx=16, pady=(14, 4))
        self.sub = tk.Label(root, text="", anchor="w", justify="left", fg="#444")
        self.sub.pack(fill="x", padx=16)

        bar = tk.Frame(root)
        bar.pack(fill="x", padx=16, pady=10)
        for text, command, width in (
            ("检查环境", self.on_status, 10),
            ("安装中文", self.on_install, 10),
            ("还原英文", self.on_restore, 10),
            ("打开备份目录", self.on_open_backup, 12),
        ):
            tk.Button(bar, text=text, command=command, width=width, height=1).pack(side="left", padx=(0, 8))

        self.log = scrolledtext.ScrolledText(root, wrap="word", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        self.write("准备就绪。建议先点“检查环境”。")
        self.on_status()

    def write(self, text: str) -> None:
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.root.update_idletasks()

    def on_status(self) -> None:
        info = installer.detect(self.cfg)
        self.sub.config(
            text=f"目标：{info['target_dir']}\n来源：{info['source_dir']}\n"
            f"版本：MEP {info['target_version'] or '未知'} / Archicad {info['source_version'] or '未知'}，当前语言 {info['target_uilanguage'] or '未知'}"
        )
        self.write("—— 环境检查 ——")
        if info["errors"]:
            for err in info["errors"]:
                self.write(f"[!] {err}")
            return
        plan = installer.preview(self.cfg)["plan"]
        self.write(f"[OK] 待复制 {len(plan['to_copy'])} 个，已相同 {len(plan['identical'])} 个")
        for name in plan["missing_in_source"][:5]:
            self.write(f"[提示] MEP 侧有、中文侧无：{name}")

    def on_install(self) -> None:
        if not messagebox.askokcancel("确认", "将先自动备份，再覆盖目标语言资源。继续？"):
            return
        try:
            result = installer.install(self.cfg, self.logger)
        except installer.GuardError as exc:
            messagebox.showerror("无法安装", str(exc))
            return
        self.write("—— 安装完成 ——")
        self.write(f"备份：{result['backup']}")
        self.write(f"复制：{len(result['copied'])} 个，剩余差异：{len(result['remaining'])} 个")
        self.write("请启动 MEP Designer 30（演示模式亦可）确认界面语言。")

    def on_restore(self) -> None:
        try:
            result = installer.restore_latest(self.cfg, self.logger)
        except installer.GuardError as exc:
            messagebox.showerror("无法还原", str(exc))
            return
        self.write("—— 已还原 ——")
        self.write(f"来源备份：{result['backup']}，还原 {result['restored']} 个文件")

    def on_open_backup(self) -> None:
        paths.BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["explorer", str(paths.BACKUP_ROOT)])


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    main()
