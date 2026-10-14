# LocalASR 0.1.0

# 简体中文

LocalASR 0.1.0 是 LocalASR 的首个公开发布版本。

LocalASR 是一款源码公开、本地运行的 Windows 语音识别与实时翻译工具。

## 主要功能

- 音频 / 视频文件转录及多文件批量处理。
- 支持英文、中文或自动语言识别。
- 麦克风实时英文识别。
- Windows 系统音频实时识别。
- 英文 → 简体中文本地翻译，并保留英文原文。
- 英文、中文、双语悬浮字幕。
- 实时会话保存、恢复与导出。
- TXT / DOCX / JSON / SRT / VTT 输出。
- 自动硬件检测和模型管理。
- 语音识别和默认翻译均在本地运行。
- Windows 每用户安装，不需要管理员权限。

## 下载

请从 GitHub Releases 下载 Windows 安装包：

https://github.com/769399481/LocalASR/releases

官方 Windows Installer：

```text
LocalASR-Setup-0.1.0-win64.exe
```

文件大小：

```text
1,303,059,102 bytes
```

SHA256：

```text
D148B3ADF46660E1EC878AB7DE6D7AA01A54DDEF01AEFEA7D861D87B75AB2836
```

Release 同时提供：

```text
SHA256SUMS.txt
```

可以使用 PowerShell 核对安装包：

```powershell
Get-FileHash .\LocalASR-Setup-0.1.0-win64.exe -Algorithm SHA256
```

结果应与上面的 SHA256 一致。

## 安装

1. 下载 `LocalASR-Setup-0.1.0-win64.exe`。
2. 可使用 `SHA256SUMS.txt` 核对文件完整性。
3. 运行 Installer。
4. 阅读许可证。
5. 选择安装目录及可选桌面快捷方式。
6. 从 Windows 开始菜单或桌面快捷方式启动 LocalASR。
7. 首次使用时，根据需要下载语音识别和翻译模型。

默认安装目录：

```text
%LOCALAPPDATA%\Programs\LocalASR
```

安装不需要管理员权限。

普通用户无需安装：

- Python
- Conda
- CUDA Toolkit
- 开发命令行环境

NVIDIA 显卡驱动仍由 Windows 或显卡厂商提供。

## 文件转录

支持单文件及批量处理。

输入格式：

- MP3
- WAV
- M4A
- FLAC
- AAC
- OGG
- MP4

识别语言：

- 英文
- 中文
- 自动识别

输出格式：

- TXT
- DOCX
- JSON
- SRT
- VTT

字幕文件使用真实 segment 时间戳。

## 实时识别

支持：

- 麦克风输入
- Windows 系统音频

实时识别过程中：

- 英文 partial 会持续更新。
- 已确认的 final 会保存到当前会话。
- 开启翻译后，final 会进行中文翻译。
- 停止识别后可以导出当前会话。

## 本地翻译

当前翻译方向：

```text
English → 简体中文
```

翻译在本地运行。

英文原文会被保留。

## 悬浮字幕

支持：

- English
- 中文
- 双语

可以调整字幕显示方式、位置、字号及透明度。

## 会话与恢复

实时识别会话可以保存和恢复。

停止识别后可以导出会话内容。

## 模型

模型不包含在 Installer 中，需要按需单独下载。

| 用途 | 模型 | 大致大小 |
| --- | --- | ---: |
| 高精度文件 ASR | large-v3 | 约 3.09 GB |
| 实时 ASR | small | 约 0.49 GB |
| 英文 → 简体中文 | Helsinki-NLP/opus-mt-en-zh + OpenCC | 约 0.32 GB |

首次下载模型需要网络连接。

模型准备完成后，主要识别和翻译流程可在本地运行，不需要将音频或转录内容上传到云端 ASR 服务。

已有兼容模型可以继续复用，不需要重复下载。

## 系统要求

目标平台：

```text
Windows 10 / Windows 11 x64
```

本版本主要在 Windows 11 上进行发布验证。

推荐：

- NVIDIA GPU
- 16 GB 内存或以上
- 足够的磁盘空间用于程序、模型、下载暂存和输出文件

没有兼容 NVIDIA GPU 时可以使用 CPU fallback，但转录速度可能明显降低。

已验证参考硬件：

```text
NVIDIA GeForce RTX 3060 Laptop GPU 6 GB
```

不保证所有 CPU / GPU 组合具有相同表现。

程序安装体积约 2.5 GB，不包含额外模型和用户数据。

当前不正式支持：

- Windows 7
- Windows ARM64
- macOS

## 隐私

LocalASR 以本地处理为主要设计方向。

默认情况下：

- 语音识别在本地运行。
- 翻译在本地运行。
- 音频不会因为识别而上传到云端。
- 转录正文不会因为识别而上传到云端。

模型下载需要联网。

