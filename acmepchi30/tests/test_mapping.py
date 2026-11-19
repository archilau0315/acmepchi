"""离线自检：配置、目录映射、语言包来源一致性。"""

from __future__ import annotations

import unittest
from pathlib import Path

from acme_lp import installer, paths, verify


class MappingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = paths.load_config()

    def test_config_keys(self) -> None:
        for key in ("product", "target_build", "source_language_dir", "target_language_dir"):
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
        info = installer.detect(self.cfg)
        if info["errors"] or not info["target_version"]:
            self.skipTest("未安装 MEP Designer 30")
        self.assertIn(self.cfg["target_build"], info["target_version"])


if __name__ == "__main__":
    unittest.main()
