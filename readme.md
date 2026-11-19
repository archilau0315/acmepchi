# ACMEPCHI · MEP Designer 30 中文界面移植工具

> 内部使用 · 不对外分发 · Internal use only
> 中文资源来源：本机已安装的 **Archicad 30 中文版（CHI）**，不涉及翻译、反编译或修改程序本体。

---

## 1. 这是个什么工具 / What it does

**中文**
MEP Designer 30 独立版只有英文（INT）界面。本工具把它同源同构建的 Archicad 30 中文界面资源（`*.mui` 卫星文件）移植过来，实现中文界面，并提供一键备份与还原。

**English**
The standalone MEP Designer 30 ships with English (INT) UI only. This tool ports the official Simplified-Chinese UI satellites (`*.mui`) from the co-installed, same-build Archicad 30 (CHI) into MEP Designer 30, with one-click backup and rollback.

### 原理 / Why it works

| 依据 | 实测结果 |
|---|---|
| 构建版本 / Build | 两者均为 `30.0.0 R1 (3001)` |
| 核心 DLL / Core DLLs | `MEPPluginUI / MEPElements / MEPAPI / MEPDistSystemsBrowser / MEPLogicCore` 等 SHA256 完全一致 |
| 语言资源 / UI satellites | 两边各 85 个 `.mui`，文件名 1:1 对应 |

界面文本不在 exe/dll 里，而在语言卫星目录（`en\`、`zh-CN\`）中，由 `uilanguage.dat` 决定加载哪个目录。因此替换卫星文件即可换语言，**不改动任何可执行文件**。

---

## 2. 目录结构 / Layout

```
acmepchi/
├─ data/mui-map.json        产品/版本/目录映射配置
├─ src/acme_lp/
│  ├─ paths.py              安装目录、版本、语言标识探测
│  ├─ backup.py             备份、还原、清单哈希
│  ├─ verify.py             资源比对与安装计划
│  ├─ installer.py          检测/安装/还原编排（含版本闸门）
│  ├─ cli.py                命令行入口
│  └─ gui.py                图形界面
├─ tests/test_mapping.py    离线自检
├─ bin/acmepchi.bat         双击启动
└─ debug_log_1.md           变更记录
```

---

## 3. 使用说明 / Usage

### 图形界面（推荐）

双击 `bin\acmepchi.bat` → 依次点 **检查环境 → 安装中文**。还原点 **还原英文**。

### 命令行 / CLI

```powershell
$env:PYTHONPATH = "e:\works\Aidev\AddOn\acmepchi\src"
python -m acme_lp.cli status      # 检查环境、待复制数量
python -m acme_lp.cli preview     # 预览将覆盖的文件
python -m acme_lp.cli install     # 备份 + 安装（默认 replace 模式）
python -m acme_lp.cli restore     # 从最近一次备份还原
python -m acme_lp.cli backups     # 查看最近备份位置
```

安装模式 / Modes：

- `replace`（默认）：用中文 `.mui` 覆盖目标 `en\` 目录，`uilanguage.dat` 保持 `en`。绕开 INT 版语言白名单。
- `switch`：新建 `zh-CN\` 目录并改写 `uilanguage.dat`，界面语言切换为中文（个别构建可能不支持）。

### 备份位置 / Backup

```
%LOCALAPPDATA%\ACMEPCHI\backup\<时间戳>\   # 含原 en 目录、uilanguage.dat、manifest.json
%LOCALAPPDATA%\ACMEPCHI\logs\acmepchi.log  # 运行日志
```

---

## 4. 前置条件与限制 / Requirements & Limits

- 必须安装 **Archicad 30 中文版**（提供中文资源）与 **MEP Designer 30**（3001 构建）。
- 写入 `C:\Program Files` 需要管理员权限；失败时请右键“以管理员身份运行”。
- MEP Designer 是**单独授权产品**，无授权时只能进入演示模式；本工具不涉及授权。
- 升级 MEP Designer 后资源版本会变化，请先 `restore` 再重新 `install`。
- 内部使用，请勿向外分发移植后的资源包。

---

## 5. 已知问题 / Known Issues

- 启动崩溃排查中：曾出现 Bug Reporter 崩溃窗口，已还原英文资源做 A/B 验证。
- 部分 MEP Designer 独有字符串（帮助、启动画面、自动更新插件）可能仍为英文，后续按差异清单补齐。

---

## 6. 变更记录 / Changelog

见 `debug_log_1.md`。
