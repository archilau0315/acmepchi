"""路径、版本与日志探测（仅 Windows）。"""

from __future__ import annotations

import ctypes
import json
import logging
import os
import sys
from pathlib import Path

APP_NAME = "ACMEPCHI"
LOCAL_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME
LOG_DIR = LOCAL_DIR / "logs"
BACKUP_ROOT = LOCAL_DIR / "backup"
_HERE = Path(__file__).resolve()
if getattr(sys, "frozen", False):
    # PyInstaller 打包后资源解压在 _MEIPASS，源码目录不再存在
    PACKAGE_ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
else:
    PACKAGE_ROOT = next(
        (base for base in (_HERE.parents[2], _HERE.parents[1]) if (base / "data" / "mui-map.json").exists()),
        _HERE.parents[2],
    )
CONFIG_PATH = PACKAGE_ROOT / "data" / "mui-map.json"

PROGRAM_FILES = [Path(os.environ.get("ProgramFiles", r"C:\Program Files")), Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))]


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_logger(name: str = "acmepchi") -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(LOG_DIR / "acmepchi.log", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    if sys.stderr is not None:  # 打包成无控制台 exe 时没有 stderr
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(fmt)
        logger.addHandler(sh)
    return logger


def _reg_default_value(root: str, subkey: str) -> str:
    """读取注册表某个键的默认值（Graphisoft 存的是 exe 路径）。"""
    if os.name != "nt":
        return ""
    try:
        import winreg
    except ImportError:
        return ""
    try:
        with winreg.OpenKey(getattr(winreg, root), subkey) as key:
            value, _ = winreg.QueryValueEx(key, "")
            return str(value)
    except OSError:
        return ""


def _find_by_registry(reg_root: str, major: str) -> Path | None:
    """在 HKCU\\Software\\GRAPHISOFT\\<reg_root> 下找版本号含 major 的子键，取其 exe 路径。"""
    if os.name != "nt":
        return None
    try:
        import winreg
    except ImportError:
        return None
    base = rf"Software\GRAPHISOFT\{reg_root}"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base) as key:
            index = 0
            while True:
                try:
                    name = winreg.EnumKey(key, index)
                except OSError:
                    break
                index += 1
                if major in name:
                    exe = _reg_default_value("HKEY_CURRENT_USER", rf"{base}\{name}")
                    if exe and Path(exe).exists():
                        return Path(exe)
    except OSError:
        return None
    return None


def find_product_dir(cfg: dict, which: str = "target") -> Path | None:
    """定位安装目录：优先注册表，其次 Program Files 扫描。"""
    if which == "target":
        reg_root, exe_name, dir_name = cfg["product_reg_root"], cfg["product_exe"], cfg["product_install_dir"]
    else:
        reg_root, exe_name, dir_name = cfg["source_reg_root"], cfg["source_exe"], cfg["source_install_dir"]

    exe = _find_by_registry(reg_root, cfg.get("reg_major", "29."))
    if exe:
        return exe.parent
    for base in PROGRAM_FILES:
        candidate = base / "GRAPHISOFT" / dir_name
        if (candidate / exe_name).exists():
            return candidate
    return None


def file_version(path: Path) -> str:
    """读取 exe 的 FileVersion（如 29.0.0.2901），失败返回空串。"""
    try:
        size = ctypes.windll.version.GetFileVersionInfoSizeW(str(path), None)
        if not size:
            return ""
        buf = ctypes.create_string_buffer(size)
        if not ctypes.windll.version.GetFileVersionInfoW(str(path), 0, size, buf):
            return ""
        ptr = ctypes.c_void_p()
        length = ctypes.c_uint()
        if not ctypes.windll.version.VerQueryValueW(buf, "\\", ctypes.byref(ptr), ctypes.byref(length)):
            return ""
        raw = ctypes.string_at(ptr, 16)
        ms, ls = int.from_bytes(raw[8:12], "little"), int.from_bytes(raw[12:16], "little")
        return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
    except Exception:  # noqa: BLE001 - 版本读取失败不应中断流程
        return ""


def read_uilanguage(install_dir: Path) -> str:
    dat = install_dir / "uilanguage.dat"
    if not dat.exists():
        return ""
    return dat.read_text(encoding="utf-8", errors="ignore").strip()


def write_uilanguage(install_dir: Path, language: str) -> None:
    (install_dir / "uilanguage.dat").write_text(language + "\n", encoding="ascii", newline="\n")
