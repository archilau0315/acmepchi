# ACMEPCHI · MEP Designer 30 中文界面移植工具

> 内部使用 · 不对外分发 · Internal use only
> 中文资源来源：本机已安装的 **Archicad 30 中文版（CHI）**，不涉及翻译、反编译或修改程序本体。
> Chinese resources come from the locally installed **Archicad 30 (CHI)**; no translation, decompilation or binary patching of the application itself.

---

## 1. 这是个什么工具 / What it does

**中文**
MEP Designer 30 独立版只提供英文（INT）界面。本工具把同源同构建的 Archicad 30 中文界面资源（`*.mui` 卫星文件）移植过来，并补齐不来自 MUI 的三处界面文案（菜单标题、工具面板分组名、用户级命令布局快照），同时提供一键备份与还原。

**English**
The standalone MEP Designer 30 ships with an English (INT) UI only. This tool ports the official Simplified-Chinese UI satellites (`*.mui`) from the co-installed, same-build Archicad 30 (CHI), then localises the three UI texts that do **not** live in MUI files (menu titles, tool-palette group names, user-level command-layout snapshot), with one-click backup and rollback.

### 界面文案从哪里来 / Where the UI text comes from

| 位置 / Source | 内容 / Content | 处理方式 / Handling |
|---|---|---|
| `MEP Designer 30\en\*.mui` | 对话框、控件、提示文本 / dialogs, controls, hints | 用 Archicad 中文版同名文件覆盖 / overwritten by CHI satellites |
| `MEP Designer 30\{en,zh-CN}\MEPPluginUI.dll.mui` | 工具名、菜单、对话框、提示与告警 / tool names, menus, dialogs, tooltips & alerts | 解析 PE 资源表，整体重写 JSNL 内 JSON 并用空格补齐 / rebuild JSNL JSON in place, space-padded |
| `Defaults\MEP Designer\WorkEnvironment\*.xml` | 菜单标题、工具面板分组名 / menu titles, palette groups | 词典 + 手工词表原位替换 / in-place replacement |
| `%APPDATA%\GRAPHISOFT\MEP Designer 30*\**\*.bin` | 用户级界面文案缓存 / user-level UI text cache | UTF-16LE 等长替换 / length-preserving replacement |

### 覆盖范围 / Coverage

`we` 会扫描用户配置目录下以下位置的 `.bin`（存在即处理，缺失自动跳过）：

| 相对路径 / Relative path | 内容 / Content |
|---|---|
| `LimitedWorkEnvironment\Command Layouts\*.bin` | 菜单栏与命令标签 / menu bar & command labels |
| `LimitedWorkEnvironment\Tools\*.bin` | 工具面板分组名（Ducts/Pipes/Electrical…）/ palette group names |
| `LimitedWorkEnvironment\Workspaces\*.bin` | 工作空间布局 / workspace layout |
| `Latest WorkEnvironment\Workspaces\*.bin` | 最近使用的布局 / recent layouts |
| `最近的工作环境\工具\*.bin` | 工具面板中文目录缓存 / localized palette cache |
| `最近的工作环境\工作空间\*.bin` | 工作空间中文目录缓存 / localized workspace cache |

> **重要 / Important**：`uilanguage.dat` 始终保持 `en`；`en\ACSpecFolders.dll.mui` 必须保留英文原版，否则程序会在 5 秒内静默退出。
> `uilanguage.dat` stays `en`; `en\ACSpecFolders.dll.mui` must remain the English original, otherwise the app silently exits within 5 seconds.
> 该文件已列入 `data\mui-map.json` 的 `exclude` 名单，`install` 会自动跳过。/ This file is listed in `exclude` in `data\mui-map.json` and is skipped automatically.

---

## 2. 目录结构 / Layout

