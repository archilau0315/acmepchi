"""PyInstaller 入口：打包成单文件 exe 时启动图形界面。"""

import os

os.environ.setdefault("PYTHONUTF8", "1")

from acme_lp.gui import main  # noqa: E402 - 先设置环境变量再导入

if __name__ == "__main__":
    main()