日志可能包含本地文件路径。

会话恢复文件可能包含字幕或转录内容。

分享日志、恢复文件或输出前，请自行检查其中的信息。

详细说明：

[PRIVACY.md](PRIVACY.md)

## License 与商业授权

LocalASR 使用：

[PolyForm Noncommercial License 1.0.0](LICENSE)

项目定位：

**Source-available / 源码公开**

非商业使用应遵循许可证。

商业用途需要单独商业许可。

商业授权联系：

```text
yehao769399481@gmail.com
```

详细说明：

[COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)

第三方组件及模型分别遵循各自许可证。

详见：

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

第三方依赖、Native Runtime、模型及再分发义务应根据实际使用场景自行核查。

本项目不提供针对具体使用场景的法律意见。

## Security

安全问题请私密联系：

```text
yehao769399481@gmail.com
```

敏感安全漏洞请不要通过公开 GitHub Issue 报告。

详见：

[SECURITY.md](SECURITY.md)

## 已知限制

- Windows Installer 当前未进行 Authenticode 数字签名。
- Windows 可能显示 `Unknown Publisher`。
- Microsoft SmartScreen 可能显示安全提示。
- 跨版本升级尚未覆盖所有真实升级场景。
- 部分 CPU / GPU / 麦克风 / 耳机 / 蓝牙设备组合未完整验证。
- 实体多显示器及部分 DPI 组合未完整验证。
- 资源管理器跨窗口拖放未覆盖所有环境。
- 某些 DRM / Protected Audio 内容可能无法通过 Windows 系统音频捕获。
- ASR 可能产生识别错误。
- 机器翻译可能产生翻译错误。
- 重要内容应人工复核。
- 当前没有自动更新功能。
- 当前没有云端 ASR。
- macOS 当前不是正式发布平台。

不要为了运行 LocalASR 而关闭 Windows 系统安全防护。

## 卸载

关闭 LocalASR 后，可以通过：

```text
Windows 设置
→ 应用
→ 安装的应用
→ LocalASR
→ 卸载
```

也可以运行安装目录中的：

```text
unins000.exe
```

默认卸载会保留：

- 已下载模型
- 应用配置
- 会话恢复数据

默认用户数据目录：

```text
%LOCALAPPDATA%\LocalASR
```

确认不再需要这些数据后，可以手动删除该目录。

删除下载的 Installer 不等于卸载应用。

## 源码

GitHub Repository：

https://github.com/769399481/LocalASR

Issues：

https://github.com/769399481/LocalASR/issues

完整安装、使用、开发、测试和构建说明：

[README.md](README.md) · [README_EN.md](README_EN.md)

---

# English

LocalASR 0.1.0 is the first public release of LocalASR.

LocalASR is a source-available Windows speech recognition and real-time translation application that runs locally.

## Highlights

- Audio / video transcription with batch file processing.
- English, Chinese, and automatic language detection.
- Real-time English recognition from microphone input.
- Real-time recognition of Windows system audio.
- Local English → Simplified Chinese translation while preserving the original English text.
- English, Chinese, and bilingual floating subtitles.
- Real-time session saving, recovery, and export.
- TXT / DOCX / JSON / SRT / VTT output.
- Automatic hardware detection and model management.
- Speech recognition and default translation run locally.
- Per-user Windows installation without administrator privileges.

## Download

Download the Windows installer from GitHub Releases:

https://github.com/769399481/LocalASR/releases

Official Windows installer:

```text
LocalASR-Setup-0.1.0-win64.exe
```

File size:

```text
1,303,059,102 bytes
```

SHA256:

```text
D148B3ADF46660E1EC878AB7DE6D7AA01A54DDEF01AEFEA7D861D87B75AB2836
```

The release also includes:

```text
SHA256SUMS.txt
```

You can verify the installer with PowerShell:

```powershell
Get-FileHash .\LocalASR-Setup-0.1.0-win64.exe -Algorithm SHA256
```

The result should match the SHA256 shown above.

## Installation

1. Download `LocalASR-Setup-0.1.0-win64.exe`.
2. Optionally verify it using `SHA256SUMS.txt`.
3. Run the installer.
4. Review the license.
5. Choose the installation directory and optional desktop shortcut.
6. Start LocalASR from the Windows Start menu or desktop shortcut.
7. On first use, download the speech recognition and translation models you need.

Default installation directory:

```text
%LOCALAPPDATA%\Programs\LocalASR
```

Administrator privileges are not required.

Regular users do not need to install:

- Python
- Conda
- CUDA Toolkit
- Development command-line tools

NVIDIA GPU drivers are still provided by Windows or the GPU vendor.

## File Transcription

Single-file and batch processing are supported.

Input formats:

- MP3
- WAV
- M4A
- FLAC
- AAC
- OGG
- MP4

Recognition languages:

- English
- Chinese
- Automatic detection