```
acmepchi/
├─ data/mui-map.json              产品/版本/目录映射配置 · product & path config
├─ src/acme_lp/
│  ├─ paths.py                    安装目录、版本、语言标识探测 · path/version probing
│  ├─ backup.py                   备份、还原、清单哈希 · backup & restore
│  ├─ verify.py                   资源比对与安装计划 · resource diff & install plan
│  ├─ installer.py                检测/安装/还原编排 · install orchestration
│  ├─ langswitch.py               中英一键切换 · EN↔ZH switcher
│  ├─ dictbuild.py                英中词典构建与缓存 · EN→ZH dictionary builder
│  ├─ wepatch.py                  工作环境 XML / bin 汉化 · work-environment patcher
│  ├─ muitext.py                  MUI 文本汉化（PE + JSON）· MUI text patcher (PE + JSON)
│  ├─ we_i18n.py                  菜单标题按 GUID 对齐 · menu titles by GUID
│  ├─ data/mep_terms.json         手工词表 · curated term list
│  ├─ data/mep_ui_zh.json         界面文本英中对照（约 650 条）· EN→ZH UI text map
│  ├─ data/mui_dict.json          词典缓存（自动生成）· dictionary cache
│  ├─ cli.py                      命令行入口 · CLI
│  └─ gui.py                      图形界面 · GUI
├─ tests/test_mapping.py          离线自检 · offline self-check
├─ bin/acmepchi.bat               双击启动 · double-click launcher
├─ bin/exe_entry.py               exe 打包入口 · PyInstaller entry
├─ dist/ACMEPCHI-30.exe           打包产物（不入库）· built exe (untracked)
└─ debug_log_1.md                 变更记录 · changelog
```

---

## 3. 使用说明 / Usage

### 图形界面（推荐）/ GUI (recommended)

双击 `bin\acmepchi.bat` → 依次点 **检查环境 → 安装中文**；还原点 **还原英文**。
双击 `bin\acmepchi.bat`, then **检查环境 → 安装中文**; use **还原英文** to roll back.

装好后可用 **切换为英文 / 切换为中文** 按钮随时互切（约 1 秒，需先退出 MEP Designer）。
After installation, the **切换为英文 / 切换为中文** button switches languages in about a second (MEP Designer must be closed).

### 命令行 / CLI

```powershell
$env:PYTHONPATH = "e:\works\Aidev\AddOn\acmepchi\acmepchi30\src"
python -m acme_lp.cli status       # 检查环境 · environment check
python -m acme_lp.cli preview      # 预览将覆盖的文件 · preview
python -m acme_lp.cli install      # 备份 + 安装 MUI，末尾自动执行 we · install (+ we)
python -m acme_lp.cli lang         # 中英互切 · toggle EN ↔ ZH
python -m acme_lp.cli lang --to en # 切到英文 · switch to English
python -m acme_lp.cli lang --to zh # 切到中文 · switch to Chinese
python -m acme_lp.cli restore      # 还原 MUI · restore MUI
python -m acme_lp.cli we --dry-run # 只统计工作环境命中数 · stats only
python -m acme_lp.cli we           # 汉化工作环境 XML 与 bin · patch WE files
python -m acme_lp.cli we --fix-length   # 可选：同时把 bin 长度字段改为中文字符数
python -m acme_lp.cli we-restore   # 还原工作环境 XML 与 bin · restore WE files
python -m acme_lp.cli backups      # 查看最近备份 · latest backup
```

安装模式 / Modes：

