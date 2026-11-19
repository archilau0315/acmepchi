# ACMEPCHI 29 · MEP Designer 29 汉化工具

> 内部使用 · 不对外分发 / Internal use only
> 中文资源来自本机已安装的 **Archicad 29 中文版**，不翻译、不反编译、不改程序本体。
> Chinese resources come from the locally installed **Archicad 29 (CHI)**; no translation, decompilation or binary patching of the application itself.

---

## 1. 当前状态 / Status

**中文**
本项目按「**MEP Designer 与 Archicad 构建号不同步**」处理，因此汉化只在工作环境层面进行：

| 项目 | 版本 |
|---|---|
| MEP Designer 29 | 29.0.0.**3200** |
| Archicad 29（中文资源来源） | 29.0.0.**5003** |

已实测完成：
- 菜单标题 95 处、用户级界面缓存 3520 处汉化（菜单栏、左侧工具面板分组、命令布局）
- 程序启动稳定，可长时间驻留，无崩溃报告
- 一键备份与还原可用

**不做**：MUI 资源整文件替换。跨构建替换已实测会导致程序在 15 秒内退出，因此对话框等文案保持英文。

**English**
This project assumes **MEP Designer and Archicad build numbers are never in sync**, so localisation stays at the work-environment layer:

| Item | Version |
|---|---|
| MEP Designer 29 | 29.0.0.**3200** |
| Archicad 29 (CHI resource source) | 29.0.0.**5003** |

Verified: 95 XML menu titles and 3520 user-level UI cache entries localised (menu bar, tool palette groups, command layouts); the app stays stable with no crash report; backup/rollback work.

Not done: whole-file MUI replacement — cross-build replacement was measured to close the app within 15 seconds, so dialogs remain English.

---

## 2. 与 30 版的差异 / Differences from v30

- 词典改为**按资源结构配对**（祖先 `#id` 路径 + 字段名），不再依赖文件内字符串顺序，因此能处理跨构建差异
- 用户级 bin 扫描路径覆盖 `WorkEnvironment`、`Latest WorkEnvironment`（29 为英文目录名）与 30 的 `LimitedWorkEnvironment`、`最近的工作环境`
- 版本探测、用户目录前缀全部由 `data/mui-map.json` 驱动（`reg_major`、`product`），不写死版本号
- 新增构建号一致性拦截，避免误装后程序无法启动

---

## 3. 目录结构 / Layout

```
acmepchi29/
├─ src/acme_lp/          # 核心包 / core package
│  ├─ paths.py           # 安装探测、配置、日志 / detection, config, logging
│  ├─ installer.py       # 安装/还原编排与校验 / install & restore
│  ├─ verify.py          # 文件比对 / file diff
│  ├─ wepatch.py         # 工作环境 XML + bin 汉化 / work-environment localisation
│  ├─ dictbuild.py       # 英中词典（按资源结构配对）/ dictionary builder
│  ├─ we_i18n.py         # 菜单标题词表 / menu title terms
│  ├─ backup.py          # 备份还原 / backup & restore
│  ├─ gui.py             # 图形界面 / GUI
│  └─ cli.py             # 命令行 / CLI
├─ bin/acmepchi.bat      # 双击启动 / double-click launcher
├─ bin/exe_entry.py      # exe 打包入口 / PyInstaller entry
├─ data/mui-map.json     # 版本映射与排除名单 / version map & exclusions
├─ tests/                # 离线自检 / offline self-tests
├─ readme.md
└─ debug_log_1.md        # 变更记录 / changelog
```

---

## 4. 使用说明 / Usage

```powershell
$env:PYTHONPATH = "e:\works\Aidev\AddOn\acmepchi\acmepchi29\src"
python -m acme_lp.cli status      # 检查环境（含构建号一致性）
python -m acme_lp.cli preview     # 预览待替换文件
python -m acme_lp.cli install     # 移植 MUI + 汉化工作环境
python -m acme_lp.cli restore     # 还原 MUI
python -m acme_lp.cli we          # 仅汉化工作环境
python -m acme_lp.cli we-restore  # 还原工作环境
python -m acme_lp.cli we --dry-run  # 只统计命中，不写文件
```

或双击 `bin\acmepchi.bat` 使用图形界面。操作前请完全退出 MEP Designer；每次写入自动备份到 `%LOCALAPPDATA%\ACMEPCHI\backup\`。

当前 `replace_mui=false`：`install` 等同于只做工作环境汉化，不会覆盖任何 MUI 文件。

---

## 5. 打包 exe / Building the exe

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --uac-admin `
  --name ACMEPCHI-29 --paths src `
  --add-data "data;data" --add-data "src/acme_lp/data;acme_lp/data" `
  bin/exe_entry.py
```

产物为 `dist\ACMEPCHI-29.exe`（单文件、无控制台、请求管理员权限）。

---

## 6. 变更记录 / Changelog

见 `debug_log_1.md`。
