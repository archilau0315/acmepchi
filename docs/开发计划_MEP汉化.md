# ACMEPCHI —— Archicad 30 / MEP Designer 30 内部汉化计划

> 内部使用 · 版本 v0.1（2026-11-19）
> English abstract: A resource-pack patcher (not an Add-On) that ports Graphisoft's own zh-CN UI satellites into the English MEP Designer 30 install, with full backup/rollback and version guard.

---

## 1. 现状诊断（已在本机实测）

| 项目 | 实测结果 | 判定 |
|---|---|---|
| `C:\Program Files\GRAPHISOFT\Archicad 30\uilanguage.dat` | `zh-CN` | Archicad 本体已是中文 |
| 注册表 `HKCU\Software\GRAPHISOFT\Archicad` | `Archicad 30.0.0 CHI R1` | 中文版已装 |
| `Archicad 30\Add-Ons\{Hydronics, Ventilation, 标准…}` | 均含 `zh-CN` 语言目录 | Archicad 内 MEP 工具已是中文 |
| `C:\Program Files\GRAPHISOFT\MEP Designer 30\uilanguage.dat` | `en` | **独立版 MEP Designer 是英文（问题所在）** |
| `MEP Designer 30\` 语言目录 | 仅 `en`（85 个 `.mui`） | 无中文资源 |
| `Archicad 30\zh-CN\` | 85 个 `.mui`，文件名与上表 **1:1 对应** | 现成中文资源可直接复用 |
| `MEPPluginUI / MEPElements / MEPAPI / MEPDistSystemsBrowser / MEPLogicCore / VBTo2DMEPPlugin / BuiltInPropertiesMEPPlugin / ACUserInterface` | 两处文件 SHA256 **完全一致**，均为 `30.0.0 R1 (3001)` | 资源 ID 完全兼容 |

**结论**：MEP Designer 30 是 Archicad 30 同源同构建的独立程序，UI 文本全部放在语言卫星目录（`en\*.mui`）中，由 `uilanguage.dat` 决定加载哪个目录。只要把 Archicad 30 已自带的中文卫星资源搬到 MEP Designer 30 下并切换语言标识，即可得到官方级中文界面 —— **不需要翻译、不需要改 DLL、不需要破解**。

**为什么不做传统 Add-On 插件**：
1. ACAPI 只能*新增*菜单、面板、对话框，**无法替换宿主内建 UI 的文本**，做不出"全汉化"；
2. 本机只装了 `API Development Kit 28`，AC30 需要 DevKit 30，编译链不匹配；
3. 资源移植方案零开发风险、可完全回滚，且用的是厂商自带中文资源。

---

## 2. 产品定义

- 名称：**ACMEPCHI**（Archicad MEP Chinese Patcher）
- 形态：绿色小工具（Python 3 + tkinter，无第三方依赖），双击运行
- 功能：`检测 → 备份 → 安装中文资源 → 校验`，以及 `一键还原`
- 适用范围：`MEP Designer 30 INT` + `Archicad 30 CHI` 同机安装（build 3001）
- 不做：不联网、不改注册表授权信息、不修改任何 `.dll/.exe`

---

## 3. 模块清单（单文件 ≤500 行）

| 文件 | 职责 | 预估行数 |
|---|---|---|
| `src/acme_lp/paths.py` | 探测安装目录、读 `uilanguage.dat`、校验 build 3001 | ~120 |
| `src/acme_lp/backup.py` | 备份清单（manifest.json + SHA256）、还原、完整性校验 | ~150 |
| `src/acme_lp/installer.py` | 源/目标语言目录 1:1 映射、分批复制、`uilanguage.dat` 切换 | ~180 |
| `src/acme_lp/verify.py` | 文件名集合比对、缺失/多余项报告、只读预检 | ~120 |
| `src/acme_lp/gui.py` | 单窗口：状态、安装、还原、日志框 | ~220 |
| `src/acme_lp/cli.py` | `status / install / restore / verify` 四个子命令 | ~120 |
| `data/mui-map.json` | 语言目录映射表 + 白名单 + 目标 build | 配置 |
| `tests/test_mapping.py` | 纯离线：映射表与真实目录一致性测试 | ~100 |

---

## 4. 分阶段计划

### P0 可行性验证（不写代码，纯手工）
1. 备份 `MEP Designer 30\uilanguage.dat` 与 `en\` 目录清单；
2. 新建 `MEP Designer 30\zh-CN\`，先只放 3 个核心文件：`MEPPluginUI.dll.mui`、`MEPElements.dll.mui`、`MEPAPI.dll.mui`；
3. 将 `uilanguage.dat` 改为 `zh-CN`；
4. 启动 MEP Designer 30，检查"设计 > MEP 工具"菜单与管道/风管设置对话框。

**验收**：MEP 工具面板出现中文；无启动报错、无乱码。若失败 → 立即还原并转 P3 备选路线。

### P1 全量资源迁移
1. 复制 `Archicad 30\zh-CN\*.mui`（85 个）到 `MEP Designer 30\zh-CN\`；
2. 逐个子目录比对 `Add-Ons\*\en` → `Add-Ons\*\zh-CN`（Hydronics、Ventilation、标准、本地、输入-输出等），按 AC30 侧已有的中文包移植；
3. 生成差异清单：MEP Designer 独有而 AC30 无中文资源的文件。

**验收**：主界面、MEP 模块、常用附加工具均为中文；差异清单留档。

### P2 安装器开发（本项目的"插件"本体）
1. 安装/还原双流程，安装前强制备份（含文件哈希与原始 `uilanguage.dat`）；
2. 版本闸门：`MEP Designer.exe` 非 `3001` 时拒绝执行；
3. 日志写入 `%LOCALAPPDATA%\ACMEPCHI\logs\`；
4. 卸载式还原：按 manifest 精确删除新增文件、恢复语言标识。

**验收**：连续"安装 → 还原 → 安装"三轮，文件树与初始状态逐字节一致（可用哈希清单比对）。

### P3 残留英文补齐（按需启动）
1. 导出 P1 差异清单中仍为英文的条目（主要是 MEP Designer 独有字符串、帮助文档、启动画面）；
2. 用 MUI 资源只读提取脚本生成待译词条表（`data/todo-strings.csv`）；
3. 人工/术语库翻译后回写为补丁 `.mui`，由安装器叠加；
4. 术语统一（管道、风管、桥架、设备、系统浏览器等），形成公司内部术语表。

**风险控制**：补丁文件单独版本号管理，升级 MEP Designer 后自动失效并提示重新生成。

### P4 可选：中文辅助 Add-On（不是汉化的必需项）
若后续需要中文命令面板 / 中文术语提示，再基于 **API Development Kit 30** 开发一个独立 Add-On（当前只有 DevKit 28，需先下载 30）。本阶段不阻塞主交付。

### P5 文档与交付
`readme.md`（中英双语：用途、模块、使用说明、回滚方法）、`debug_log_1.md`（按公司规范记录每次变更）、术语表随包分发。

---

## 5. 风险与对策

| 风险 | 影响 | 对策 |
|---|---|---|
| 升级到 R2 / 30.0.1 后资源不匹配 | 中文失效或界面异常 | 版本闸门 + 一键还原 + 升级后重取对应中文包 |
| 个别对话框仍为英文 | 体验不完整 | P3 差分补齐，按词条迭代 |
| Graphisoft EULA 限制修改安装文件 | 合规风险 | 仅公司内部单机使用、不对外分发；只搬运厂商自带资源，不反编译 |
| 文件写入 Program Files 需管理员 | 安装失败 | 安装器请求提权，失败时给出手动步骤 |
| 中文图库/帮助缺失 | 工具提示、帮助仍英文 | 引用 Archicad 30 中文图库包与中文帮助路径 |

---

## 6. 交付物

1. `ACMEPCHI.exe`（或 `python -m acme_lp.gui`）单文件工具 + 配置
2. 中文资源迁移包（由本机 Archicad 30 CHI 生成，不入 git 大文件，用脚本现取）
3. `readme.md`（双语）、`debug_log_1.md`、术语表 `data/glossary_zh.csv`
4. 回滚说明（3 步手工操作，防止工具损坏时无法恢复）

---

## 7. 待确认

1. 你的 MEP 工作流是**独立 MEP Designer 30**，还是**Archicad 30 内的 MEP 工具**？（后者当前已是中文，问题可能只是某个 Add-On 语言目录缺失）
2. 是否接受"资源移植 + 安装器"路线（推荐），还是坚持要一个 Add-On 形态的插件？
3. 中文术语是否沿用 Graphisoft 官方译法（管道/风管/桥架），还是用公司习惯叫法。
