# Phase 15.1 — Bilingual README & Developer Setup Documentation

日期：2026-10-14。状态：**COMPLETE**。最终 Verdict：**READY FOR PHASE 16**，仅表示可以由用户另行指定下一阶段；本次不进入 Phase 16。

| # | 检查 | 结果 |
| --- | --- | --- |
| 1 | Phase 15.1 | COMPLETE，文档范围完成 |
| 2 | README.md | 完整简体中文，普通用户优先，开发者章节自包含 |
| 3 | README_EN.md | 完整对应英文版，不是摘要 |
| 4 | 语言切换 | 顶部互链正确，本地链接检查通过 |
| 5 | 旧开发文档 | docs/DEVELOPMENT.md 存在；DEVELOPMENT_EN.md 不存在 |
| 6 | 迁移处理 | 有效内容整合入两份 README；原中文开发文档只保留简短双语迁移入口。构建代码错误提示仍引用该文件，因此不删除、不改产品代码；贡献指南和历史报告当前指引已更新 |
| 7 | 中文普通用户说明 | 功能、下载/安装/卸载、要求、文件/实时/悬浮字幕、格式、模型、隐私、限制齐全 |
| 8 | 英文普通用户说明 | 与中文对应，保留未发布措辞与真实验证边界 |
| 9 | 开发者说明 | 环境、依赖、源码入口、CLI、模型、数据、测试、两层构建、checksum、目录树、排错均直接在 README |
| 10 | Conda | conda create -n asr python=3.11；conda activate asr；实际 Python 3.11.15，无强制补丁锁定 |
| 11 | Dependencies | 实际 requirements.txt / requirements-realtime.txt / requirements-translation.txt；构建另用 requirements-build.txt，未引用不存在文件 |
| 12 | PyTorch / CUDA | 实际 torch 2.6.0+cu124；requirements 仅固定 2.6.0，不保证 CUDA wheel；明确 CTranslate2 runtime、驱动、CPU fallback 及 optimized 构建的额外要求 |
| 13 | Models | large-v3、small、Helsinki-NLP/opus-mt-en-zh + OpenCC；按需下载、固定 revision/完整性校验、源/安装版路径与旧路径兼容范围正确 |
| 14 | Source-run command | conda run -n asr --no-capture-output python src/gui.py |
| 15 | Source run | **PASS**；实际 asr Python GUI 窗口与准备页面显示，无立即异常，正常关闭，退出码 0；仅使用独立验证数据目录，不做转录/实时测试 |
| 16 | Full test command | conda run -n asr --no-capture-output python -m unittest discover -s tests -v |
| 17 | Test command verification | **PASS**；同一 unittest discovery 使用 -p test_subtitle_export.py；19 tests，1.951 秒，OK，退出码 0。明确不是本次全量 280 项 |
| 18 | Standalone build | build.ps1 / distribution/build.py / LocalASR.spec、CPU wheel 暂存、runtime、覆盖目录和输出路径完整；引用 Phase 15 实际构建，不重建 |
| 19 | Installer build | Inno Setup 6.7.3、实际 .iss / build_installer.ps1；明确先 standalone，参数指定新输出目录，脚本不自动运行 PyInstaller |
| 20 | SHA256 | PowerShell 单文件校验和已有 checksums.ps1 helper；标注只适用于最终 RC |
| 21 | Structure | 根据实际 src/tests/distribution/docs/.github/build.ps1/requirements/README/LICENSE 整理；说明忽略的本地数据不随 clone 提供 |
| 22 | Troubleshooting | CUDA、模型、麦克风、系统音频、翻译模型、Inno、PyInstaller 七类问题 |
| 23 | 双语一致性 | 功能、限制、版本、模型、依赖、许可和联系方式对应；22 条 PowerShell 命令（忽略注释）完全一致 |
| 24 | GitHub URL | https://github.com/769399481/LocalASR；clone 使用 .git，无占位地址 |
| 25 | License | PolyForm Noncommercial License 1.0.0；官方 LICENSE 原文未修改 |
| 26 | Commercial | 商业用途需单独许可；yehao769399481@gmail.com；未增加价格或合同 |
| 27 | Security | yehao769399481@gmail.com，链接 SECURITY.md |
| 28 | 产品代码 | 未修改；60 个源/构建/安装器相关文件前后哈希一致 |
| 29 | Installer | 未修改、未重建、未安装；最终 1,303,059,102 bytes，SHA256 与 Phase 15 相同 |
| 30 | 完整测试 | 未重跑；只做文档要求的源 GUI 和 19 项测试命令验证。280 项是 Phase 15 已验证 baseline |
| 31 | 文档限制 | 没有全新 Conda 环境重新安装；GPU 配置仍受硬件/驱动/runtime影响；不是完整传递依赖 lock；构建命令本次仅与实际脚本及 Phase 15 证据核对，不重新执行 |
| 32 | Phase 16 readiness | **READY FOR PHASE 16**；本次停止，不执行下一阶段 |

## 保持不变的 RC

`dist/release-phase15/LocalASR-Setup-0.1.0-win64.exe`

大小：**1,303,059,102 bytes**。

SHA256：`D148B3ADF46660E1EC878AB7DE6D7AA01A54DDEF01AEFEA7D861D87B75AB2836`。

只读比对用于确认文档工作未改动制品，不是重做 Phase 15 Release Validation。未安装、卸载或重装软件，未跑 ASR / Translation / System Audio / Overlay smoke。

本次改动仅为 README.md、README_EN.md、开发指南迁移页、CONTRIBUTING 链接、历史报告顶部当前开发指引和本报告。历史事实段落保留，专门的架构/安装策略文档仍可作为扩展参考；普通开发流程不再依赖另一个 Developer Guide。

本地证据：validation/phase15_1/source-run.log、test-command.txt、product-before.json、unchanged.json、bilingual.json、links.json。原始本机路径不公开。源码启动使用 LOCALASR_DATA_DIR 隔离，不下载模型、不改变已卸载状态。

未 push、tag、上传、创建 Release 或正式发布。停止于 Phase 15.1。
