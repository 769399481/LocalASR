# LocalASR

简体中文 | [English](README_EN.md)

**LocalASR 一款本地运行的 Windows 语音识别与实时翻译工具。**

项目定位：**Source-available**。

当前稳定版本：**v0.1.0**

[项目主页](https://github.com/769399481/LocalASR) ·
[Issues](https://github.com/769399481/LocalASR/issues) ·
[Releases](https://github.com/769399481/LocalASR/releases)

---

## 功能特点

- 音频 / 视频文件转录及多文件批量处理。
- 支持英文、中文或自动语言识别。
- 麦克风实时英文字幕。
- Windows 系统音频实时字幕。
- 英文 → 简体中文本地翻译，并保留英文原文。
- 英文、中文、双语悬浮字幕。
- 实时会话保存、恢复与导出。
- TXT / DOCX / JSON / SRT / VTT 输出。
- 自动硬件检测。
- 语音识别模型和翻译模型按需下载。
- 音频识别和默认翻译均在本地运行。

---

## 下载与安装

请从：

[GitHub Releases](https://github.com/769399481/LocalASR/releases)

下载最新 Windows 安装包。

当前版本：

```text
LocalASR-Setup-0.1.0-win64.exe
```

安装步骤：

1. 下载 `LocalASR-Setup-0.1.0-win64.exe`。
2. 可使用 Release 中提供的 `SHA256SUMS.txt` 核对文件完整性。
3. 运行 Installer。
4. 阅读许可证并选择安装目录及可选桌面快捷方式。
5. 从 Windows 开始菜单或桌面快捷方式启动 LocalASR。
6. 首次使用时，根据需要下载语音识别和翻译模型。

普通用户无需安装：

- Python
- Conda
- CUDA Toolkit
- 命令行开发环境

NVIDIA 显卡驱动仍由 Windows 或显卡厂商提供。

默认每用户安装目录：

```text
%LOCALAPPDATA%\Programs\LocalASR
```

安装不需要管理员权限。

---

## 卸载

关闭正在运行的 LocalASR 后，可以通过：

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

- 用户配置
- 已下载模型
- 会话恢复数据
- LocalASR 用户数据目录

默认用户数据目录：

```text
%LOCALAPPDATA%\LocalASR
```

确认不再需要这些内容后，可以手动删除该目录。

用户自行选择的输出目录不会被卸载程序删除。

删除下载的 Installer 本身不会卸载已经安装的 LocalASR。

---

## 系统要求

- Windows 10 / Windows 11 x64。
- 实际发布验证主要基于 Windows 11。
- 推荐 NVIDIA GPU。
- 无 NVIDIA GPU 时可以使用 CPU fallback，但文件转录速度会明显降低。
- 实时性能取决于 CPU、GPU 和音频环境。
- 建议 16 GB 内存或以上。
- 已验证 NVIDIA GeForce RTX 3060 Laptop GPU 6 GB。
- 不保证所有 GPU / CPU 组合均具有相同表现。
- 程序安装体积约 2.5 GB。
- 模型、下载暂存、缓存及输出文件需要额外磁盘空间。
- 首次下载模型需要网络连接。
- 麦克风功能需要有效输入设备以及 Windows 麦克风权限。
- Windows 系统音频采集默认使用当前播放设备。

当前不正式支持：

- Windows 7
- Windows ARM64
- macOS

---

## 使用方式

### 文件转录

打开 LocalASR 后进入文件转录页面。

可以：

- 添加单个音频 / 视频文件。
- 一次添加多个文件进行批量处理。
- 选择识别语言。
- 开启或关闭中文翻译。
- 选择质量模式。
- 选择输出格式。
- 选择输出目录。

然后开始转录。

当前翻译方向：

```text
English → 简体中文
```

任务完成后可以直接打开输出目录查看结果。

---

### 实时字幕

实时字幕支持：

- 麦克风输入
- Windows 系统音频

开始前选择对应音频来源并确认设备。

实时识别过程中：

- 英文 partial 会持续更新。
- 已确认的英文 final 会保存到当前会话。
- 开启翻译后，final 内容会进行中文翻译。
- 停止实时识别后可以导出会话内容。

使用 Windows 系统音频时，请确认：

- 默认播放设备正确。
- 音量不是 0。
- 没有静音。
- 播放设备当前正常输出声音。

---

### 悬浮字幕

悬浮字幕支持：

- English
- 中文
- 双语

可以调整：

- 字号
- 位置
- 透明度
- 编辑 / 观看模式

中文字幕需要开启翻译，并准备好翻译模型。

---

## 支持格式

### 输入格式

支持：

- MP3
- WAV
- M4A
- FLAC
- AAC
- OGG
- MP4

具体文件是否可以正常解码，也取决于文件本身是否完整以及实际编码格式。

### 输出格式

支持：

- TXT
- DOCX
- JSON
- SRT
- VTT

字幕文件使用真实 segment 时间戳。

双语结果可以保存到 JSON / DOCX 等支持对应内容的格式。

---

## 模型

| 用途 | 模型 | 大致大小 |
| --- | --- | ---: |
| 高精度文件 ASR | large-v3 | 约 3.09 GB |
| 实时 ASR | small | 约 0.49 GB |
| 英文 → 简体中文 | Helsinki-NLP/opus-mt-en-zh + OpenCC | 约 0.32 GB |

文件转录和实时识别可以使用不同模型配置。

LocalASR 会根据硬件情况和质量模式推荐合适的运行策略。

模型：

- 不包含在 Git 仓库中。
- 不包含在 Windows Installer 中。
- 根据需要单独下载。
- 已存在并可识别的模型可以被复用。

推荐直接在应用中的 **语音模型** 页面安装需要的模型。

---

## 隐私

LocalASR 以本地处理为主要设计方向。

默认情况下：

- 音频识别在本地运行。
- 翻译在本地运行。
- 音频不会因为识别而上传到云端。
- 转录正文不会因为识别而上传到云端。

模型下载需要联网。

诊断字段不会主动包含：

- 完整转录正文
- 原始音频
- 完整用户日志

但是：

- 日志可能包含本地文件路径。
- 会话恢复文件可能包含字幕或转录内容。
- 用户主动分享日志、恢复文件或输出文件前，应自行检查其中的信息。

详细说明见：

[PRIVACY.md](PRIVACY.md)

---

## 已知限制

- Windows Installer 当前没有 Authenticode 数字签名。
- Windows 可能显示 `Unknown Publisher`。
- Microsoft SmartScreen 可能显示安全提示。
- 跨版本 Upgrade 尚未覆盖所有真实升级场景。
- 部分 GPU / CPU / 音频设备组合未完整验证。
- 真人麦克风环境差异较大。
- 耳机 / 蓝牙设备组合未完整验证。
- 实体多显示器及部分 DPI 组合未完整验证。
- 资源管理器跨窗口拖放未覆盖所有实际环境。
- 某些 DRM / Protected Audio 内容可能无法通过系统音频捕获。
- 不同软件和虚拟音频设备可能影响 WASAPI loopback。
- ASR 可能产生识别错误。
- 机器翻译可能产生翻译错误。
- 重要内容应人工复核。
- 当前没有云端 ASR。
- 当前没有自动更新功能。
- macOS 当前不是正式发布平台。

不要为了运行 LocalASR 而关闭 Windows 系统安全防护。

版本更新说明见：

[RELEASE_NOTES_0.1.0.md](RELEASE_NOTES_0.1.0.md)

---

## License 与商业授权

LocalASR 使用：

[PolyForm Noncommercial License 1.0.0](LICENSE)

项目定位：

**Source-available / 源码公开**

非商业使用应遵循 PolyForm Noncommercial License 1.0.0。

商业用途需要获得单独商业许可。

商业授权联系：

```text
yehao769399481@gmail.com
```

详细说明：

[COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)

第三方组件及模型分别遵循各自许可证。

详情见：

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

第三方依赖、Native Runtime、模型及再分发义务应根据实际使用场景自行核查。本项目不声称已经提供针对所有使用场景的法律意见。

安全问题请通过以下邮箱私密联系：

```text
yehao769399481@gmail.com
```

详情见：

[SECURITY.md](SECURITY.md)

---

# 开发者指南

以下命令默认在：

- Windows
- PowerShell
- LocalASR 仓库根目录

中执行。

推荐使用 Conda 环境：

```text
asr
```

主要验证 Python 版本：

```text
Python 3.11.15
```

项目目标运行环境：

```text
Windows x64
Python 3.11
```

---

## 获取源码

```powershell
git clone https://github.com/769399481/LocalASR.git
cd LocalASR
```

创建 Conda 环境：

```powershell
conda create -n asr python=3.11
conda activate asr
```

如果已经存在可用的 `asr` 环境，则无需重新创建。

---

## 安装依赖

完整 GUI 功能的主要依赖：

```powershell
conda run -n asr python -m pip install -r requirements.txt -r requirements-realtime.txt -r requirements-translation.txt
```

项目实际参考版本包括：

- faster-whisper `1.2.1`
- CTranslate2 `4.8.1`
- PyTorch `2.6.0+cu124`
- python-docx `1.2.0`
- tkinterdnd2 `0.6.3`
- sounddevice `0.5.4`
- webrtcvad-wheels `2.0.14`
- NumPy `2.4.4`
- PyAudioWPatch `0.2.12.8`
- Transformers `5.13.1`
- SentencePiece `0.2.2`
- Sacremoses `0.1.1`
- OpenCC reimplementation `0.1.7`

这些 requirements 文件主要固定直接依赖，并不是完整传递依赖 lock。

---

## NVIDIA GPU

`requirements.txt` 中的：

```text
torch==2.6.0
```

不强制指定 CUDA wheel。

需要 NVIDIA GPU 的开发者应根据自己的驱动和硬件环境选择合适的 PyTorch 版本。

LocalASR 当前主要验证环境：

```text
PyTorch 2.6.0+cu124
```

PyTorch 官方安装说明：

https://docs.pytorch.org/get-started/previous-versions/

需要注意：

ASR 推理主要由 CTranslate2 执行。

因此：

```python
torch.cuda.is_available()
```

并不能单独代表 faster-whisper / CTranslate2 的 GPU 推理环境一定正常。

GPU ASR 还需要：

- NVIDIA 驱动
- CTranslate2 可访问的 CUDA Runtime
- cuBLAS
- cuDNN
- 对应 DLL 可以被程序正确找到

faster-whisper：

https://github.com/SYSTRAN/faster-whisper

通常不需要完整安装 CUDA Toolkit。

仅安装 Python requirements 也不代表 GPU 推理环境一定配置完成。

---

## CPU fallback

没有 NVIDIA GPU 时，可以使用 CPU fallback。

需要注意：

- 文件 ASR 会明显更慢。
- 不保证所有 CPU 都能达到实时识别速度。
- 实时 ASR 性能与 CPU 性能密切相关。
- 翻译默认使用 CPU，以减少对 ASR GPU 显存的占用。

---

## 源码运行

启动 GUI：

```powershell
conda run -n asr --no-capture-output python src/gui.py
```

启动后打开：

```text
语音模型
```

然后下载需要的模型。

LocalASR 不会在每次启动时自动下载全部模型。

受管理模型通常保存到：

```text
models/<model-id>/<pinned-revision>
```

模型 catalog：

```text
src/model_catalog.json
```

其中包含模型版本、文件信息和完整性校验数据。

模型下载支持：

- 临时目录
- 下载完成校验
- 取消
- 重试
- 已存在模型复用

不要手动伪造模型完成标记。

---

## 其他源码入口

文件 CLI：

```powershell
conda run -n asr --no-capture-output python src/main.py
```

实时 CLI：

```powershell
conda run -n asr --no-capture-output python src/realtime_demo.py --help
```

文件 CLI 配置：

```text
src/config.py
```

实时配置：

```text
src/realtime_config.py
```

运行批处理前，应根据实际模型、输入目录和输出目录调整配置。

---

## 配置与用户数据

### 源码运行

源码运行时，默认数据根目录为仓库根目录。

主要内容包括：

| 内容 | 默认位置 |
| --- | --- |
| GUI 配置 | `gui_settings.json` |
| 模型 | `models/` |
| 下载暂存 | `downloads/` |
| 缓存 | `cache/` |
| 日志 | `logs/` |
| 会话恢复 | `recovery/` |
| 默认输出 | `output/` |

### 安装版 / Standalone

安装版和 Standalone 默认使用：

```text
%LOCALAPPDATA%\LocalASR
```

源码运行和安装版并不是同一个默认数据位置。

---

## 自定义数据目录

可以使用：

```text
LOCALASR_DATA_DIR
```

隔离测试数据。

例如：

```powershell
$env:LOCALASR_DATA_DIR = Join-Path $PWD 'validation/source-smoke'

conda run -n asr --no-capture-output python src/gui.py
```

应用关闭后恢复当前 PowerShell：

```powershell
Remove-Item Env:LOCALASR_DATA_DIR
```

该命令：

- 只删除当前 Shell 中的环境变量。
- 不会删除任何实际数据。

模型、配置、录音、输出、日志、恢复文件以及构建产物均不应提交到 Git。

---

## 测试

运行完整自动测试：

```powershell
conda run -n asr --no-capture-output python -m unittest discover -s tests -v
```

LocalASR v0.1.0 发布前完整自动化回归：

```text
280 tests passed
```

自动测试覆盖：

- 模拟模型
- 模拟音频
- 临时目录
- Tk GUI 控件
- 子进程
- 转录逻辑
- 实时处理逻辑
- 导出逻辑
- 模型管理相关逻辑

自动测试不等于所有真实硬件组合均已验证。

Tk GUI 测试需要可用 Windows 桌面环境。

当前没有经过长期验证的公共 CI runner 配置。

传递依赖没有全部锁定，因此不同机器重新创建环境时可能出现差异。

---

## 运行部分测试

例如：

```powershell
conda run -n asr --no-capture-output python -m unittest discover -s tests -p test_subtitle_export.py -v
```

部分 `tests/manual_*.py` 属于显式手工测试，不在默认 unittest discovery 范围内。

这些测试可能需要：

- 本地 ASR 模型
- 翻译模型
- 实际音频文件
- 麦克风
- Windows 系统音频

请使用自己的测试音频，不要提交私人录音或私人输出。

---

## Windows Standalone 构建

安装构建依赖：

```powershell
conda run -n asr python -m pip install -r requirements-build.txt
```

下载仅供构建暂存使用的 CPU Torch wheel：

```powershell
conda run -n asr python -m pip download --no-deps --only-binary=:all: --index-url https://download.pytorch.org/whl/cpu "torch==2.6.0+cpu" --dest distribution/vendor
```

检查构建路径：

```powershell
conda run -n asr python distribution/check_build_paths.py
```

执行 optimized 构建：

```powershell
.\build.ps1 -Variant optimized
```

参考构建工具：

```text
PyInstaller 6.22.3
pyinstaller-hooks-contrib 2026.8
```

主要构建入口：

```text
distribution/build.py
```

PyInstaller spec：

```text
distribution/LocalASR.spec
```

输出：

```text
dist/LocalASR-Optimized/
```

主程序：

```text
dist/LocalASR-Optimized/LocalASR.exe
```

Standalone 为 onedir 构建。

**必须保留整个 `LocalASR-Optimized` 目录，不能只复制其中的 EXE。**

optimized 构建可能清理：

```text
build/optimized
dist/LocalASR-Optimized
```

重新构建前，请自行备份需要保留的旧构建。

---

## Standalone GPU Runtime

optimized 构建会从当前开发环境中的 CUDA PyTorch Runtime 收集指定 CUDA / cuDNN DLL。

如果构建环境缺少需要的 Runtime，构建应明确失败。

用于 Marian 打包的 CPU Torch wheel：

```text
distribution/vendor
```

仅供构建暂存使用，不用于替换开发环境中的 GPU PyTorch。

最终 Standalone 体积主要来自：

- Python Runtime
- Native Runtime
- CUDA / cuDNN Runtime
- PyTorch / 翻译相关依赖
- GUI 与应用代码

ASR 和翻译模型不包含在 Standalone 中。

---

## Windows Installer 构建

Installer 使用：

```text
Inno Setup
```

当前验证版本：

```text
Inno Setup 6.7.3
```

Installer 源文件：

```text
distribution/installer/LocalASR.iss
```

兼容入口：

```text
distribution/installer.iss
```

需要先完成 Standalone 构建。

Installer 构建脚本不会自动执行 PyInstaller。

检查 Installer 构建：

```powershell
.\distribution\installer\build_installer.ps1 `
    -Standalone dist/LocalASR-Optimized `
    -OutputDirectory dist/release-local `
    -CheckOnly
```

正式构建：

```powershell
.\distribution\installer\build_installer.ps1 `
    -Standalone dist/LocalASR-Optimized `
    -OutputDirectory dist/release-local
```

脚本会尝试自动查找：

```text
tools/InnoSetup/ISCC.exe
```

或者系统中标准安装位置的 Inno Setup 6。

也可以使用：

```text
-Compiler
```

手动指定：

```text
ISCC.exe
```

成功构建后会生成类似：

```text
LocalASR-Setup-0.1.0-win64.exe
SHA256SUMS.txt
build-summary.json
```

脚本默认不会覆盖已经存在的同名发布文件。

如果重新构建，建议使用新的输出目录。

应用版本来自：

```text
src/app_version.py
```

Installer 构建时会核对载荷版本。

---

## SHA256

校验下载后的官方安装包：

```powershell
Get-FileHash .\LocalASR-Setup-0.1.0-win64.exe -Algorithm SHA256
```

LocalASR v0.1.0 官方 Windows 安装包：

```text
文件：
LocalASR-Setup-0.1.0-win64.exe

大小：
1,303,059,102 bytes

SHA256：
D148B3ADF46660E1EC878AB7DE6D7AA01A54DDEF01AEFEA7D861D87B75AB2836
```

也可以直接与 GitHub Release 中提供的：

```text
SHA256SUMS.txt
```

进行比较。

为自己构建的 Installer 生成 SHA256 清单：

```powershell
.\distribution\checksums.ps1 `
    -Files .\dist\release-local\LocalASR-Setup-0.1.0-win64.exe `
    -Output .\dist\release-local\SHA256SUMS-verified.txt
```

自行重新构建的 Installer 即使版本号相同，二进制内容和 SHA256 也可能与官方发布包不同。

---

## 项目结构

```text
LocalASR/
├─ .github/                     # GitHub Issue / PR 配置
├─ distribution/                # Standalone、Installer、构建及校验工具
├─ src/                         # 核心代码、GUI、模型管理、版本信息
├─ tests/                       # 自动测试与显式手工测试
│
├─ .gitignore
├─ build.ps1
│
├─ requirements.txt
├─ requirements-realtime.txt
├─ requirements-translation.txt
├─ requirements-build.txt
│
├─ README.md
├─ README_EN.md
├─ RELEASE_NOTES_0.1.0.md
│
├─ LICENSE
├─ COMMERCIAL_LICENSE.md
├─ PRIVACY.md
├─ SECURITY.md
├─ THIRD_PARTY_NOTICES.md
└─ CONTRIBUTING.md
```

以下内容不会随 Git clone 提供：

- ASR 模型
- 翻译模型
- `dist/`
- `build/`
- 本地用户数据
- 下载缓存
- 用户输出
- 私人录音
- 本地日志

---

## 常见问题

| 问题 | 检查方式 |
| --- | --- |
| CUDA unavailable | 检查应用硬件诊断、NVIDIA 驱动及 CTranslate2 所需 Runtime。可以使用 CPU fallback，不应只用 `torch.cuda.is_available()` 判断 ASR GPU 状态。 |
| Model missing | 打开“语音模型”页面下载需要的模型，并检查网络、磁盘空间和数据目录。 |
| Microphone unavailable | 检查 Windows 默认输入设备、麦克风权限以及其他软件是否独占设备。 |
| System Audio unavailable | 检查默认输出设备、音量、静音状态以及 PyAudioWPatch。部分受保护音频可能无法捕获。 |
| Translation model missing | 中文翻译模型与 ASR 模型独立，需要单独下载并安装翻译相关依赖。 |
| Inno Setup missing | 安装官方 Inno Setup，或者通过 `-Compiler` 指定实际 `ISCC.exe`。 |
| PyInstaller failure | 检查 Conda `asr` 环境、构建依赖、CPU Torch wheel 暂存、CUDA Runtime、磁盘空间、spec 和输出路径。 |

---

## 反馈与问题

如果发现 Bug 或希望提出功能建议，请使用：

[GitHub Issues](https://github.com/769399481/LocalASR/issues)

提交问题时建议提供：

- Windows 版本
- CPU
- GPU
- LocalASR 版本
- 使用的 ASR 模型
- 音频来源
- 问题复现步骤
- 必要的错误信息

请不要公开提交：

- 私人录音
- 含敏感内容的完整转录
- 密码
- Token
- 私有 API Key
- 其他个人隐私数据

安全漏洞请不要通过公开 Issue 报告。

请发送至：

```text
yehao769399481@gmail.com
```

---

## Release

当前稳定版本：

```text
LocalASR v0.1.0
```

Windows Installer：

```text
LocalASR-Setup-0.1.0-win64.exe
```

下载：

[GitHub Releases](https://github.com/769399481/LocalASR/releases)

Release Notes：

[RELEASE_NOTES_0.1.0.md](RELEASE_NOTES_0.1.0.md)

---

## License

Copyright © LocalASR contributors / copyright holder.

LocalASR is source-available software licensed under the:

**PolyForm Noncommercial License 1.0.0**

See:

[LICENSE](LICENSE)

Commercial use requires separate permission.

Commercial licensing:

```text
yehao769399481@gmail.com
```