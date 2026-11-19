# debug_log_1.md — ACMEPCHI 变更记录

> 记录规则：每次代码/配置改动追加一条，时间按 Asia/Shanghai。

| # | 时间 | 模块 | 变更简述 | 备注 |
|---|---|---|---|---|
| 1 | 2026-11-19 13:10 | docs | 新增《开发计划_MEP汉化.md》 | 基于本机实测：Archicad 30 为 CHI 中文版，独立 MEP Designer 30 为 INT 英文版；两者 build 3001，核心 DLL SHA256 一致，中文 `.mui` 文件名 1:1 对应 |
| 2 | 2026-11-19 13:19 | P0 备份 | 备份 `MEP Designer 30\en\` 全部 85 个 `.mui` 与 `uilanguage.dat` | 备份路径 `%LOCALAPPDATA%\ACMEPCHI\backup\p0-20261119-131929` |
| 3 | 2026-11-19 13:20 | P0 试验 A | 新建 `zh-CN\` 放 3 个核心 `.mui`，`uilanguage.dat` 改 `zh-CN` | 进程启动后自行退出；经 A/B 对比 `en` 同样退出，判定为非常驻进程环境（沙箱/许可）导致，非资源问题；已删除 `zh-CN\` 目录，`uilanguage.dat` 还原为 `en` |
| 4 | 2026-11-19 13:26 | P0 试验 B | 改用"原地替换"：将 `Archicad 30\zh-CN\` 的 `MEPPluginUI/MEPElements/MEPAPI.dll.mui` 覆盖到 `MEP Designer 30\en\` | 保持 `uilanguage.dat=en`，绕开语言白名单校验；待人工启动确认后再全量 85 个 |
