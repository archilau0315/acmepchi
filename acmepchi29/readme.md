# ACMEPCHI 29 · MEP Designer 29 汉化工具

> 内部使用 · 不对外分发 / Internal use only
> 中文资源来自本机已安装的 **Archicad 29 中文版**，不翻译、不反编译、不改程序本体。
> Chinese resources come from the locally installed **Archicad 29 (CHI)**; no translation, decompilation or binary patching of the application itself.

---

## 1. 当前状态 / Status

**中文**
代码已完成，可检测环境、移植 MUI、汉化工作环境（菜单栏、工具面板分组、命令布局缓存）、一键备份与还原。

但本机环境暂不具备验证条件：

| 项目 | 版本 |
|---|---|
| MEP Designer 29 R1 INT | 29.0.0.**3000** |
| Archicad 29 R1 CHI | 29.0.0.**5003** |

两者构建号不同，MUI 资源结构对不上，替换后 MEP Designer 会静默退出（实测：整批替换启动即退；仅换 3 个 MEP 文件可启动但十几秒后退出）。因此工具内置**构建号一致性校验**：不一致时直接拦截，不做任何写入。

**下一步**：把 MEP Designer 29 更新到与 Archicad 29 相同的构建（29.2 / 5003），再执行 `check` 应无报错，即可安装验证并打包 exe。

**English**
Code is complete: environment check, MUI porting, work-environment localisation (menus, palette groups, command-layout cache), backup and rollback.

The local pair is **29.0.0.3000** (MEP Designer 29) vs **29.0.0.5003** (Archicad 29 CHI). Different builds mean incompatible MUI resources; replacing them makes MEP Designer exit silently. The tool therefore **blocks installation when build numbers differ**. Update MEP Designer 29 to the same build (29.2 / 5003), re-check, then verify and build the exe.

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

---

## 5. 打包 exe / Building the exe

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --uac-admin `
  --name ACMEPCHI-29 --paths src `
  --add-data "data;data" --add-data "src/acme_lp/data;acme_lp/data" `
  bin/exe_entry.py
```

产物为 `dist\ACMEPCHI-29.exe`。**构建号统一并验证通过后**再执行此命令对外发布。

---

## 6. 变更记录 / Changelog

见 `debug_log_1.md`。
