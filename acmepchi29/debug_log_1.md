# 变更记录 · MEP Designer 29 汉化工具

| # | 时间 | 模块 | 变更简述 | 备注 |
|---|---|---|---|---|
| 1 | 2026-11-19 17:30 | 目录 | 由 acmepchi30 复制出 acmepchi29，移除 30 版词典缓存与构建产物 | 目录独立自洽，各自打包 |
| 2 | 2026-11-19 17:32 | config/paths/wepatch | `mui-map.json` 改为 29 配置（`reg_major=29.`）；`paths` 版本前缀改为配置驱动；bin 扫描新增 `WorkEnvironment`、`Latest WorkEnvironment`（29 的英文目录名） | 29 用户目录结构与 30 不同，原路径大小写与命名都不匹配 |
| 3 | 2026-11-19 17:35 | dictbuild | 词典构建由「按字符串顺序配对」改为「按资源结构配对」（祖先 `#id` 路径 + 字段名），并过滤非 ASCII 源串 | 29 的 MEP 与 Archicad 构建号不同，旧算法配对错乱（出现 `Save→全部用户`）；新算法产出 12573 条，抽样正确 |
| 4 | 2026-11-19 17:40 | backup/installer | `latest_backup` 支持按语言目录名过滤；`restore` 只认含 `en` 的备份；修正传参取 `Path(...).name` | 修复「还原时误选工作环境备份、还原 0 个文件」的问题 |
| 5 | 2026-11-19 17:50 | installer/tests | 新增构建号一致性校验：MEP 与 Archicad 版本不同即报错拦截；测试改为验证该守卫；`target_build` 从配置移除 | 整批替换跨构建 MUI 后用 WMI 启动，15 秒内退出；已全部还原英文（diff=0） |
| 6 | 2026-11-19 17:55 | readme | 新增 29 版双语说明，记录当前状态与「先统一构建号再打包」的结论 | 待 MEP Designer 29 更新到 5003 后复测并打包 exe |
| 7 | 2026-11-19 18:20 | config/installer/gui | 改为工作环境汉化模式：`replace_mui=false`；`install`/`restore_latest` 走工作环境分支；GUI 提示改为「仅汉化工作环境」，结果展示 XML/bin 命中数；`wepatch` 增加 `summary` | 用户确认 MEP 29 已更新到 29.0.0.3200，并要求本项目一律按「MEP 与 Archicad 构建号不同步」处理 |
| 8 | 2026-11-19 18:24 | dictbuild | 英文源优先取当前安装的 `en`（仍是英文时），不再默认取历史备份；重建词典 12595 条 | 更新后旧备份是 3000 版英文，直接比对会错位 |
| 9 | 2026-11-19 18:28 | 实测 | 还原工作环境 → 重新汉化：XML 95 处、bin 3520 处；WMI 启动 MEP 29 后跨命令持续存活（35 秒以上），无 Bug Reporter；`we --dry-run` 剩余命中 0 | 跨构建整文件替换 MUI 实测 15 秒内退出，故明确不做 |
| 10 | 2026-11-19 18:35 | 打包 | PyInstaller 打出 `dist\ACMEPCHI-29.exe`（11.3 MB，onefile/windowed/uac-admin）；测试 3 项通过；实测 exe 启动后窗口标题「ACMEPCHI · MEP Designer 29 汉化 v0.1.0」 | 交付：用户按自己安装的版本选用 29 或 30 的 exe |
