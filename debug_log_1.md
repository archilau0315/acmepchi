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
