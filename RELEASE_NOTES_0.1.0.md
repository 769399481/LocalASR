# LocalASR 0.1.0

**Release Candidate — 尚未正式发布。** Windows 源码公开、本地语音识别与实时翻译工具。

## Highlights

- 文件批量转录，支持英文、中文、自动识别。
- 麦克风实时英文识别与 Windows 系统音频实时识别。
- 英文 → 简体中文本地翻译，保留英文原文。
- 悬浮字幕、会话保存与恢复。
- TXT / DOCX / JSON / SRT / VTT 五种导出。
- ASR 与默认翻译本地运行，音频和转录默认不上传。
- 每用户 Windows Installer，无需管理员权限。

## Installation

正式发布后，从 [Releases](https://github.com/769399481/LocalASR/releases) 下载 `LocalASR-Setup-0.1.0-win64.exe`，核对随附 `SHA256SUMS.txt` 后安装。当前没有声称该文件已经在线。

[GitHub 项目](https://github.com/769399481/LocalASR) · [Issues](https://github.com/769399481/LocalASR/issues)

安装默认位于 `%LOCALAPPDATA%\Programs\LocalASR`。普通用户不需要 Python、Conda 或 CUDA Toolkit。卸载前先关闭应用；Windows 应用设置或 `unins000.exe` 可以卸载程序，**默认保留模型、配置和转录数据**。删除安装包不等于卸载应用。

## Models

模型不包含在 Installer 中，首次使用按需下载，需要网络及额外磁盘空间；已有模型可继续识别，不需要重复下载。文件高精度 large-v3 约 3.09 GB，实时 small 约 0.49 GB，Marian 英中翻译约 0.32 GB。模型准备好后可离线使用。

## Requirements

Windows 10 / 11 x64 为目标，实际安装验证基于 Windows 11。NVIDIA GPU 推荐，CPU fallback 可用但速度依设备而异。建议 16 GB 内存或以上；程序约 2.497 GB，还需要模型、暂存和输出空间。不承诺 Windows 7、ARM64 或所有 GPU。

## License

[PolyForm Noncommercial License 1.0.0](LICENSE)。LocalASR 为 **Source-available / 源码公开**。

非商业使用遵循许可证；任何商业用途需要单独商业许可。Commercial licensing：**yehao769399481@gmail.com**，见 [商业授权说明](COMMERCIAL_LICENSE.md)。第三方组件及模型分别遵循各自许可证，见 [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)。Native 分发义务：**LEGAL REVIEW RECOMMENDED**，不声称法律确认完毕。

## Security / Privacy

Security contact：**yehao769399481@gmail.com**，敏感漏洞请私密报告，见 [SECURITY](SECURITY.md)。诊断字段白名单不含转录正文或完整日志；音频和转录默认不上传。详见 [PRIVACY](PRIVACY.md)。

## Known Limitations

- Installer **UNSIGNED**，未进行 Authenticode 代码签名；Windows 可能显示 Unknown Publisher 或 SmartScreen 提示。
- Cross-version Upgrade validation = **PARTIAL**；只有同版覆盖和重装验证，没有真实旧 Installer 升级验证。
- 部分硬件组合、真人麦克风讲话、耳机、实体多显示器、部分物理 DPI 未完整验证。
- 资源管理器跨窗口拖放未完整验证；应用内部原生拖放已有验证。
- 某些 DRM / protected audio 或特殊音频路径可能无法系统回采。
- ASR / 翻译会出错，重要内容应人工复核。
- macOS 未正式支持，不是本次 Release 平台；无自动更新或云端 ASR。

## Validation / Checksums

本次实际检查范围、最终安装包大小、SHA256 和发布建议见 [Phase 15 Checklist](docs/development/PHASE15_RELEASE_CHECKLIST.md)。以最终包随附的 SHA256SUMS.txt 为准；旧 Phase 14 哈希只标识旧候选，不适用于重建后的 RC。

最终 RC 安装包：1,303,059,102 bytes；SHA256：
D148B3ADF46660E1EC878AB7DE6D7AA01A54DDEF01AEFEA7D861D87B75AB2836

[完整制品列表](docs/development/PHASE15_ARTIFACTS.md)。
