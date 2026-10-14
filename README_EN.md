# LocalASR

[简体中文](README.md) | English

**LocalASR is a source-available Windows speech recognition and real-time translation application that runs locally.**

Project type: **Source-available**

Current stable version: **v0.1.0**

[Project Home](https://github.com/769399481/LocalASR) ·
[Issues](https://github.com/769399481/LocalASR/issues) ·
[Releases](https://github.com/769399481/LocalASR/releases)

---

## Features

- Audio / video transcription with batch file processing.
- English, Chinese, or automatic language detection.
- Real-time English subtitles from microphone input.
- Real-time subtitles from Windows system audio.
- Local English → Simplified Chinese translation while preserving the original English text.
- English, Chinese, and bilingual floating subtitles.
- Real-time session saving, recovery, and export.
- TXT / DOCX / JSON / SRT / VTT output.
- Automatic hardware detection.
- On-demand speech recognition and translation model downloads.
- Speech recognition and default translation are processed locally.

---

## Download and Installation

Download the latest Windows installer from:

[GitHub Releases](https://github.com/769399481/LocalASR/releases)

Current version:

```text
LocalASR-Setup-0.1.0-win64.exe
```

Installation steps:

1. Download `LocalASR-Setup-0.1.0-win64.exe`.
2. Optionally verify the file using the included `SHA256SUMS.txt`.
3. Run the installer.
4. Review the license and choose the installation directory and optional desktop shortcut.
5. Start LocalASR from the Windows Start menu or desktop shortcut.
6. On first use, download the speech recognition and translation models you need.

Regular users do not need to install:

- Python
- Conda
- CUDA Toolkit
- Command-line development tools

NVIDIA GPU drivers are still provided by Windows or the GPU vendor.

Default per-user installation directory:

```text
%LOCALAPPDATA%\Programs\LocalASR
```

Administrator privileges are not required for installation.

---

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

from the LocalASR installation directory.

By default, uninstalling LocalASR preserves:

- User settings
- Downloaded models
- Session recovery data
- The LocalASR user data directory

Default user data directory:

```text
%LOCALAPPDATA%\LocalASR
```

You may manually delete this directory after confirming that you no longer need its contents.

Output folders selected by the user are not removed by the uninstaller.

Deleting the downloaded installer does not uninstall LocalASR.

---

## System Requirements

- Windows 10 / Windows 11 x64.
- Release validation was primarily performed on Windows 11.
- NVIDIA GPU is recommended.
- CPU fallback is available without an NVIDIA GPU, but file transcription will be significantly slower.
- Real-time performance depends on CPU, GPU, and audio conditions.
- 16 GB RAM or more is recommended.
- NVIDIA GeForce RTX 3060 Laptop GPU 6 GB has been validated.
- Identical performance is not guaranteed across all GPU / CPU combinations.
- Installed application size is approximately 2.5 GB.
- Models, temporary downloads, cache, and output files require additional disk space.
- An internet connection is required for first-time model downloads.
- Microphone features require a working input device and Windows microphone permission.
- Windows system audio capture uses the current playback device.

Currently not officially supported:

- Windows 7
- Windows ARM64
- macOS

---

## Usage

### File Transcription

Open LocalASR and go to the file transcription page.

You can:

- Add a single audio / video file.
- Add multiple files for batch processing.
- Select the recognition language.
- Enable or disable Chinese translation.
- Select a quality mode.
- Select output formats.
- Select an output directory.

Then start transcription.

Current translation direction:

```text
English → Simplified Chinese
```

After the task finishes, you can open the output directory directly.

---

### Real-Time Subtitles

Real-time subtitles support:

- Microphone input
- Windows system audio

Select the corresponding audio source and confirm the device before starting.

During real-time recognition:

- English partial results are updated continuously.
- Confirmed English final results are saved to the current session.
- When translation is enabled, final results are translated into Chinese.
- Session contents can be exported after stopping recognition.

When using Windows system audio, make sure:

- The correct default playback device is selected.
- Playback volume is not set to 0.
- The device is not muted.
- The playback device is actively outputting audio.

---

### Floating Subtitles

Floating subtitles support:

- English
- Chinese
- Bilingual

You can adjust:

- Font size
- Position
- Opacity
- Edit / viewing mode

Chinese subtitles require translation to be enabled and the translation model to be available.

---

## Supported Formats

### Input Formats

Supported:

- MP3
- WAV
- M4A
- FLAC
- AAC
- OGG
- MP4

Whether a specific file can be decoded also depends on file integrity and the actual codec used.

### Output Formats

Supported:

- TXT
- DOCX
- JSON
- SRT
- VTT

Subtitle files use real segment timestamps.

Bilingual results can be stored in formats that support the corresponding content, such as JSON and DOCX.

---

## Models

| Purpose | Model | Approximate Size |
| --- | --- | ---: |
| High-accuracy file ASR | large-v3 | ~3.09 GB |
| Real-time ASR | small | ~0.49 GB |
| English → Simplified Chinese | Helsinki-NLP/opus-mt-en-zh + OpenCC | ~0.32 GB |

File transcription and real-time recognition can use different model configurations.

LocalASR can recommend suitable runtime strategies based on hardware and quality settings.

Models:

- Are not included in the Git repository.
- Are not included in the Windows installer.
- Are downloaded separately as needed.
- Can be reused if an existing compatible model is detected.

It is recommended to install required models from the **Speech Models** page inside the application.

---

## Privacy

LocalASR is designed primarily for local processing.

By default:

- Speech recognition runs locally.
- Translation runs locally.
- Audio is not uploaded to the cloud for recognition.
- Transcription text is not uploaded to the cloud for recognition.

Model downloads require internet access.

Diagnostic fields do not intentionally include:

- Full transcription content
- Raw audio
- Complete user logs

However:

- Logs may contain local file paths.
- Session recovery files may contain subtitles or transcription content.
- Users should review logs, recovery files, or exported files before sharing them.

For details, see:

[PRIVACY.md](PRIVACY.md)

---

## Known Limitations

- The Windows installer is currently not Authenticode-signed.
- Windows may display `Unknown Publisher`.
- Microsoft SmartScreen may display a security warning.
- Cross-version upgrades have not been validated across every real-world upgrade scenario.
- Some GPU / CPU / audio device combinations have not been fully tested.
- Real microphone environments vary significantly.
- Headphone / Bluetooth combinations have not been fully tested.
- Physical multi-monitor and some DPI combinations have not been fully tested.
- Cross-window drag-and-drop from File Explorer has not been validated in every environment.
- Some DRM / Protected Audio content may not be capturable through system audio.
- Some software and virtual audio devices may affect WASAPI loopback capture.
- ASR may produce recognition errors.
- Machine translation may produce translation errors.
- Important content should be reviewed manually.
- Cloud ASR is not currently provided.
- Automatic updates are not currently provided.
- macOS is not currently an official release platform.

Do not disable Windows security protections just to run LocalASR.

Version update information:

[RELEASE_NOTES_0.1.0.md](RELEASE_NOTES_0.1.0.md)

---

## License and Commercial Licensing

LocalASR is licensed under:

[PolyForm Noncommercial License 1.0.0](LICENSE)

Project type:

**Source-available**

Noncommercial use must comply with the PolyForm Noncommercial License 1.0.0.

Commercial use requires a separate commercial license.

Commercial licensing contact:

```text
yehao769399481@gmail.com
```

See:

[COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)

Third-party components and models remain subject to their own licenses.

See:

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

Users are responsible for reviewing third-party dependency, native runtime, model, and redistribution obligations for their actual use case. This project does not claim to provide legal advice for every possible usage scenario.

For security issues, please contact privately:

```text
yehao769399481@gmail.com
```

See:

[SECURITY.md](SECURITY.md)

---

# Developer Guide

The following commands assume:

- Windows
- PowerShell
- The LocalASR repository root directory

Recommended Conda environment:

```text
asr
```

Primary validated Python version:

```text
Python 3.11.15
```

Target development environment:

```text
Windows x64
Python 3.11
```

---

## Get the Source Code

```powershell
git clone https://github.com/769399481/LocalASR.git
cd LocalASR
```

Create a Conda environment:

```powershell
conda create -n asr python=3.11
conda activate asr
```

If you already have a working `asr` environment, you do not need to recreate it.

---

## Install Dependencies

Install the main dependencies required for the full GUI:

```powershell
conda run -n asr python -m pip install -r requirements.txt -r requirements-realtime.txt -r requirements-translation.txt
```

Reference versions used by the project include:

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

These requirements files primarily pin direct dependencies and are not a full transitive dependency lock.

---

## NVIDIA GPU

In `requirements.txt`:

```text
torch==2.6.0
```

does not force a specific CUDA wheel.

Developers using an NVIDIA GPU should choose a PyTorch build appropriate for their own hardware and driver environment.

Primary validated LocalASR environment:

```text
PyTorch 2.6.0+cu124
```

Official PyTorch installation instructions:

https://docs.pytorch.org/get-started/previous-versions/

Important:

ASR inference is primarily performed by CTranslate2.

Therefore:

```python
torch.cuda.is_available()
```

alone does not guarantee that faster-whisper / CTranslate2 GPU inference will work correctly.

GPU ASR also requires:

- NVIDIA driver
- CUDA Runtime accessible to CTranslate2
- cuBLAS
- cuDNN
- Required DLLs available to the application

faster-whisper:

https://github.com/SYSTRAN/faster-whisper

A full CUDA Toolkit installation is usually not required.

Installing Python requirements alone does not guarantee that the GPU inference environment is fully configured.

---

## CPU Fallback

CPU fallback is available when no NVIDIA GPU is present.

Keep in mind:

- File ASR will be significantly slower.
- Real-time performance is not guaranteed on every CPU.
- Real-time ASR performance depends heavily on CPU performance.
- Translation uses CPU by default to avoid consuming ASR GPU VRAM.

---

## Run from Source

Start the GUI:

```powershell
conda run -n asr --no-capture-output python src/gui.py
```

After startup, open:

```text
Speech Models
```

and download the models you need.

LocalASR does not automatically download every model on each startup.

Managed models are typically stored under:

```text
models/<model-id>/<pinned-revision>
```

Model catalog:

```text
src/model_catalog.json
```

The catalog contains model version, file information, and integrity verification metadata.

The model downloader supports:

- Temporary download directories
- Post-download verification
- Cancellation
- Retry
- Reuse of existing compatible models

Do not manually forge model completion markers.

---

## Other Source Entry Points

File CLI:

```powershell
conda run -n asr --no-capture-output python src/main.py
```

Real-time CLI:

```powershell
conda run -n asr --no-capture-output python src/realtime_demo.py --help
```

File CLI configuration:

```text
src/config.py
```

Real-time configuration:

```text
src/realtime_config.py
```

Before running batch processing, configure the actual model, input directory, and output directory as needed.

---

## Configuration and User Data

### Source Mode

When running from source, the default data root is the repository root.

Main locations:

| Content | Default Location |
| --- | --- |
| GUI settings | `gui_settings.json` |
| Models | `models/` |
| Temporary downloads | `downloads/` |
| Cache | `cache/` |
| Logs | `logs/` |
| Session recovery | `recovery/` |
| Default output | `output/` |

### Installed / Standalone Mode

Installed and standalone versions use:

```text
%LOCALAPPDATA%\LocalASR
```

by default.

Source mode and installed mode therefore do not use the same default data location.

---

## Custom Data Directory

You can use:

```text
LOCALASR_DATA_DIR
```

to isolate test data.

Example:

```powershell
$env:LOCALASR_DATA_DIR = Join-Path $PWD 'validation/source-smoke'

conda run -n asr --no-capture-output python src/gui.py
```

After closing the application, restore the current PowerShell environment:

```powershell
Remove-Item Env:LOCALASR_DATA_DIR
```

This command:

- Only removes the environment variable from the current shell.
- Does not delete any actual data.

Models, settings, recordings, output, logs, recovery files, and build artifacts should not be committed to Git.

---

## Testing

Run the full automated test suite:

```powershell
conda run -n asr --no-capture-output python -m unittest discover -s tests -v
```

Full automated regression result before the LocalASR v0.1.0 release:

```text
280 tests passed
```

Automated tests cover areas including:

- Mock models
- Mock audio
- Temporary directories
- Tk GUI controls
- Subprocess behavior
- Transcription logic
- Real-time processing logic
- Export logic
- Model management logic

Automated tests do not mean that every real hardware combination has been validated.

Tk GUI tests require an available Windows desktop environment.

There is currently no long-term validated public CI runner configuration.

Transitive dependencies are not fully locked, so recreating the environment on another machine may produce differences.

---

## Run Selected Tests

Example:

```powershell
conda run -n asr --no-capture-output python -m unittest discover -s tests -p test_subtitle_export.py -v
```

Some `tests/manual_*.py` files are explicit manual tests and are not included in default unittest discovery.

These tests may require:

- Local ASR models
- Translation models
- Real audio files
- Microphone access
- Windows system audio

Use your own test audio and do not commit private recordings or private output.

---

## Windows Standalone Build

Install build dependencies:

```powershell
conda run -n asr python -m pip install -r requirements-build.txt
```

Download a CPU Torch wheel used only for packaging:

```powershell
conda run -n asr python -m pip download --no-deps --only-binary=:all: --index-url https://download.pytorch.org/whl/cpu "torch==2.6.0+cpu" --dest distribution/vendor
```

Check build paths:

```powershell
conda run -n asr python distribution/check_build_paths.py
```

Run the optimized build:

```powershell
.\build.ps1 -Variant optimized
```

Reference build tools:

```text
PyInstaller 6.22.3
pyinstaller-hooks-contrib 2026.8
```

Main build entry:

```text
distribution/build.py
```

PyInstaller spec:

```text
distribution/LocalASR.spec
```

Output:

```text
dist/LocalASR-Optimized/
```

Main executable:

```text
dist/LocalASR-Optimized/LocalASR.exe
```

The standalone build uses PyInstaller onedir mode.

**Keep the entire `LocalASR-Optimized` directory. Do not copy only the EXE.**

The optimized build may clean:

```text
build/optimized
dist/LocalASR-Optimized
```

Back up any build you want to keep before rebuilding.

---

## Standalone GPU Runtime

The optimized build collects required CUDA / cuDNN DLLs from the CUDA-enabled PyTorch runtime already available in the development environment.

If required runtime files are missing, the build should fail explicitly.

The CPU Torch wheel used for Marian packaging is stored under:

```text
distribution/vendor
```

It is used only for packaging and does not replace the GPU-enabled PyTorch installed in the development environment.

The final standalone size mainly comes from:

- Python Runtime
- Native Runtime
- CUDA / cuDNN Runtime
- PyTorch / translation dependencies
- GUI and application code

ASR and translation model weights are not included in the standalone package.

---

## Windows Installer Build

The installer uses:

```text
Inno Setup
```

Validated version:

```text
Inno Setup 6.7.3
```

Installer source:

```text
distribution/installer/LocalASR.iss
```

Compatibility entry:

```text
distribution/installer.iss
```

You must build the standalone package first.

The installer build script does not automatically run PyInstaller.

Check the installer configuration:

```powershell
.\distribution\installer\build_installer.ps1 `
    -Standalone dist/LocalASR-Optimized `
    -OutputDirectory dist/release-local `
    -CheckOnly
```

Build the installer:

```powershell
.\distribution\installer\build_installer.ps1 `
    -Standalone dist/LocalASR-Optimized `
    -OutputDirectory dist/release-local
```

The script attempts to locate:

```text
tools/InnoSetup/ISCC.exe
```

or a standard Inno Setup 6 installation.

You can also use:

```text
-Compiler
```

to specify the actual:

```text
ISCC.exe
```

path manually.

A successful installer build produces files similar to:

```text
LocalASR-Setup-0.1.0-win64.exe
SHA256SUMS.txt
build-summary.json
```

The script does not overwrite an existing release file with the same name by default.

Use a new output directory when rebuilding.

The application version is read from:

```text
src/app_version.py
```

The installer build validates the payload version.

---

## SHA256

Verify the downloaded official installer:

```powershell
Get-FileHash .\LocalASR-Setup-0.1.0-win64.exe -Algorithm SHA256
```

Official LocalASR v0.1.0 Windows installer:

```text
File:
LocalASR-Setup-0.1.0-win64.exe

Size:
1,303,059,102 bytes

SHA256:
D148B3ADF46660E1EC878AB7DE6D7AA01A54DDEF01AEFEA7D861D87B75AB2836
```

You can also compare it with:

```text
SHA256SUMS.txt
```

provided in the GitHub Release.

To generate a SHA256 manifest for your own installer build:

```powershell
.\distribution\checksums.ps1 `
    -Files .\dist\release-local\LocalASR-Setup-0.1.0-win64.exe `
    -Output .\dist\release-local\SHA256SUMS-verified.txt
```

A locally rebuilt installer may have different binary contents and a different SHA256 even if the version number is the same.

---

## Project Structure

```text
LocalASR/
├─ .github/                     # GitHub Issue / PR configuration
├─ distribution/                # Standalone, installer, build, and checksum tools
├─ src/                         # Core code, GUI, model management, version information
├─ tests/                       # Automated and explicit manual tests
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

The following are not included when cloning the Git repository:

- ASR models
- Translation models
- `dist/`
- `build/`
- Local user data
- Download cache
- User output
- Private recordings
- Local logs

---

## Troubleshooting

| Problem | What to Check |
| --- | --- |
| CUDA unavailable | Check LocalASR hardware diagnostics, NVIDIA drivers, and the runtime required by CTranslate2. CPU fallback is available. Do not rely only on `torch.cuda.is_available()` to determine ASR GPU availability. |
| Model missing | Open the Speech Models page and download the required model. Check network access, disk space, and the data directory. |
| Microphone unavailable | Check the Windows default input device, microphone permission, and whether another application is exclusively using the device. |
| System Audio unavailable | Check the default playback device, volume, mute state, and PyAudioWPatch. Some protected audio may not be capturable. |
| Translation model missing | The translation model is separate from the ASR models and must be downloaded independently. Translation dependencies must also be installed. |
| Inno Setup missing | Install the official Inno Setup package or provide the actual `ISCC.exe` path through `-Compiler`. |
| PyInstaller failure | Check the Conda `asr` environment, build dependencies, CPU Torch wheel staging, CUDA Runtime, disk space, spec file, and output paths. |

---

## Feedback and Issues

If you find a bug or want to request a feature, use:

[GitHub Issues](https://github.com/769399481/LocalASR/issues)

When reporting an issue, please include:

- Windows version
- CPU
- GPU
- LocalASR version
- ASR model used
- Audio source
- Steps to reproduce the issue
- Relevant error information

Please do not publicly submit:

- Private recordings
- Full transcriptions containing sensitive information
- Passwords
- Tokens
- Private API keys
- Other personal or sensitive data

Do not report security vulnerabilities through public GitHub Issues.

Please send security reports to:

```text
yehao769399481@gmail.com
```

---

## Release

Current stable version:

```text
LocalASR v0.1.0
```

Windows installer:

```text
LocalASR-Setup-0.1.0-win64.exe
```

Download:

[GitHub Releases](https://github.com/769399481/LocalASR/releases)

Release Notes:

[RELEASE_NOTES_0.1.0.md](RELEASE_NOTES_0.1.0.md)

---

## License

LocalASR is source-available software licensed under the:

**PolyForm Noncommercial License 1.0.0**

See:

[LICENSE](LICENSE)

Commercial use requires separate permission.

Commercial licensing:

```text
yehao769399481@gmail.com
```