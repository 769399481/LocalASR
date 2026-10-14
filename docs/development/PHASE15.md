# Phase 15 — Final Release Check

日期：2026-10-14。**Phase 15 COMPLETE WITH KNOWN VALIDATION LIMITATIONS**。

工程封板建议：**READY FOR RELEASE**。尚未正式发布，未 push、上传、创建 tag、GitHub Release 或公告，未进入 Phase 16。该建议基于下述已验证范围，不等于全硬件保证或第三方许可法律确认。

## 产品、版本和许可

| 项目 | 最终值 |
| --- | --- |
| Product | LocalASR |
| Final version | 0.1.0；未 bump |
| Candidate | LocalASR 0.1.0 Release Candidate |
| Positioning | Source-available / 源码公开；Windows 本地语音识别与实时翻译工具 |
| Repository | https://github.com/769399481/LocalASR |
| Git remote / clone URL | https://github.com/769399481/LocalASR.git，仅用于 Git 语义 |
| License | PolyForm Noncommercial License 1.0.0，官方正文未修改 |
| Commercial policy | 非商业使用遵循许可证；任何商业用途需单独商业许可 |
| Commercial contact | yehao769399481@gmail.com |
| Security contact | yehao769399481@gmail.com |
| README | 完成，面向普通用户，说明安装、卸载、模型、隐私、要求与限制，明确尚未上线 |
| Release Notes | RELEASE_NOTES_0.1.0.md 已完成 |

LICENSE SHA256 与 Phase 14 保存的官方文件一致：C0EA4A896D2C8C394B29F9427589996DB826CD501C512279FF0ED3EF48FABBE5。未向许可正文追加商业条款。README、About、Security、开发说明和 Installer 的网页链接统一使用无 .git 的正式 URL；历史阶段记录加当前信息说明，保留当时事实。

About 实际显示 LocalASR 0.1.0 与正式 GitHub 地址；Diagnostics、版本源、载荷 ProductVersion、Installer、Windows Add/Remove Programs、Notes、文件名均为 0.1.0。模板版本占位符及依赖/许可证版本不当作应用版本改写。

## 最终 Installer

| 项目 | 结果 |
| --- | --- |
| 文件名 | LocalASR-Setup-0.1.0-win64.exe |
| 最终本地路径（相对仓库） | dist/release-phase15/LocalASR-Setup-0.1.0-win64.exe |
| Size | **1,303,059,102 bytes**，1.303059102 GB |
| SHA256 | **D148B3ADF46660E1EC878AB7DE6D7AA01A54DDEF01AEFEA7D861D87B75AB2836** |
| Signing | **UNSIGNED / NotSigned** |
| Metadata rebuild | **是**，About 与 Inno 项目/支持/更新 URL 更新；随包公开说明同步 |
| Compiler | Inno Setup 6.7.3，238.834 秒，成功 |
| Standalone | dist/LocalASR-Phase15，2,496,925,778 字节，6,365 文件 |

先重新计算 Phase 14 原包，确认 1,303,219,736 bytes 与 48A0C9D3C09E3648DFC6BF7E0CF5F970E0B02C5D9ED2E5504AF9C36B1009EE99 完全一致，再进行有意重建。旧包保留在 dist/release-final，不使用旧 hash 标识新 RC。新文件已再次独立计算并匹配 SHA256SUMS.txt，大小比旧 Installer 少 160,634 字节。

载荷差异已解释：既有、未修改的同源 DLL 去重规则去掉 358,912 字节的根层 asmjit.dll 副本，保留 torch/lib/asmjit.dll；三个新旧文件哈希相同。EXE 增加 13 字节，载荷净减 358,899 字节。实际安装版 Translation 已验证加载 torch/lib/asmjit.dll。本阶段没有增加瘦身规则、native 压缩、依赖升级或业务功能。

安装信息实际核对 AppPublisherURL=项目主页、AppSupportURL=/issues、AppUpdatesURL=/releases；固定 AppId 不变。真实普通用户安装，无管理员权限、不需重启。当前 Windows 可能显示 Unknown Publisher / SmartScreen 提示，未做公网下载信誉测试，不建议绕过或禁用安全防护。

## 一轮最终安装版短测

所有本轮运行均使用真正安装目录中的 LocalASR.exe，不用 Conda GUI 替代。模型与 11 秒合成英文测试音频复用现有本地资源，无下载。

| 检查 | Phase 15 rerun 结果 |
| --- | --- |
| Installer install | PASS；退出码 0，130.423 秒；日志显示新建应用目录及卸载记录 |
| Start Menu launch | PASS；通过 Windows Shell 启动实际开始菜单 .lnk，人工看到 GUI；不是声称人工点击 Start 菜单 |
| About | PASS；实际界面版本、许可、邮箱、正式 GitHub URL |
| File ASR | PASS；large-v3 GPU，真实短音频，completion_valid=true |
| English → Chinese | PASS；本地 Marian CPU + OpenCC，file_translation_complete=true |
| 双语 DOCX | PASS；bilingual_docx=true |
| Export | PASS；文件和实时会话 TXT/DOCX/JSON/SRT/VTT 均生成 |
| System Audio | PASS；实际 Windows 播放/回采，9 条英文 final、9 条中文，audio drop=0、translation drop=0 |
| Overlay | PASS（短 smoke）；computer-use 实际看到英文与中文悬浮字幕；未重复完整控件/DPI验收 |
| Model discovery | PASS；small、large-v3、opus-mt-en-zh 均 installed=true |
| Diagnostics | PASS；app=LocalASR、version=0.1.0；字段白名单无开发机目录、Conda/Python 开发路径或 transcript |
| Microphone | PARTIAL；本轮也实际采集帧并两次启停；真人讲话识别仍未验证 |
| 正常退出 | PASS；core/system 均退出码 0、无残留进程 |
| Uninstall | PASS；退出码 0，7.593 秒；应用目录、开始菜单和 HKCU 程序条目删除 |
| 用户数据保留 | PASS；真实配置哈希不变；models/output/recovery/logs/cache 哨兵一致 |

