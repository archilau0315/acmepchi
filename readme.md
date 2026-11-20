# ACMEPCHI

**MEP Designer 30 中文界面移植工具** · Port the official Simplified-Chinese UI into MEP Designer 30

[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)](#当前状态--status)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](#当前状态--status)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%2F%2011-lightgrey.svg)](#系统要求--requirements)
[![License](https://img.shields.io/badge/license-Internal%20use-orange.svg)](#免责声明--disclaimer)

> 内部工具，不对外分发 · Internal tool, not for redistribution

---

## 目录 / Table of Contents

- [项目简介 / Overview](#项目简介--overview)
- [当前状态 / Status](#当前状态--status)
- [功能特性 / Features](#功能特性--features)
- [系统要求 / Requirements](#系统要求--requirements)
- [快速开始 / Quick Start](#快速开始--quick-start)
- [备份与还原 / Backup & Rollback](#备份与还原--backup--rollback)
- [项目结构 / Project Structure](#项目结构--project-structure)
- [工作原理 / How It Works](#工作原理--how-it-works)
- [打包 / Build](#打包--build)
- [已知限制 / Known Limits](#已知限制--known-limits)
- [变更记录 / Changelog](#变更记录--changelog)
- [免责声明 / Disclaimer](#免责声明--disclaimer)

---

## 项目简介 / Overview

**中文**

MEP Designer 30 独立版只提供英文（INT）界面。本工具把**同源同构建**的 Archicad 30 中文版（CHI）界面资源 `*.mui` 移植到 MEP Designer 30，并补齐不存放在 MUI 里的界面文案（`MEPPluginUI.dll.mui` 内的 JSON 字符串表、工作环境 XML 的菜单标题与工具面板分组名）。

不翻译、不反编译、不修改程序本体，只搬运厂商自带的中文资源；所有写入前自动备份，支持一键还原。

**English**

The standalone MEP Designer 30 ships with an English (INT) UI only. This tool ports the `*.mui` UI satellites from the **co-installed, same-build** Archicad 30 (CHI), then localises the UI strings that do not live in MUI files (the JSON string table inside `MEPPluginUI.dll.mui`, plus menu titles and palette group names in the work-environment XML).

No translation, no decompilation, no patching of the application itself — only vendor-provided Chinese resources are moved, with automatic backup before every write and one-click rollback.

### 界面文案来源 / Where the UI Text Comes From

| 位置 / Source | 内容 / Content | 处理方式 / Handling |
|---|---|---|
| `<产品目录>\en\*.mui` | 对话框、控件、提示 / dialogs, controls, hints | 用 Archicad 中文版同名文件覆盖 / overwritten by CHI satellites |
| `{en,zh-CN}\MEPPluginUI.dll.mui` | 工具名、菜单、对话框、告警 / tool names, menus, dialogs, alerts | 解析 PE 资源表，整段重写 JSNL 内 JSON，空格补齐 / rebuild JSNL JSON in place, space-padded |
| `Defaults\<产品>\WorkEnvironment\*.xml` | 菜单标题、面板分组名 / menu titles, palette groups | 词典 + 手工词表原位替换 / in-place replacement |

---

## 当前状态 / Status

| 项目 / Item | 状态 / State |
|---|---|
| 版本 / Version | `0.1.0` |
| 目标程序 / Target | MEP Designer 30（build `3001`） |
| 资源来源 / Source | Archicad 30 中文版（CHI，同构建） |
| 交付形态 / Delivery | 源码 + `dist\ACMEPCHI-30.exe`（单文件，约 11 MB） |
| 界面语言 / UI | 图形界面 + 命令行 / GUI and CLI |
| 维护范围 / Scope | 仅 MEP Designer 30 / MEP Designer 30 only |

**中文**
MEP Designer 30 已完成全流程验证：资源迁移、MUI 文本重写、工作环境汉化、备份还原均可正常执行，打包产物可独立运行。

**English**
The MEP Designer 30 toolchain is complete and verified end to end: satellite migration, MUI text rewriting, work-environment localisation, and backup/rollback all work, and the packaged executable runs standalone.

---

## 功能特性 / Features

**中文**

- **环境检测**：自动定位 MEP Designer 30 与 Archicad 30 安装目录，校验构建号与语言目录。
- **全量资源迁移**：85 个 `.mui` 卫星文件按文件名 1:1 映射复制，自动跳过有兼容性风险的文件。
- **MUI 文本汉化**：解析 PE 资源树，重写 `MEPPluginUI.dll.mui` 内的 JSON 界面文案（约 660 条英中对照表），文件长度不变。
- **工作环境汉化**：菜单标题、工具面板分组名原位替换，已是中文的内容不会被二次处理（幂等）。
- **安全防护**：安装前强制备份；程序运行中拒绝写入；只读属性自动处理；异常可一键还原。
- **双入口**：双击启动的图形界面，以及 `status / preview / install / restore / we / we-restore` 命令行子命令。

**English**

- **Environment check** — locates MEP Designer 30 and Archicad 30, validates build number and language folders.
- **Full satellite migration** — copies 85 `.mui` files with 1:1 name mapping, skipping files known to be incompatible.
- **MUI text localisation** — parses the PE resource tree and rewrites the JSON UI strings inside `MEPPluginUI.dll.mui` (~660 EN→ZH entries) without changing file size.
- **Work-environment localisation** — in-place replacement of menu titles and palette group names; already-Chinese content is never touched (idempotent).
- **Safety first** — mandatory backup before install, writes refused while the app is running, read-only attributes handled, one-click rollback.
- **Two entry points** — a double-click GUI and CLI subcommands `status / preview / install / restore / we / we-restore`.

---

## 系统要求 / Requirements

| 项目 / Item | 要求 / Requirement |
|---|---|
| 操作系统 / OS | Windows 10 / 11（64 位 / x64） |
| Python | 3.9+（仅源码运行需要 / source mode only） |
| MEP Designer | 30（build `3001`） |
| Archicad | 30 中文版（CHI，同构建，提供中文资源 / provides the zh-CN satellites） |
| 权限 / Privileges | 写入 `C:\Program Files` 需要管理员 / admin rights for Program Files |

> 使用 `dist\ACMEPCHI-30.exe` 时无需安装 Python。 / Python is not required when using the built exe.

---

## 快速开始 / Quick Start

### 图形界面（推荐）/ GUI (recommended)

**中文**
1. 完全退出 MEP Designer。
2. 双击 `acmepchi30\bin\acmepchi.bat`；或运行 `acmepchi30\dist\ACMEPCHI-30.exe`（需在 UAC 提示中选「是」）。
3. 依次点击 **检查环境 → 安装中文**，完成后重新启动 MEP Designer。

**English**
1. Quit MEP Designer completely.
2. Double-click `acmepchi30\bin\acmepchi.bat`, or run `acmepchi30\dist\ACMEPCHI-30.exe` (confirm the UAC prompt).
3. Click **检查环境 → 安装中文**, then restart MEP Designer.

### 命令行 / CLI

```powershell
cd acmepchi30
$env:PYTHONPATH = "$PWD\src"

python -m acme_lp.cli status       # 检查环境 · environment check
python -m acme_lp.cli preview      # 预览将覆盖的文件 · preview planned writes
python -m acme_lp.cli install      # 备份 + 安装 MUI，末尾自动执行 we · install (+ we)
python -m acme_lp.cli restore      # 还原 MUI · restore MUI
python -m acme_lp.cli we           # 仅汉化工作环境 · patch work environment only
python -m acme_lp.cli we-restore   # 还原工作环境 · roll back work environment
python -m acme_lp.cli backups      # 查看最近备份 · list latest backups
```

> `we`、`we-restore` 支持 `--dry-run` 只统计命中数，不改写任何文件。
> Both accept `--dry-run` to report matches without writing anything.

---

## 备份与还原 / Backup & Rollback

**中文**

每次写入前自动备份，还原按备份时间倒序回溯：

```
%LOCALAPPDATA%\ACMEPCHI\backup\<时间戳>\      # MUI 全量快照 + manifest.json
%LOCALAPPDATA%\ACMEPCHI\backup\we-<时间戳>\   # 工作环境快照（XML + bin）
%LOCALAPPDATA%\ACMEPCHI\logs\acmepchi.log     # 运行日志
```

- 还原英文：GUI 点 **还原英文**，或执行 `we-restore` + `restore`。
- `we` 与 `we-restore` 要求 MEP Designer 已完全退出，运行中会直接报错，不会强杀进程。

**English**

A backup is taken before every write; rollback walks backups newest-first:

```
%LOCALAPPDATA%\ACMEPCHI\backup\<timestamp>\      # full MUI snapshot + manifest.json
%LOCALAPPDATA%\ACMEPCHI\backup\we-<timestamp>\   # work-environment snapshot (XML + bin)
%LOCALAPPDATA%\ACMEPCHI\logs\acmepchi.log        # runtime log
```

- To revert: click **还原英文** in the GUI, or run `we-restore` then `restore`.
- `we` and `we-restore` require MEP Designer to be closed; a running instance causes a hard error, never a forced kill.

---

## 项目结构 / Project Structure

```
acmepchi/
└─ acmepchi30/                     # MEP Designer 30 工具 / the MEP Designer 30 tool
   ├─ bin/
   │  ├─ acmepchi.bat              # 双击启动 / double-click launcher
   │  └─ exe_entry.py              # exe 打包入口 / PyInstaller entry
   ├─ data/
   │  ├─ mui-map.json              # 产品/版本/路径映射与排除名单 / mapping & exclude list
   │  └─ mep_ui_zh.json            # 界面文本英中对照 / EN→ZH UI text map
   ├─ src/acme_lp/
   │  ├─ paths.py                  # 安装目录、版本、语言标识探测 / path & version probing
   │  ├─ backup.py                 # 备份、还原、清单哈希 / backup & restore
   │  ├─ verify.py                 # 资源比对与安装计划 / resource diff & install plan
   │  ├─ installer.py              # 检测/安装/还原编排 / install orchestration
   │  ├─ dictbuild.py              # 英中词典构建与缓存 / EN→ZH dictionary builder
   │  ├─ muitext.py                # MUI 文本汉化（PE + JSON）/ MUI text patcher
   │  ├─ wepatch.py                # 工作环境 XML 汉化 / work-environment XML patcher
   │  ├─ we_i18n.py                # 菜单标题按 GUID 对齐 / menu titles by GUID
   │  ├─ cli.py                    # 命令行入口 / CLI
   │  ├─ gui.py                    # 图形界面 / GUI
   │  └─ data/                     # 手工词表与词典缓存 / term list & dictionary cache
   ├─ tests/test_mapping.py        # 离线自检 / offline self-check
   ├─ docs/                        # 开发计划与记录 / design notes
   ├─ dist/                        # 打包产物，不入库 / built exe (untracked)
   ├─ readme.md                    # 本工具的详细说明 / tool-level docs
   └─ debug_log_1.md               # 变更记录 / changelog
```

---

## 工作原理 / How It Works

| 步骤 / Step | 做法 / Implementation |
|---|---|
| 词典 / Dictionary | 英文原版 MUI 与 Archicad 中文版同名文件按 `"#id"` 分段配对，得到约 9 400 条英中词条，缓存为 `mui_dict.json` |
| 卫星迁移 / Satellites | `mui-map.json` 决定产品名、构建号与排除名单，按文件名 1:1 复制到目标语言目录 |
| MUI 文本 / MUI text | 解析 DOS/NT 头与资源树，取出 JSNL 2000~2004 正文，按对照表重写 JSON，容量不足时压缩分隔符并补空格 |
| 工作环境 / Work environment | 只替换 `<Name>英文</Name>` 与 `title="英文"`，要求纯 ASCII 且命中词表；XML 实体自动转义 |
| 幂等 / Idempotent | 已是中文的内容不会再命中英文键，重复执行命中数为 0 |

---

## 打包 / Build

```powershell
cd acmepchi30
python -m PyInstaller --noconfirm --clean --onefile --windowed --uac-admin `
  --name ACMEPCHI-30 --paths src `
  --add-data "data;data" --add-data "src/acme_lp/data;acme_lp/data" `
  bin/exe_entry.py
```

产物 / Output：`acmepchi30\dist\ACMEPCHI-30.exe`（单文件，内嵌 tkinter 与词典缓存 / single file, bundles tkinter and dictionary cache）

---

## 已知限制 / Known Limits

**中文**

- `en\ACSpecFolders.dll.mui` 必须保留英文原版，否则程序会在数秒内静默退出；该文件已在排除名单中。
- MEP 专属 MUI（`MEPPluginUI`、`MEPAPI`、`MEPElements` 等）不能整体替换，否则「设计」菜单会消失；这些文件只通过 JSON 文本重写方式汉化。
- 帮助文本、启动画面等少量字符串可能仍为英文。
- 升级 MEP Designer 后资源版本会变化：请先 `we-restore` / `restore`，再重新 `install`。
- 无授权环境下程序只能进入演示模式，与汉化无关。

**English**

- `en\ACSpecFolders.dll.mui` must remain the English original, otherwise the app silently exits within seconds; it is on the exclude list.
- MEP-specific MUI files (`MEPPluginUI`, `MEPAPI`, `MEPElements`, …) cannot be replaced wholesale, or the Design menu disappears; they are localised via JSON text rewriting only.
- A few strings (help text, splash screen) may remain in English.
- After a MEP Designer upgrade the resource build changes: run `we-restore` / `restore` first, then `install` again.
- Without a licence the app starts in demo mode; this is unrelated to localisation.

---

## 变更记录 / Changelog

详见 [acmepchi30/debug_log_1.md](acmepchi30/debug_log_1.md)。
See [acmepchi30/debug_log_1.md](acmepchi30/debug_log_1.md) for the full change history.

---

## 免责声明 / Disclaimer

**中文**
本仓库仅供内部使用，不对外分发。工具只搬运本机已安装的 Archicad 中文版界面资源，不翻译、不反编译、不修改程序本体，不涉及授权绕过。移植后的资源请勿公开传播；使用前请自行确认符合 Graphisoft 许可条款。

**English**
This repository is for internal use only and is not distributed publicly. The tool only moves UI resources from the locally installed Archicad (CHI); it does not translate, decompile, or modify the application, and does not bypass licensing. Do not redistribute ported resources; verify compliance with the Graphisoft licence terms before use.
