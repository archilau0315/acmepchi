# debug_log_1.md — ACMEPCHI 变更记录

> 记录规则：每次代码/配置改动追加一条，时间按 Asia/Shanghai。

| # | 时间 | 模块 | 变更简述 | 备注 |
|---|---|---|---|---|
| 1 | 2026-11-19 13:10 | docs | 新增《开发计划_MEP汉化.md》 | 基于本机实测：Archicad 30 为 CHI 中文版，独立 MEP Designer 30 为 INT 英文版；两者 build 3001，核心 DLL SHA256 一致，中文 `.mui` 文件名 1:1 对应 |
| 2 | 2026-11-19 13:19 | P0 备份 | 备份 `MEP Designer 30\en\` 全部 85 个 `.mui` 与 `uilanguage.dat` | 备份路径 `%LOCALAPPDATA%\ACMEPCHI\backup\p0-20261119-131929` |
| 3 | 2026-11-19 13:20 | P0 试验 A | 新建 `zh-CN\` 放 3 个核心 `.mui`，`uilanguage.dat` 改 `zh-CN` | 进程启动后自行退出；经 A/B 对比 `en` 同样退出，判定为非常驻进程环境（沙箱/许可）导致，非资源问题；已删除 `zh-CN\` 目录，`uilanguage.dat` 还原为 `en` |
| 4 | 2026-11-19 13:26 | P0 试验 B | 改用"原地替换"：将 `Archicad 30\zh-CN\` 的 `MEPPluginUI/MEPElements/MEPAPI.dll.mui` 覆盖到 `MEP Designer 30\en\` | 保持 `uilanguage.dat=en`，绕开语言白名单校验；待人工启动确认后再全量 85 个 |
| 5 | 2026-11-19 13:35 | 诊断 | 用户启动弹出 `No license found for MEP Designer` | 独立版为单独授权产品；仅能进演示模式，与汉化无关 |
| 6 | 2026-11-19 13:44 | 诊断 | 用户反馈启动出现 GRAPHISOFT Bug Reporter 崩溃 | 崩溃前已加载图库解压（`LCFUnZip`）与 `3D` 目录；WER 与事件日志无记录 |
| 7 | 2026-11-19 13:52 | 回滚 | 从备份还原 `en\MEPPluginUI/MEPElements/MEPAPI.dll.mui` | 三个文件 SHA256 与备份一致，恢复到英文原版，用于 A/B 定位崩溃原因 |
| 8 | 2026-11-19 14:05 | 新增 | 创建工具骨架：`paths/backup/verify/installer/cli/gui`、`data/mui-map.json`、`tests/test_mapping.py`、`bin/acmepchi.bat`、双语 `readme.md` | 修复两处 bug：配置根目录定位（`parents[2]`）、注册表键名拼装；`cli status` 输出 85 个待复制，单元测试 3/3 通过 |
| 9 | 2026-11-19 13:58 | 全量安装 | 还原基线后执行 `install`，85 个中文 `.mui` 覆盖 `MEP Designer 30\en\`，`status` 显示待复制 0 / 已相同 85 | 首次安装因 MEP Designer 运行中占用文件报 `PermissionError`，强制关闭后成功；已补"程序运行中拒绝安装/还原"闸门，备份 `backup\20261119-135821` |
| 10 | 2026-11-19 14:39 | 新增 | 新建 `src/acme_lp/we_i18n.py`：按菜单 GUID 从 Archicad 中文版工作环境 XML 取官方译法，原位替换 MEP 的 `Command Layouts\*.xml` 中 `title`，新增 CLI `menu` / `menu-restore`（支持 `--dry-run`） | 实测替换 154 处、可译 171 条；备份 `backup\we-20261119-143918`；验证启动 35 秒稳定 |
| 11 | 2026-11-19 14:41 | 试验 | `en\ProductResourceProvider.dll.mui` 换成 Archicad 中文版，启动 30 秒稳定（产品级菜单文案来源） | 单文件替换未触发崩溃，待用户目视确认菜单栏是否变中文；原文件已备份可还原 |
| 12 | 2026-11-19 15:57 | 新增 | 新建 `dictbuild.py`（MUI 英中词典，缓存 `data/mui_dict.json`）、`wepatch.py`（工作环境 XML + 命令布局 bin 汉化）、`data/mep_terms.json`（35 条手工词表）；CLI 增加 `we` / `we-restore`，`install` 末尾自动调用 `we` | 词典 9428 条；XML 命中 11 处（`MEP Engineering Tools.xml` 分组名 8 + `Standard Commands.xml` 标题 3）；补入词表后 bin 命中 25 处；每次写文件前备份到 `%LOCALAPPDATA%\ACMEPCHI\backup\we-<时间戳>\` |
| 13 | 2026-11-19 15:59 | 验证 | 实际执行 `we` 后启动 MEP Designer 观察 20 秒（10/10 次采样存活，Responding=True）后结束进程；重跑 dry-run 命中 0（幂等）；`we-restore` 回溯还原 XML 与 bin 正常；单元测试 3/3 通过 | 原始 bin 备份（`.bak`）上算法命中 126 处且文件长度不变；程序运行中执行 `we` 会直接报错退出，不强杀进程 |
| 14 | 2026-11-19 16:26 | 扩展 | `wepatch.py` 扫描范围从单个 `Command Layouts\*.bin` 扩展为 6 类目录（Command Layouts / Tools / Workspaces / Latest Workplaces / 最近的工作环境\工具 / 最近的工作环境\工作空间）；新增「整条记录」判定（文本前紧邻 `01 00 + 字符数` 记录头即视为完整标签），修复 `Connect` 等尾部紧邻非 ASCII 字节的标签被漏译；新增 `set_readonly()` 用 Win32 属性接口清除/恢复只读（`os.chmod` 在被程序刚关闭的文件上偶发无效）；`--fix-length` 可选改写长度字段 | 命中：`Standard Commands 30.bin` 7 + `MEP Engineering Tools 30.bin` 8 + `工具.bin` 8；词表补 `&Ducts/&Pipes/&Electrical/&Connect/&General/&Architectural/&Grid System` 与 `Grids→网格`（共 43 条）；文件长度均保持不变 |
| 15 | 2026-11-19 16:31 | 验证 | 实际写入后启动 MEP Designer 20 秒（10/10 次采样存活，Responding=True），正常关闭后复查中文仍在；`we-restore` 回溯还原 5 个文件（2 XML + 3 bin）正常，只读属性恢复；单元测试 3/3 通过 | 长度策略实际采用「保持原长度字段 + U+FFFF 补齐」；备选「改写为中文字符数」经内存对比验证（长度字段 10→2、文件长度不变）；bin 内不存在独立 `Document` 标签（仅 `Documenting/Documentation/Documents`），菜单栏 Document 文案来自 MUI/命令注册表 |
| 16 | 2026-11-19 17:00 | 修复 | 词表新增 `Do&cument → 文档(&N)`、`Stori&es → 楼层(&E)`；`we` 实际写入 Standard Commands 30.bin 2 处，文件长度 88926 不变 | 根因：英文菜单把快捷键字母放在词中（`Do&cument`），旧词表仅有 `Document` 故一直漏译；菜单栏 Document 与视图菜单 Stories 均取自同一 bin 快照，非 MUI 资源；备份 `%LOCALAPPDATA%\ACMEPCHI\backup\we-20261119-170036` |
| 17 | 2026-11-19 17:10 | 结构调整 | 仓库改为多版本布局：v30 全部代码迁入 `acmepchi30\`（src/bin/data/tests/docs/readme/本日志），新建 `acmepchi29\` 待开发；根目录新增双语总 readme，`.gitignore` 的 `mui_dict.json` 改为通配 | `paths.PACKAGE_ROOT` 用 `parents[2]` 定位，迁移后仍命中 `acmepchi30\data\mui-map.json`；`bin\acmepchi.bat` 的 `%~dp0..\src` 无需改动；实测 `cli status` 与 3 项单元测试通过；已移除误提交的 `tests\__pycache__\*.pyc` |