文件 Core 短测 63.433 秒；系统音频采集目标 45 秒。音频不上传，测试完整文本与本机路径只留在忽略的 validation 中。Diagnostics 的硬件型号是明确允许字段，不含不必要的私人配置或原始异常。

**最终机器状态：应用已卸载，没有再装回去；模型、设置、输出、恢复及日志保留。** 安装包及回退文件仍在本地。

明确复用的 **Phase 14 verified**：官方 License 页面实际展示、运行中安装退出码 7、运行中卸载保护提示及退出码 1、同版重装与数据保留、之前 6,366 文件旧载荷哈希验证。这些不冒充 Phase 15 重新执行，也不把旧载荷哈希比对声称为新载荷比对。本轮新包的安装、核心短测、About、诊断、模型、系统音频/Overlay、导出、卸载均为 Phase 15 rerun。

## 自动测试、第三方与源码隐私

完整 Conda asr 测试：**280 tests，51.138 秒，全部通过**。没有弱化线程、stop、export、ASR、translation、session、recovery 等核心断言。之后仅文档/验证记录更新，无应用代码变更。

THIRD_PARTY_NOTICES 已检查覆盖 faster-whisper、CTranslate2、PyTorch、Transformers、Helsinki/Marian、OpenCC、tkinterdnd2、WebRTC VAD、sounddevice、PortAudio、python-docx、PyInstaller、Inno Setup、CUDA，以及其他已记录组件。第三方保留各自许可，未套用 PolyForm。**LEGAL REVIEW RECOMMENDED**：实际 FFmpeg/PyAV、NVIDIA、Microsoft runtime 等 native 再分发与对应源码/通知义务仍应复核；未作法律确认或保证。

源码候选沿用既有隔离 Git ignore probe 进行最终清单和模式扫描，没有重新做 Repository Cleanup。排除 models、dist、Installer、build、日志、音频、转录、配置、cache、recovery、validation 和本机工具；.gitignore 实际匹配检查通过。未发现密钥/令牌/私钥或真实个人开发路径。允许的路径示例为测试合成 example/test 数据；公开联系邮箱为用户指定。Phase 14 报告的一处开发机路径及个人配置指纹已脱敏。

根目录 **未 git init**，无 staged/committed 文件、无已配置 remote；不能称为“干净 Git 工作树”。最终候选清单见本地 validation/phase15/public-files.txt，扫描统计见 source-audit.json；模式扫描不保证未来修改绝无秘密，首次提交仍应看 staged diff。未配置 remote、未提交或 push。

## Known limitations / PARTIAL / PENDING / Blockers

**PARTIAL**：跨版本 Upgrade（没有真实旧 Installer）；native 第三方许可法律复核；真人麦克风内容、耳机、实体多显示器、部分物理 DPI、Explorer 跨窗口拖放、全部硬件/干净 Windows 10 验证。Overlay 本轮只覆盖真实双语显示 smoke，不扩展成全部视觉操作通过。

**已披露非 blocker**：未签名及 SmartScreen 可能提示，Upgrade PARTIAL，部分硬件未测，macOS 未正式支持，DRM/受保护或特殊音频路径限制。没有发现已确认的许可证缺失、秘密泄露、安装/启动失败、核心功能破坏、数据丢失、无法解释哈希或开发机路径依赖等真正 blocker。

**PENDING（发布动作，不是本阶段遗漏）**：用户决定实际发布时机、Git 初始化/remote/提交、push、tag、上传及 GitHub Release；本阶段禁止执行。签名证书与法律专业复核为后续所有者决定，不伪造完成。

**Release blockers：当前已执行范围内未发现。Recommendation：READY FOR RELEASE。** 这是工程 RC 封板建议，保留上述限制，不是法律审查完成或自动发布授权。

## 清单、制品与修改范围

- [Final Release Checklist](PHASE15_RELEASE_CHECKLIST.md)
- [Release Artifact List](PHASE15_ARTIFACTS.md)
- RELEASE_NOTES_0.1.0.md、LICENSE、COMMERCIAL_LICENSE.md、SECURITY.md 已同步到本地 release-phase15 目录；SHA256SUMS.txt 标识最终 EXE。
- 主要修改：README、Security、Commercial、开发/安装说明、Release Notes/模板、Phase 15 三份报告、历史报告当前信息注记；src/ui_strings.py 的 GitHub 文案；distribution/build.py 的独立 --phase15 目标；Inno 三个 URL 字段。未重构 Installer 或 UI。
- 原始证据：validation/phase15 下 baseline、final-artifact、version-check、arp、install/uninstall、installed-core、installed-system、diagnostics-final、manual-startup、overlay-manual、regression、source-audit、notices-review。私人日志不加入源码候选。

Phase 15 完成后停止。没有上传、push、tag、GitHub Release、公告、Phase 16 或新业务功能。