Output formats:

- TXT
- DOCX
- JSON
- SRT
- VTT

Subtitle files use real segment timestamps.

## Real-Time Recognition

Supported input sources:

- Microphone
- Windows system audio

During real-time recognition:

- English partial results are updated continuously.
- Confirmed final results are stored in the current session.
- When translation is enabled, final results are translated into Chinese.
- The session can be exported after recognition is stopped.

## Local Translation

Current translation direction:

```text
English → Simplified Chinese
```

Translation runs locally.

The original English text is preserved.

## Floating Subtitles

Supported display modes:

- English
- Chinese
- Bilingual

Subtitle display, position, font size, and opacity can be adjusted.

## Sessions and Recovery

Real-time sessions can be saved and recovered.

Session contents can be exported after recognition is stopped.

## Models

Models are not bundled with the installer and are downloaded separately as needed.

| Purpose | Model | Approximate Size |
| --- | --- | ---: |
| High-accuracy file ASR | large-v3 | ~3.09 GB |
| Real-time ASR | small | ~0.49 GB |
| English → Simplified Chinese | Helsinki-NLP/opus-mt-en-zh + OpenCC | ~0.32 GB |

An internet connection is required for first-time model downloads.

Once the required models are available, the main recognition and translation workflows run locally without uploading audio or transcription content to a cloud ASR service.

Existing compatible models can be reused without downloading them again.

## System Requirements

Target platform:

```text
Windows 10 / Windows 11 x64
```

Release validation was primarily performed on Windows 11.

Recommended:

- NVIDIA GPU
- 16 GB RAM or more
- Sufficient disk space for the application, models, temporary downloads, and output

CPU fallback is available when no compatible NVIDIA GPU is present, but transcription may be significantly slower.

Validated reference hardware:

```text
NVIDIA GeForce RTX 3060 Laptop GPU 6 GB
```

Identical performance is not guaranteed across all CPU / GPU combinations.

The installed application is approximately 2.5 GB before additional models and user data.

Currently not officially supported:

- Windows 7
- Windows ARM64
- macOS

## Privacy

LocalASR is designed primarily for local processing.

By default:

- Speech recognition runs locally.
- Translation runs locally.
- Audio is not uploaded to the cloud for recognition.
- Transcription content is not uploaded to the cloud for recognition.

Model downloads require internet access.

Logs may contain local file paths.

Session recovery files may contain subtitle or transcription content.

Review logs, recovery files, or exported files before sharing them.

See:

[PRIVACY.md](PRIVACY.md)

## License and Commercial Licensing

LocalASR is licensed under:

[PolyForm Noncommercial License 1.0.0](LICENSE)

Project type:

**Source-available**

Noncommercial use must comply with the license.

Commercial use requires separate permission.

Commercial licensing:

```text
yehao769399481@gmail.com
```

See:

[COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)

Third-party components and models remain subject to their respective licenses.

See:

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

Users and redistributors should review third-party dependency, native runtime, model, and redistribution requirements for their own use case.

This project does not provide legal advice.

## Security

Security issues should be reported privately to:

```text
yehao769399481@gmail.com
```

Please do not report sensitive security vulnerabilities through public GitHub Issues.

See:

[SECURITY.md](SECURITY.md)

## Known Limitations

- The Windows installer is currently unsigned.
- Windows may display `Unknown Publisher`.
- Microsoft SmartScreen may display a warning.
- Cross-version upgrades have not been validated across every real-world version transition.
- Some CPU / GPU / microphone / headphone / Bluetooth device combinations have not been fully tested.
- Physical multi-monitor and some DPI configurations have not been fully tested.
- File Explorer cross-window drag-and-drop has not been validated in every environment.
- Some DRM / Protected Audio content may not be capturable through Windows system audio.
- ASR may produce recognition errors.
- Machine translation may produce translation errors.
- Important content should be reviewed manually.
- Automatic updates are not currently provided.
- Cloud ASR is not currently provided.
- macOS is not an official release platform.

Do not disable Windows security protections simply to run LocalASR.

## Uninstallation

After closing LocalASR, you can uninstall it through:

```text
Windows Settings
→ Apps
→ Installed apps
→ LocalASR
→ Uninstall
```

You can also run:

```text
unins000.exe
```

from the installation directory.

By default, uninstalling preserves:

- Downloaded models
- Application settings
- Session recovery data

Default user data directory:

```text
%LOCALAPPDATA%\LocalASR
```

Delete this directory manually only after confirming that you no longer need the stored data.

Deleting the downloaded installer does not uninstall the application.

## Source Code

GitHub Repository:

https://github.com/769399481/LocalASR

Issues:

https://github.com/769399481/LocalASR/issues

For complete installation, usage, development, testing, and build instructions, see:

[README.md](README.md) · [README_EN.md](README_EN.md)