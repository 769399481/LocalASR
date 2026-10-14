# Phase 15 — Final Release Checklist

日期：2026-10-14。目标：LocalASR 0.1.0 Release Candidate。此文件不是发布公告。

Repository：https://github.com/769399481/LocalASR

Git remote / clone：https://github.com/769399481/LocalASR.git

| 项目 | 状态 | 证据 / 范围 |
| --- | --- | --- |
| Version / Product | PASS | src/app_version.py：LocalASR / 0.1.0；About、Diagnostics、构建共享版本 |
| GitHub URL | PASS | README、Security、About、Installer 三个语义正确链接已统一；.git 仅 clone / remote |
| LICENSE | PASS | 与 Phase 14 官方原文逐字节哈希一致，未修改 |
| Source-available | PASS | 当前 README / Notes 定位一致；旧阶段记录明确标注历史 |
| Commercial / Security contact | PASS | yehao769399481@gmail.com，无价格或合同新增 |
| README / Release Notes | PASS | 已完成，明确 RC / 尚未上线 |
| Installer / size / SHA256 | PASS | 有意重建；1,303,059,102 bytes；D148B3ADF46660E1EC878AB7DE6D7AA01A54DDEF01AEFEA7D861D87B75AB2836；独立复算匹配 |
| Signing / SmartScreen | PASS | 明确 UNSIGNED / Unknown Publisher 可能提示，不绕过保护 |
| Install / Start Menu / uninstall | PASS | Phase 15 rerun；实际 .lnk 启动，安装/卸载均退出码 0，数据保留，最终已卸载 |
| File ASR / Translation / Export | PASS | Phase 15 rerun；真实短音频、中文翻译、双语 DOCX、五种导出 |
| System Audio / Overlay | PASS | Phase 15 rerun；9 英文/9 中文，音频/翻译零丢弃；实际看到双语悬浮字幕 |
| Model discovery / Diagnostics | PASS | Phase 15 rerun；三模型 installed=true，LocalASR 0.1.0，无私人路径/转录 |
| Tests | PASS | Phase 15：280 tests，51.138 秒，全部通过 |
| Third-party notices | PARTIAL | 所需组件列齐且不重新授权；LEGAL REVIEW RECOMMENDED，不是法律确认 |
| Source privacy | PASS | 最终候选清单与模式扫描未发现秘密/真实私人路径；忽略规则覆盖私有数据与构建产物 |
| Git state / remote | PASS | 根目录未 git init，无远端；未初始化、提交、push 或创建 tag |
| Known limitations | PASS | Notes 明确签名、Upgrade、硬件、protected audio、macOS 限制 |
| Cross-version Upgrade | PARTIAL | 无真实旧 Installer，同版重装不等于跨版升级 |
| Release blockers / recommendation | PASS | 当前验证范围未发现真正 blocker；READY FOR RELEASE（工程封板，非法律保证） |

详细最终数值与证据来源见 PHASE15.md。历史 Phase 14 哈希只标识旧包，不适用于本次重建包。

最终状态：**Phase 15 COMPLETE WITH KNOWN VALIDATION LIMITATIONS**。完整制品列表见 [PHASE15_ARTIFACTS](PHASE15_ARTIFACTS.md)，最终报告见 [PHASE15](PHASE15.md)。

PENDING 仅为明确禁止执行的正式发布动作；尚未 push、上传、创建 tag 或 GitHub Release。UNSIGNED、Upgrade PARTIAL 等已披露限制不按本次标准自动列为 blocker。