- `replace`（默认）：用中文 `.mui` 覆盖目标 `en\` 目录，`uilanguage.dat` 保持 `en`。
- `switch`：新建 `zh-CN\` 目录并改写 `uilanguage.dat`（个别构建可能不支持）。

### 备份位置 / Backup

```
%LOCALAPPDATA%\ACMEPCHI\backup\<时间戳>\      # MUI 全量备份 · full MUI snapshot
%LOCALAPPDATA%\ACMEPCHI\backup\we-<时间戳>\   # 工作环境备份，含 manifest.json
%LOCALAPPDATA%\ACMEPCHI\logs\acmepchi.log     # 运行日志 · runtime log
```

### 回滚 / Rollback

```powershell
python -m acme_lp.cli we-restore   # 回溯所有 we-* 备份，还原 bin 与两个 XML
python -m acme_lp.cli restore      # 从最近一次全量备份还原 en\ 与 uilanguage.dat
```

`we` 与 `we-restore` 都要求 **MEP Designer 已完全退出**（运行中会直接报错，不会强杀进程）。
Both `we` and `we-restore` require MEP Designer to be closed; a running instance causes a hard error, never a forced kill.

---

## 4. 实现要点 / How it works

| 步骤 / Step | 做法 / Implementation |
|---|---|
| 建词典 / Dictionary | 英文原版 MUI 与 Archicad 中文版同名文件按 `"#id"` 分段，段内 `text/name` 数量相等时按序配对，还原 `\uXXXX`，得到约 9 400 条英文→中文；缓存为 `src/acme_lp/data/mui_dict.json` |
| XML / XML files | 只替换 `<Name ...>英文</Name>` 与 `title="英文"`，仅当文本为纯 ASCII 且命中词表；`&` 快捷键前缀自动兼容；XML 实体自动转义 |
| bin / Snapshot | 按英文长度降序在 UTF-16LE 字节流中查找，命中「前后字符非字母数字」或「文本前紧邻 `01 00 + 字符数` 记录头」才替换；译文更短时用 `U+FFFF` 补齐，文件长度不变（默认保留原长度字段，`--fix-length` 改写为中文字符数） |
| 幂等 / Idempotent | 已是中文的内容不会再命中英文键，重复执行命中数为 0 |

---

## 5. 前置条件与限制 / Requirements & Limits

- 必须安装 **Archicad 30 中文版**（提供中文资源）与 **MEP Designer 30**（3001 构建）。
- 写入 `C:\Program Files` 需要管理员权限；失败时请右键“以管理员身份运行”。
- 工作环境 bin 带只读属性，`we` 会先解除只读再写入；还原时按原属性写回。
- 不要删除 `Standard Commands 30.bin`，删除会导致“设计菜单消失”。
- MEP Designer 是**单独授权产品**，无授权时只能进入演示模式；本工具不涉及授权。
- 升级 MEP Designer 后资源版本会变化，请先 `we-restore` / `restore` 再重新 `install`。
- `en` 目录始终保持英文原版，中文只写入 `zh-CN`，因此中英互切不会残留对方语言的文本。
- 内部使用，请勿向外分发移植后的资源包。

---

## 6. 已知问题 / Known Issues

- `ACSpecFolders.dll.mui` 必须保持英文，其余 MUI 可安全替换。
- 帮助文本、启动画面等少量 MEP 专有字符串可能仍为英文。
- 无授权环境下启动会提示 license，与汉化无关。

---

## 7. 分发给最终用户 / End-user install

**中文**
1. 前提：本机已安装 **MEP Designer 30**，且装有**同构建的 Archicad 30 中文版**（中文资源来源）。
2. 完全退出 MEP Designer。
3. 双击 `dist\ACMEPCHI-30.exe`，在 UAC 提示中选「是」（写入 Program Files 需要管理员权限）。
4. 依次点 **检查环境 → 安装中文**，看到「安装完成」后重新启动 MEP Designer。
5. 想恢复英文点 **还原英文**；备份在 `%LOCALAPPDATA%\ACMEPCHI\backup`。

**English**
1. Prerequisite: **MEP Designer 30** plus a **same-build Archicad 30 (CHI)** installed on the machine.
2. Quit MEP Designer completely.
3. Double-click `dist\ACMEPCHI-30.exe` and confirm the UAC prompt (admin rights are needed for Program Files).
4. Click **检查环境 → 安装中文**, then restart MEP Designer.
5. Use **还原英文** to roll back; backups live in `%LOCALAPPDATA%\ACMEPCHI\backup`.

> exe 只适用于 MEP Designer 30（build 3001）。 / The exe targets MEP Designer 30 (build 3001) only.

## 8. 打包 exe / Building the exe

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --uac-admin `
  --name ACMEPCHI-30 --paths src `
  --add-data "data;data" --add-data "src/acme_lp/data;acme_lp/data" `
  bin/exe_entry.py
```

产物在 `dist\ACMEPCHI-30.exe`（约 11 MB，单文件，内嵌 tkinter 与词典缓存）。
Output: `dist\ACMEPCHI-30.exe` (~11 MB, single file, bundles tkinter and the dictionary cache).

---

## 9. 变更记录 / Changelog

见 `debug_log_1.md`。
