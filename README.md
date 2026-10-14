# LocalASR

简体中文 | [English](README_EN.md)

**LocalASR 是一款源码公开、本地运行的 Windows 语音识别与实时翻译工具。** 项目定位：**Source-available**。

当前版本为 **0.1.0 Release Candidate**，已完成 Phase 15 封板，尚未正式发布。

[项目主页](https://github.com/769399481/LocalASR) · [Issues](https://github.com/769399481/LocalASR/issues) · [Releases](https://github.com/769399481/LocalASR/releases)

## 功能特点

- 音频 / 视频文件转录、多文件批量处理，英文、中文或自动识别。
- 麦克风实时英文字幕和 Windows 系统音频实时字幕。
- 英文 → 简体中文本地翻译，保留英文原文。
- 英文、中文、双语悬浮字幕；会话恢复与导出。
- TXT / DOCX / JSON / SRT / VTT 输出。
- 自动硬件检测、模型按需下载、本地优先处理。

## 下载与安装

**正式发布后**，可从 [GitHub Releases](https://github.com/769399481/LocalASR/releases) 下载；当前不表示文件已经上线。

1. 下载 `LocalASR-Setup-0.1.0-win64.exe`，核对随附 `SHA256SUMS.txt`。
2. 运行 Installer，阅读许可证并选择安装目录及可选桌面快捷方式。
3. 从开始菜单启动 LocalASR。
4. 首次使用时按提示下载需要的语音和翻译模型。

普通用户无需 Python、Conda、CUDA Toolkit 或命令行。显卡驱动仍由系统 / 厂商提供。默认每用户安装到 `%LOCALAPPDATA%\Programs\LocalASR`，不需要管理员权限。

退出任务并关闭应用后，可在 Windows「设置 → 应用 → 安装的应用」卸载，或运行安装目录的 `unins000.exe`。**卸载默认保留用户数据及模型**；确认不需要后才手动删除 `%LOCALAPPDATA%\LocalASR`。另选目录的输出需要自行管理。删除下载的安装包不会卸载应用。

## 系统要求

- Windows 10 / 11 x64 为目标；实际安装验证基于 Windows 11。
- NVIDIA GPU 推荐；CPU fallback 可用，但文件转录明显更慢，实时性能取决于硬件。
- 建议 16 GB 内存或以上；已验证 RTX 3060 Laptop 6 GB，不保证所有 GPU / CPU。
- 程序约 2.497 GB，模型及下载暂存、输出需要额外空间；模型首次下载需要网络。
- 麦克风需要可用输入设备和系统授权；系统音频采集默认播放设备。
- 不承诺 Windows 7、ARM64 或 macOS 正式支持。

## 使用方式

### 文件转录

添加或拖入音频 / 视频，可批量添加。选择识别语言、中文翻译开关、质量模式、输出格式和目录，再开始。翻译当前仅支持英文 → 简体中文。完成后打开输出目录查看结果。

### 实时字幕

选择麦克风或 Windows 系统音频，确认设备后开始。英文草稿（partial）会更新，已确认内容（final）与中文译文保存在会话中。停止后可导出；系统音频测试时请确保默认播放设备未静音且音量适中。

### 悬浮字幕

可选择 English、中文或双语，调整字号、位置及透明度，切换编辑 / 观看模式。中文显示需要开启翻译并准备翻译模型。

## 支持格式

输入：**MP3、WAV、M4A、FLAC、AAC、OGG、MP4**。是否能解码还取决于文件完整性与具体编码。

输出：**TXT、DOCX、JSON、SRT、VTT**。字幕使用真实 segment 时间戳；当前字幕优先保留原文，双语结果可保存到 JSON / DOCX。

## 模型

| 用途 | 模型 | 大致大小 |
| --- | --- | --- |
| 高精度文件 ASR | large-v3 | 3.09 GB |
| 实时 ASR | small | 0.49 GB |
| 英文 → 简体中文 | Helsinki-NLP/opus-mt-en-zh + OpenCC，CPU | 0.32 GB |

文件与实时模型独立配置；硬件检测和质量模式可能推荐更适合当前电脑的选择。模型不包含在 Git 仓库或 Installer 中。优先在应用“语音模型”页面按需下载，已有可识别模型会被复用。

## 隐私

ASR 和默认翻译本地运行，音频、转录默认不上传；模型下载需要联网。诊断字段白名单不包含转录正文、原始音频或完整日志。日志可能含个人路径，恢复文件含字幕，分享前应检查。详见 [PRIVACY](PRIVACY.md)。

## 已知限制

- Installer 尚未 Authenticode 签名；Windows 可能显示 Unknown Publisher 或 SmartScreen 提示。
- 跨版本 Upgrade 验证为 **PARTIAL**，同版覆盖 / 重装不等于跨版本升级。
- 部分硬件、真人麦克风内容、耳机 / 蓝牙、实体多显示器、部分物理 DPI 未完整验证。
- 资源管理器跨窗口拖放未完整验证；应用内部原生拖放已验证。
- 某些 DRM / protected audio 或特殊音频路径可能无法捕获。
- 识别和翻译可能出错，重要内容应人工复核。macOS 未正式支持；无云端 ASR 或自动更新。

更多范围见 [0.1.0 Release Notes](RELEASE_NOTES_0.1.0.md)。不要为使用软件关闭系统安全防护。

## License 与商业授权

LocalASR 使用 [PolyForm Noncommercial License 1.0.0](LICENSE)，定位 **Source-available / 源码公开**。非商业使用遵循许可证；任何商业用途需要单独商业许可，联系 **yehao769399481@gmail.com**，见 [COMMERCIAL_LICENSE](COMMERCIAL_LICENSE.md)。

第三方组件和模型分别遵循各自许可证，见 [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)。Native 再分发义务仍为 **LEGAL REVIEW RECOMMENDED**，不声称法律确认完毕。

安全问题请私密联系 **yehao769399481@gmail.com**，见 [SECURITY](SECURITY.md)。

## 开发者指南

以下命令在 Windows PowerShell、仓库根目录执行。所有 Python、依赖、测试和构建操作使用 Conda `asr`。已有可用环境不需要为阅读文档重装或升级。

### 获取源码与创建环境

```powershell
git clone https://github.com/769399481/LocalASR.git
cd LocalASR
conda create -n asr python=3.11
conda activate asr
```

主要验证环境为 Python **3.11.15**，通常无需精确锁定此补丁版本；该项目目标为 Windows x64 / Python 3.11。

### 依赖与 GPU / CPU

实际参考版本：faster-whisper **1.2.1**、CTranslate2 **4.8.1**、PyTorch **2.6.0+cu124**、python-docx **1.2.0**、tkinterdnd2 **0.6.3**；实时依赖 sounddevice **0.5.4**、webrtcvad-wheels **2.0.14**、NumPy **2.4.4**、Windows PyAudioWPatch **0.2.12.8**；翻译使用 Transformers **5.13.1**、SentencePiece **0.2.2**、Sacremoses **0.1.1**、OpenCC reimplementation **0.1.7**。

新环境安装完整 GUI 功能的直接依赖：

```powershell
conda run -n asr python -m pip install -r requirements.txt -r requirements-realtime.txt -r requirements-translation.txt
```

这些文件固定直接依赖，并非完整传递依赖 lock。`requirements.txt` 的 `torch==2.6.0` **不指定 CUDA build**。需要 NVIDIA GPU 的开发者应按 [PyTorch 官方 2.6.0 安装说明](https://docs.pytorch.org/get-started/previous-versions/)选择适合硬件的 wheel；已验证参考是 2.6.0+cu124，不应随意升级到其他版本。

ASR 推理由 CTranslate2 执行，不能仅用 `torch.cuda.is_available()` 判断 ASR 可用性。GPU 还需要兼容 NVIDIA 驱动及可被找到的 CUDA/cuBLAS/cuDNN runtime DLL，参见 [faster-whisper 1.2.1](https://github.com/SYSTRAN/faster-whisper/tree/v1.2.1)。通常无需完整 CUDA Toolkit；安装 Python requirements 本身不保证 GPU 路径就绪。

无 NVIDIA GPU 时可用 CPU fallback；文件 ASR 更慢，不保证所有 CPU 达到实时。翻译默认用 CPU，避免占用实时 ASR 的 GPU 显存。当前 optimized 构建另有 CUDA runtime 收集要求，见下文，不能把 CPU 源码运行等同于可构建相同 GPU 安装包。

### 源码运行与模型准备

真实 GUI 入口：

```powershell
conda run -n asr --no-capture-output python src/gui.py
```

启动后打开“语音模型”，勾选需要的模型并下载；不是每次启动自动下载所有模型。托管模型存入数据根目录的 `models/<model-id>/<pinned-revision>`。`src/model_catalog.json` 固定 revision、文件大小和 SHA256 / Git blob SHA-1；下载使用暂存目录、校验后标记完成，支持取消与重试。旧模型路径 / HF cache 的识别也有兼容逻辑，校验范围不完全等同受管理下载，勿手动伪造完成标记。

其他实际入口：

```powershell
conda run -n asr --no-capture-output python src/main.py
conda run -n asr --no-capture-output python src/realtime_demo.py --help
```

文件 CLI 读取 `src/config.py`，实时 CLI 配置在 `src/realtime_config.py`；先按实际模型、输入和输出目录配置，再运行批处理。

### 配置与用户数据

| 内容 | 默认数据根目录下的位置 |
| --- | --- |
| GUI 配置 | gui_settings.json |
| 模型 / 下载暂存 / 缓存 | models/、downloads/、cache/ |
| 日志 / 会话恢复 | logs/、recovery/ |
| 默认输出 | output/（GUI 可选择其他目录） |

源码运行的数据根目录默认是仓库根目录；安装版 / standalone 默认是 `%LOCALAPPDATA%\LocalASR`，两者并非同一默认位置。可用环境变量 `LOCALASR_DATA_DIR` 隔离测试数据，例如：

```powershell
$env:LOCALASR_DATA_DIR = Join-Path $PWD 'validation/source-smoke'
conda run -n asr --no-capture-output python src/gui.py
# 应用关闭后，恢复当前 shell 的默认数据位置：
Remove-Item Env:LOCALASR_DATA_DIR
```

此命令只移除 shell 环境变量，不删除数据。模型、配置、录音、输出、日志、恢复、构建与验证产物均被 Git 忽略；不要用私人输出执行测试。

### 测试

完整回归命令：

```powershell
conda run -n asr --no-capture-output python -m unittest discover -s tests -v
```

Phase 15 release baseline：**280 tests passed**。自动测试包含模拟模型/音频、临时目录、真实 Tk 控件和子进程；不依赖真实模型或私人输入，不等于所有硬件验证。Tk 测试需要可用 Windows 桌面。当前没有经 runner 验证的 CI，传递依赖未全锁定，不承诺新机器获得完全相同结果。

验证测试命令的小范围示例：

```powershell
conda run -n asr --no-capture-output python -m unittest discover -s tests -p test_subtitle_export.py -v
```

Phase 15.1 已实际验证源码 GUI 启动与此子集（19 tests passed），未重复完整发布回归。`tests/manual_*.py` 不在自动 discovery 范围；需要相应本地模型/音频。历史 GUI replay 默认音频在本地 validation 中，clone 不包含；请提供自有测试音频，或使用支持参数的 benchmark（短单声道 PCM16 / 16 kHz WAV）。

### Windows standalone 构建

先安装构建依赖并下载**仅供打包暂存**的 CPU torch wheel（不替换当前环境 GPU torch）：

```powershell
conda run -n asr python -m pip install -r requirements-build.txt
conda run -n asr python -m pip download --no-deps --only-binary=:all: --index-url https://download.pytorch.org/whl/cpu "torch==2.6.0+cpu" --dest distribution/vendor
conda run -n asr python distribution/check_build_paths.py
.\build.ps1 -Variant optimized
```

参考构建工具为 PyInstaller **6.22.3**、hooks-contrib **2026.8**。入口 `distribution/build.py`，spec `distribution/LocalASR.spec`。输出 `dist/LocalASR-Optimized/LocalASR.exe`；必须保留整个目录，不能只复制 EXE。optimized 构建会清理 `build/optimized` 和 `dist/LocalASR-Optimized`，运行前备份需要的版本。

构建会从开发环境现有 CUDA torch 的 `lib` 收集指定 CUDA/cuDNN DLL，缺少时明确失败；CPU wheel 仅暂存供 Marian 打包。体积主要来自 Python/native runtime、GPU runtime 和翻译依赖，模型不打包。UI 资源由 Tk 生成，无外部自定义 icon。

Phase 15 已实际使用以下独立目标构建封板 RC：

```powershell
conda run -n asr --no-capture-output python distribution/build.py --phase15
```

它会重新生成 `build/phase15` 与 `dist/LocalASR-Phase15`；**不要在保留最终 RC 的工作区随意运行**。本次文档阶段没有重新构建。

### Windows Installer 构建

需要官方 [Inno Setup](https://jrsoftware.org/isinfo.php)，当前验证为 **6.7.3**。实际源文件 `distribution/installer/LocalASR.iss`，旧 `distribution/installer.iss` 仅作 include 兼容入口。

先完成 standalone，再运行安装器脚本；它不会自动执行 PyInstaller：

```powershell
.\distribution\installer\build_installer.ps1 -Standalone dist/LocalASR-Optimized -OutputDirectory dist/release-local -CheckOnly
.\distribution\installer\build_installer.ps1 -Standalone dist/LocalASR-Optimized -OutputDirectory dist/release-local
```

脚本自动查找 `tools/InnoSetup/ISCC.exe` 或标准 Inno Setup 6 安装位置；也可加 `-Compiler` 指定实际 ISCC.exe。输出 `LocalASR-Setup-0.1.0-win64.exe`、`SHA256SUMS.txt` 和 `build-summary.json`；已存在文件会拒绝覆盖，重建请使用新的输出目录。版本取自 `src/app_version.py` 并核对载荷版本。

Phase 15 RC 位于 `dist/release-phase15`，保持不变。详细安装策略与签名范围见 [INSTALLER](docs/INSTALLER.md)、[CODE_SIGNING](docs/CODE_SIGNING.md)。

### SHA256

下载目录中核对文件：

```powershell
Get-FileHash .\LocalASR-Setup-0.1.0-win64.exe -Algorithm SHA256
```

为自建制品生成清单，使用现有 helper（不会覆盖已有输出）：

```powershell
.\distribution\checksums.ps1 -Files .\dist\release-local\LocalASR-Setup-0.1.0-win64.exe -Output .\dist\release-local\SHA256SUMS-verified.txt
```

Phase 15 最终 RC：**1,303,059,102 bytes**，SHA256：`D148B3ADF46660E1EC878AB7DE6D7AA01A54DDEF01AEFEA7D861D87B75AB2836`。该哈希只适用于最终 RC，不保证自建包相同。见 [制品列表](docs/development/PHASE15_ARTIFACTS.md)。

### 项目结构

```text
LocalASR/
├─ src/                   # Core、GUI、模型 catalog、版本
├─ tests/                 # 自动与显式手工测试
├─ distribution/          # build、spec、hooks、installer、checksums
├─ docs/                  # 架构、安装策略与历史验证报告
├─ .github/               # Issue / PR 模板
├─ build.ps1
├─ requirements*.txt
├─ README.md
├─ README_EN.md
└─ LICENSE
```

模型、dist、build 和本地用户数据不随 Git clone 提供。参见 [架构](docs/ARCHITECTURE.md) 与 [贡献说明](CONTRIBUTING.md)。

### 常见问题

| 问题 | 检查方式 |
| --- | --- |
| CUDA unavailable | 查看应用硬件诊断、NVIDIA 驱动及 CTranslate2 所需 runtime；可使用 CPU fallback，不以 torch 单项检测替代 ASR 检测。 |
| Model missing | 打开“语音模型”按需下载，检查数据目录、网络和磁盘空间；不要手动标记模型完整。 |
| Microphone unavailable | 检查 Windows 默认输入设备、麦克风访问权限及其他应用占用。 |
| System Audio unavailable | Windows 使用 WASAPI loopback，检查默认输出设备、音量/静音及 PyAudioWPatch；受保护音频可能无法捕获。 |
| Translation model missing | 翻译模型独立于 ASR，单独下载中文翻译模型并安装翻译依赖。 |
| Inno Setup missing | 安装官方 Inno Setup，或将实际 ISCC.exe 路径传给 -Compiler。 |
| PyInstaller failure | 确认 asr、依赖、CPU wheel 暂存、CUDA runtime、磁盘空间、spec 与输出路径；先运行路径检查，阅读构建日志。 |
