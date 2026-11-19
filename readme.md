# ACMEPCHI · MEP Designer 界面汉化工具集

> 内部使用 · 不对外分发 · Internal use only
> 中文资源来自本机已安装的 **Archicad 中文版**，不翻译、不反编译、不改程序本体。
> Chinese resources come from the locally installed **Archicad (CHI)**; no translation, decompilation or binary patching of the application itself.

---

## 1. 项目说明 / What this is

**中文**
本仓库按主版本分目录，每个目录是一套独立的汉化工具：把同源同构建的 Archicad 中文界面资源（`*.mui`）移植到英文版 MEP Designer，并补齐不来自 MUI 的界面文案（菜单标题、工具面板分组名、用户级命令布局缓存），提供一键备份与还原。

**English**
This repository is split by major version. Each directory is a self-contained localisation tool that ports the official Simplified-Chinese UI satellites (`*.mui`) from the co-installed, same-build Archicad into the English MEP Designer, then localises the UI texts that do **not** live in MUI files (menu titles, palette group names, user-level command-layout cache), with one-click backup and rollback.

### 界面文案从哪里来 / Where the UI text comes from

| 位置 / Source | 内容 / Content | 处理方式 / Handling |
|---|---|---|
| `<产品目录>\en\*.mui` | 对话框、控件、提示文本 / dialogs, controls, hints | 用 Archicad 中文版同名文件覆盖 / overwritten by CHI satellites |
| `Defaults\<产品>\WorkEnvironment\*.xml` | 菜单标题、工具面板分组名 / menu titles, palette groups | 词典 + 手工词表原位替换 / in-place replacement |
| `%APPDATA%\GRAPHISOFT\<产品> 30*\**\*.bin` | 用户级界面文案缓存 / user-level UI text cache | UTF-16LE 等长替换 / length-preserving replacement |

---

## 2. 目录结构 / Layout

```
acmepchi/
├─ acmepchi30/          # MEP Designer 30 汉化工具（已完成）/ v30 tool (done)
│  ├─ src/acme_lp/      # Python 包 / Python package
│  ├─ bin/              # 启动脚本 / launcher
│  ├─ data/             # 映射配置 / mapping config
│  ├─ tests/            # 自检 / self-test
│  ├─ docs/             # 开发记录 / dev notes
│  ├─ readme.md         # v30 详细说明 / v30 details
│  └─ debug_log_1.md    # v30 变更记录 / v30 change log
├─ acmepchi29/          # MEP Designer 29 汉化工具（工作环境汉化，MUI 保持英文）/ v29 (work-environment only)
└─ readme.md            # 本文件 / this file
```

---

## 3. 使用说明 / Usage

**中文**
进入对应版本目录，双击 `bin\acmepchi.bat` 打开图形界面，或在该目录下用命令行执行：

```powershell
$env:PYTHONPATH="$PWD\src"
python -m acme_lp.cli status      # 检查环境
python -m acme_lp.cli install     # 移植 MUI + 汉化工作环境
python -m acme_lp.cli we          # 仅汉化工作环境（菜单/工具面板）
python -m acme_lp.cli we-restore  # 还原工作环境
python -m acme_lp.cli restore     # 还原 MUI
```

**English**
Enter the version folder, double-click `bin\acmepchi.bat` for the GUI, or run from that folder:

```powershell
$env:PYTHONPATH="$PWD\src"
python -m acme_lp.cli status      # check environment
python -m acme_lp.cli install     # port MUI + localise work environment
python -m acme_lp.cli we          # work environment only (menus / palettes)
python -m acme_lp.cli we-restore  # roll back work environment
python -m acme_lp.cli restore     # roll back MUI
```

> **重要 / Important**：操作前请完全退出 MEP Designer；每次写入都会自动备份到 `%LOCALAPPDATA%\ACMEPCHI\backup\`。
> Fully quit MEP Designer before running; every write is backed up to `%LOCALAPPDATA%\ACMEPCHI\backup\`.
