"""离线自检：配置、目录映射、语言包来源一致性。"""

from __future__ import annotations

import unittest
from pathlib import Path

from acme_lp import installer, paths, verify


class MappingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = paths.load_config()

    def test_config_keys(self) -> None:
        for key in ("product", "exclude", "source_language_dir", "target_language_dir"):
            self.assertIn(key, self.cfg)

    def test_source_matches_target_names(self) -> None:
        """干净环境：中文资源与英文资源文件名应 1:1。装过则只检查不失败。"""
        info = installer.detect(self.cfg)
        if info["errors"]:
            self.skipTest(f"环境不完整：{info['errors']}")
        src_names = verify.names(info["source_language_dir"])
        dst_names = verify.names(info["target_language_dir"])
        only_source = src_names - dst_names
        self.assertLessEqual(len(only_source), 0, f"中文侧多出文件：{sorted(only_source)[:5]}")

    def test_version_guard(self) -> None:
        """本项目按构建号不同步处理：工作环境模式放行，整文件替换模式必须拦截。"""
        info = installer.detect(self.cfg)
        if not (info["target_version"] and info["source_version"]):
            self.skipTest("未同时安装 MEP Designer 29 与 Archicad 29")
        mismatch = info["target_version"] != info["source_version"]
        blocked = any("构建号不一致" in item for item in info["errors"])
        if self.cfg.get("replace_mui", True):
            self.assertEqual(mismatch, blocked)
        else:
            self.assertFalse(blocked)
            forced = installer.detect({**self.cfg, "replace_mui": True})
            self.assertEqual(mismatch, any("构建号不一致" in item for item in forced["errors"]))


if __name__ == "__main__":
    unittest.main()
