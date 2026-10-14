# LocalASR

[简体中文](README.md) | English

**LocalASR is a source-available local speech recognition and realtime translation application for Windows.** Project positioning: **Source-available**.

The current version is **0.1.0 Release Candidate**. Phase 15 release checks are complete; no official release has been published yet.

[Repository](https://github.com/769399481/LocalASR) · [Issues](https://github.com/769399481/LocalASR/issues) · [Releases](https://github.com/769399481/LocalASR/releases)

## Features

- Audio/video file transcription and batch processing, with English, Chinese or automatic language detection.
- Realtime English captions from a microphone or Windows system audio.
- Local English → Simplified Chinese translation, preserving the English original.
- English, Chinese or bilingual floating captions; session recovery and export.
- TXT / DOCX / JSON / SRT / VTT output.
- Automatic hardware detection, on-demand model downloads and local-first processing.

## Download and installation

**After the official release**, download from [GitHub Releases](https://github.com/769399481/LocalASR/releases). This does not claim the file is already available online.

1. Download `LocalASR-Setup-0.1.0-win64.exe` and check the accompanying `SHA256SUMS.txt`.
2. Run the Installer, read the license and choose the installation directory and optional desktop shortcut.
3. Start LocalASR from the Start Menu.
4. Follow the first-use prompts to download the speech and translation models you need.

End users do not need Python, Conda, CUDA Toolkit or a command line. GPU drivers are still supplied by the OS/vendor. Installation is per-user at `%LOCALAPPDATA%\Programs\LocalASR` by default and does not require administrator privileges.

Stop tasks and close the app before uninstalling through Windows Settings → Apps → Installed apps, or by running `unins000.exe` in the installation directory. **Uninstall preserves user data and models.** Delete `%LOCALAPPDATA%\LocalASR` manually only after confirming you no longer need its contents. Exports saved elsewhere must be managed separately. Deleting the downloaded Installer does not uninstall the app.

## System requirements

- Windows 10 / 11 x64 is the target; actual installation validation used Windows 11.
- An NVIDIA GPU is recommended. CPU fallback is available, but file transcription is substantially slower and realtime performance depends on hardware.
- 16 GB RAM or more is recommended. An RTX 3060 Laptop 6 GB has been tested; not every GPU/CPU is guaranteed.
- The app occupies approximately 2.497 GB. Models, download staging and exports need additional space; initial model downloads require internet access.
- Microphone capture requires an available input device and system permission. System audio captures the default playback device.
- Windows 7, ARM64 and official macOS support are not promised.

## Usage

### File transcription

Add or drag in audio/video files, including multiple files. Choose the recognition language, Chinese translation option, quality mode, export formats and output directory, then start. Translation currently supports only English → Simplified Chinese. Open the output directory when processing finishes.

### Realtime captions

Select microphone or Windows system audio, check the device and start. English partial results may change; confirmed final results and Chinese translations remain in the session. Stop before exporting. For system audio, make sure the default playback device is unmuted and at a moderate volume.

### Floating captions

Choose English, Chinese or bilingual display, adjust font size, position and opacity, and switch between editing/viewing modes. Chinese display requires translation to be enabled and the translation model to be available.

## Supported formats

Input: **MP3, WAV, M4A, FLAC, AAC, OGG, MP4**. Decoding also depends on file integrity and the actual codec.

Output: **TXT, DOCX, JSON, SRT, VTT**. Subtitles use actual segment timestamps. Subtitle export currently prioritizes the original language; bilingual results can be saved in JSON / DOCX.

## Models

| Purpose | Model | Approximate size |
| --- | --- | --- |
| High-accuracy file ASR | large-v3 | 3.09 GB |
| Realtime ASR | small | 0.49 GB |
| English → Simplified Chinese | Helsinki-NLP/opus-mt-en-zh + OpenCC, CPU | 0.32 GB |

File and realtime models are configured separately. Hardware detection and quality modes may recommend a different choice for your computer. Models are not included in Git or the Installer. Prefer downloading them on demand through the app's speech-model page; recognizable existing models are reused.

## Privacy

ASR and default translation run locally. Audio and transcripts are not uploaded by default; model downloads require internet access. Allowlisted diagnostics do not include transcript text, original audio or complete logs. Logs may contain personal paths and recovery files contain captions; review before sharing. See [PRIVACY](PRIVACY.md).

## Known limitations

- The Installer has no Authenticode signature. Windows may display Unknown Publisher or a SmartScreen prompt.
- Cross-version Upgrade validation is **PARTIAL**. Same-version installation/reinstallation is not cross-version upgrade validation.
- Some hardware combinations, spoken microphone content, headphones/Bluetooth, physical multiple monitors and physical DPI settings have not been fully validated.
- Cross-window dragging from File Explorer has not been fully validated; internal native drag-and-drop has been tested.
- Some DRM/protected audio or special audio paths may not be captured.
- Recognition and translation can be wrong; review important content. macOS is not officially supported; there is no cloud ASR or automatic updater.

See [0.1.0 Release Notes](RELEASE_NOTES_0.1.0.md) for scope. Do not disable system security protection to use the app.

## License and commercial licensing

LocalASR uses the [PolyForm Noncommercial License 1.0.0](LICENSE) and is **Source-available**. Noncommercial use follows that license; any commercial use requires a separate commercial license. Contact **yehao769399481@gmail.com**; see [COMMERCIAL_LICENSE](COMMERCIAL_LICENSE.md).

Third-party components and models retain their own licenses; see [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md). Native redistribution obligations remain **LEGAL REVIEW RECOMMENDED**, not legally cleared.

Report security issues privately to **yehao769399481@gmail.com**; see [SECURITY](SECURITY.md).

## Developer guide

Run the following commands in Windows PowerShell from the repository root. Use Conda `asr` for all Python, dependency, test and build operations. Do not reinstall or upgrade an existing working environment just to follow this documentation.

### Clone and create the environment

```powershell
git clone https://github.com/769399481/LocalASR.git
cd LocalASR
conda create -n asr python=3.11
conda activate asr
```

The main validated environment uses Python **3.11.15**. You generally do not need to pin that exact patch version; the project targets Windows x64 / Python 3.11.

### Dependencies and GPU / CPU

Actual reference versions: faster-whisper **1.2.1**, CTranslate2 **4.8.1**, PyTorch **2.6.0+cu124**, python-docx **1.2.0**, tkinterdnd2 **0.6.3**. Realtime dependencies include sounddevice **0.5.4**, webrtcvad-wheels **2.0.14**, NumPy **2.4.4**, and Windows PyAudioWPatch **0.2.12.8**. Translation uses Transformers **5.13.1**, SentencePiece **0.2.2**, Sacremoses **0.1.1**, and the OpenCC reimplementation **0.1.7**.

For a new environment, install the direct dependencies for the complete GUI feature set:

```powershell
conda run -n asr python -m pip install -r requirements.txt -r requirements-realtime.txt -r requirements-translation.txt
```

These files pin direct dependencies, not a complete transitive lock. The `torch==2.6.0` requirement **does not select a CUDA build**. NVIDIA GPU developers should choose a compatible wheel using the [official PyTorch 2.6.0 instructions](https://docs.pytorch.org/get-started/previous-versions/). The validated reference is 2.6.0+cu124; do not casually upgrade versions.

CTranslate2 performs ASR inference; `torch.cuda.is_available()` alone does not establish ASR availability. GPU execution also needs a compatible NVIDIA driver and discoverable CUDA/cuBLAS/cuDNN runtime DLLs; see [faster-whisper 1.2.1](https://github.com/SYSTRAN/faster-whisper/tree/v1.2.1). A complete CUDA Toolkit is generally unnecessary. Installing Python requirements alone does not guarantee a working GPU path.

Without an NVIDIA GPU, CPU fallback can be used. File ASR is slower and realtime operation is not guaranteed on every CPU. Translation defaults to CPU to avoid consuming realtime ASR GPU memory. The optimized build has additional CUDA runtime collection requirements described below; CPU source execution does not imply that you can build the same GPU distribution.

### Run from source and prepare models

The actual GUI entry point is:

```powershell
conda run -n asr --no-capture-output python src/gui.py
```

Open the speech-model page, select the models you need and download them. Startup does not automatically download every model. Managed models are stored under `models/<model-id>/<pinned-revision>` inside the data root. `src/model_catalog.json` pins revisions, file sizes and SHA256 / Git blob SHA-1 values. Downloads are staged, checked and marked complete, with cancellation/retry support. Legacy model paths and HF cache discovery have compatibility handling with different validation scope; do not fabricate completion markers.

Other actual entry points:

```powershell
conda run -n asr --no-capture-output python src/main.py
conda run -n asr --no-capture-output python src/realtime_demo.py --help
```

The file CLI reads `src/config.py`; realtime CLI configuration is in `src/realtime_config.py`. Configure actual model/input/output locations before running a batch.

### Configuration and user data

| Content | Location relative to the default data root |
| --- | --- |
| GUI configuration | gui_settings.json |
| Models / download staging / cache | models/, downloads/, cache/ |
| Logs / session recovery | logs/, recovery/ |
| Default exports | output/ (the GUI can select another directory) |

Source execution defaults to the repository root. Installed/standalone builds default to `%LOCALAPPDATA%\LocalASR`; these are different default locations. Set `LOCALASR_DATA_DIR` to isolate test data, for example:

```powershell
$env:LOCALASR_DATA_DIR = Join-Path $PWD 'validation/source-smoke'
conda run -n asr --no-capture-output python src/gui.py
# After closing the app, restore the shell's default data location:
Remove-Item Env:LOCALASR_DATA_DIR
```

This removes only the shell environment variable, not data. Models, configuration, recordings, exports, logs, recovery, build and validation artifacts are ignored by Git. Do not run tests against private output.

### Tests

Complete regression command:

```powershell
conda run -n asr --no-capture-output python -m unittest discover -s tests -v
```

Phase 15 release baseline: **280 tests passed**. Automated tests use mock models/audio, temporary directories, real Tk widgets and subprocesses. They do not require real models/private input and do not certify all hardware. Tk tests need an available Windows desktop. CI has not been validated on a runner, transitive dependencies are not fully locked, and identical results on every new machine are not promised.

A smaller command-verification example:

```powershell
conda run -n asr --no-capture-output python -m unittest discover -s tests -p test_subtitle_export.py -v
```

Phase 15.1 actually verified source GUI startup and this subset (**19 tests passed**), without repeating full release regression. `tests/manual_*.py` is outside automatic discovery and requires the relevant local models/audio. Historical GUI replay defaults reference local validation audio that is not included in a clone. Supply your own test audio or use a benchmark accepting arguments (short mono PCM16 / 16 kHz WAV).

### Windows standalone build

Install build dependencies and download the CPU torch wheel **only for packaging staging**; it does not replace the GPU torch in your active environment:

```powershell
conda run -n asr python -m pip install -r requirements-build.txt
conda run -n asr python -m pip download --no-deps --only-binary=:all: --index-url https://download.pytorch.org/whl/cpu "torch==2.6.0+cpu" --dest distribution/vendor
conda run -n asr python distribution/check_build_paths.py
.\build.ps1 -Variant optimized
```

Reference build tools are PyInstaller **6.22.3** and hooks-contrib **2026.8**. The entry point is `distribution/build.py`, with `distribution/LocalASR.spec`. Output is `dist/LocalASR-Optimized/LocalASR.exe`; keep the whole folder, not just the EXE. The optimized build clears `build/optimized` and `dist/LocalASR-Optimized`, so preserve any required versions first.

The build collects specific CUDA/cuDNN DLLs from the existing CUDA torch `lib` directory and fails explicitly if they are missing. The CPU wheel is staged for Marian packaging. Size mainly comes from Python/native runtimes, GPU runtimes and translation dependencies; model weights are excluded. UI resources are generated by Tk, with no external custom icon.

Phase 15 actually built the sealed RC with this separate target:

```powershell
conda run -n asr --no-capture-output python distribution/build.py --phase15
```

This regenerates `build/phase15` and `dist/LocalASR-Phase15`. **Do not casually run it in a workspace preserving the final RC.** No build was repeated during this documentation phase.

### Windows Installer build

Install official [Inno Setup](https://jrsoftware.org/isinfo.php); the validated version is **6.7.3**. The actual source is `distribution/installer/LocalASR.iss`; `distribution/installer.iss` is only a compatibility include.

Complete the standalone build first. The installer script does not automatically run PyInstaller:

```powershell
.\distribution\installer\build_installer.ps1 -Standalone dist/LocalASR-Optimized -OutputDirectory dist/release-local -CheckOnly
.\distribution\installer\build_installer.ps1 -Standalone dist/LocalASR-Optimized -OutputDirectory dist/release-local
```

The script looks for `tools/InnoSetup/ISCC.exe` or the standard Inno Setup 6 installation; use `-Compiler` for an explicit ISCC.exe path. Output includes `LocalASR-Setup-0.1.0-win64.exe`, `SHA256SUMS.txt` and `build-summary.json`. Existing outputs are not overwritten; use a new directory for another build. Version comes from `src/app_version.py` and is checked against the payload.

The Phase 15 RC in `dist/release-phase15` remains unchanged. See [INSTALLER](docs/INSTALLER.md) and [CODE_SIGNING](docs/CODE_SIGNING.md) for installation policy and signing scope.

### SHA256

Check a downloaded file in its directory:

```powershell
Get-FileHash .\LocalASR-Setup-0.1.0-win64.exe -Algorithm SHA256
```

Generate a manifest for your own build with the existing helper, which refuses to overwrite its output:

```powershell
.\distribution\checksums.ps1 -Files .\dist\release-local\LocalASR-Setup-0.1.0-win64.exe -Output .\dist\release-local\SHA256SUMS-verified.txt
```

Phase 15 final RC: **1,303,059,102 bytes**; SHA256: `D148B3ADF46660E1EC878AB7DE6D7AA01A54DDEF01AEFEA7D861D87B75AB2836`. This hash identifies only the final RC, not arbitrary local builds. See the [artifact list](docs/development/PHASE15_ARTIFACTS.md).

### Project structure

```text
LocalASR/
├─ src/                   # Core, GUI, model catalog, version
├─ tests/                 # Automated and explicit manual tests
├─ distribution/          # build, spec, hooks, installer, checksums
├─ docs/                  # Architecture, installer policy, validation history
├─ .github/               # Issue / PR templates
├─ build.ps1
├─ requirements*.txt
├─ README.md
├─ README_EN.md
└─ LICENSE
```

Models, dist, build and local user data are not included in a Git clone. See [architecture](docs/ARCHITECTURE.md) and [contributing](CONTRIBUTING.md).

### Troubleshooting

| Problem | What to check |
| --- | --- |
| CUDA unavailable | Check app hardware diagnostics, NVIDIA drivers and CTranslate2 runtimes. Use CPU fallback if appropriate; torch-only detection is insufficient. |
| Model missing | Download through the model page; check the data directory, network and disk space. Do not manually mark a model complete. |
| Microphone unavailable | Check Windows default input, microphone permissions and other apps using the device. |
| System Audio unavailable | Windows uses WASAPI loopback. Check the default output device, volume/mute and PyAudioWPatch; protected audio may be unavailable. |
| Translation model missing | Translation is independent of ASR. Download the Chinese translation model and install translation dependencies. |
| Inno Setup missing | Install official Inno Setup or pass the actual ISCC.exe location with -Compiler. |
| PyInstaller failure | Check asr, dependencies, CPU wheel staging, CUDA runtimes, disk space, spec and output paths. Run the path check first and read build logs. |
