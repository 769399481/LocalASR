# Phase 13 Repository Cleanup Plan

扫描日期：2026-10-12。只整理版本控制边界和文档；不删除模型、用户数据、回退构建或唯一证据。当前目录尚未初始化 Git。

| 分类 | 路径 / 内容 | 处理 |
| --- | --- | --- |
| KEEP | src/、tests/、requirements*.txt | 保留；审查路径、隐私、依赖，不改变 Core |
| KEEP | build.ps1、distribution/*.py / *.ps1 / *.spec、hooks/ | 保留构建与验证入口；一次性迁移脚本另行归档 |
| KEEP | README、公共说明、GitHub 模板、docs/ | 面向用户 / 开发者分层，文档例子通用化 |
| ARCHIVE | PHASE7–12.6.md、旧 DEVELOPMENT.md、旧 README | 原件备份到被忽略的 archive/local-originals；公开脱敏历史副本移入 docs/development |
| ARCHIVE | distribution/phase12_edit.py、phase12_strings.py | 过期一次性源码迁移脚本，移入本地 archive/，不作为维护工具公开 |
| ARCHIVE | validation/（457 文件，42,324,585 字节） | 本地保留原始证据并整体忽略；docs/development/VALIDATION.md 保留有价值的脱敏摘要与证据索引 |
| REGENERATABLE | build/（1,245,350,449 字节）、dist/（19,383,674,729 字节） | 不删除；全部忽略，保留 Phase 10/11/12/12.5/12.6 回退版本 |
| REGENERATABLE | distribution/vendor/、third_party_licenses/ | 本地 wheel / runtime staging / 生成许可证清单，排除 Git；保留生成脚本 |
| REGENERATABLE | __pycache__、.pytest_cache、临时截图/音频/测试输出 | 忽略；不为释放磁盘做大规模删除 |
| REVIEW | models/（3,689,280,146 字节）、HF cache | 全部忽略；首次使用按需下载，不提交权重 |
| REVIEW | input/、output/、recovery/、logs/、gui_settings.json | 用户私有数据，原样保留且忽略；不公开转录、设备信息或日志 |
| REVIEW | tools/InnoSetup/、tools/innosetup-*.exe、distribution/installer.iss | 历史未启用工具；二进制忽略，安装脚本保留但不运行、不制作 Installer |
| REVIEW | 主项目 License、FFmpeg/NVIDIA 实际分发义务 | License 待用户选择；二进制发布前复核，不宣称已获法律许可 |
| DELETE | 根目录空文件 6.16 | 无内容、非源码；采用移入本地 archive 而非永久删除 |

## 执行边界

不初始化远端、不提交、不打 tag、不上传或创建 Release。不下载模型，不升级依赖。不重新构建整个应用。只对版本控制候选文本做敏感信息扫描；私有日志 / 模型目录通过忽略规则隔离。原件保留在本地忽略目录，公开历史报告会标明路径脱敏。历史证据引用按仓库根目录解释，并注明 clone 不附带原始验证数据。

整理后运行 Conda asr 完整测试；检查构建引用、文档链接、忽略规则和公开候选清单。CI 本阶段只评估，不在未验证 Windows runner 环境上声称通过。

