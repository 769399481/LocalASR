> 当前发布信息（Phase 15）：LocalASR 0.1.0 RC；项目 https://github.com/769399481/LocalASR；PolyForm Noncommercial 1.0.0 / Source-available。下文为历史阶段记录，其中当时未确定的地址或许可不代表当前状态。

> 历史记录：Phase 13 已将开发机路径通用化。文中的源代码 / validation / dist 路径相对仓库根目录；原始验证数据不随 Git 提供。当前开发步骤见 [README 开发者指南](../../README.md#开发者指南)。

# Phase 9 — Standalone Windows build and packaged validation

## Audit and decisions

Before packaging, source review found GUI/config/log/recovery/output and translation defaults rooted in the source tree; small was discovered from the developer's HF cache; GUI entry lacked frozen multiprocessing dispatch. Native dependencies include CT2/Whisper, torch CUDA DLLs, PyAV, sounddevice/PortAudio, WebRTC VAD, SentencePiece/OpenCC/Transformers. No models or user files were removed.

PyInstaller onedir was selected over Nuitka: existing Python remains unchanged, mature Tk/torch hooks, no new C compiler/toolchain, visible native dependency layout and simpler debugging. The inference work already runs in native libraries, so compiling GUI Python is not a priority. See [PyInstaller usage](https://pyinstaller.org/en/stable/usage.html) and [Nuitka compiler requirements](https://nuitka.net/user-documentation/user-manual.html#c-compiler).

Scope was narrowed before any Installer was compiled. Previously prepared installer.iss and local tool files are deferred historical artifacts, unused by the active build. No Installer, upgrade or uninstall validation is claimed. Packaging additions were installed only into Conda asr: PyInstaller 6.22.3 and hooks-contrib 2026.8 plus their build dependencies. ASR/CUDA/translation versions were not upgraded.

## Build

Run `.\build.ps1`. Version comes solely from src/app_version.py; build generates matching Windows version metadata. Generated build/ and dist/LocalASR are cleared with path checks; models/input/output/recovery are untouched. Weights are forbidden in output validation. The build script has no Installer option.

The standalone directory contains LocalASR.exe and _internal/ with Python 3.11, Tcl/Tk, extension modules, CPU/GPU libraries, model download catalog and third-party notices. Distribute the whole directory, not only the executable. The runtime adds only bundled DLL locations, and frozen multiprocessing dispatch runs before GUI imports. Custom hooks handle the installed webrtcvad-wheels distribution and the required Marian modules/Transformers metadata.

Copy the whole standalone directory to run it elsewhere. No public Release has been uploaded, and no signed executable is claimed.

## Paths and first run

Frozen builds write config, logs, recovery, models, downloads, cache and default output under %LOCALAPPDATA%/LocalASR; output can be changed in the GUI. Source runs retain the original project data paths. LOCALASR_DATA_DIR provides a testing/developer override. Old source data is not silently moved or copied.

The existing Phase 8 detector and recommender run in the background. First-run setup is a single short panel: computer check → recommended Fast/Best Quality and Balanced → selected model downloads → continue. It can be skipped. Translation is optional; enabling it without its model opens a language-model download prompt. Existing project/user models and local HF cache remain reusable, but a clean installation does not require any developer cache.

The model registry remains offline. Managed models use models/<id>/<pinned-revision> with an installed.json marker and exact file sizes. Legacy local directories remain supported. No large model is loaded merely for startup validation.

## Download reliability

model_catalog.json pins upstream commit IDs, file sizes, LFS SHA256 or Git blob SHA1 for all required files. Only the required PyTorch/CT2 weights are included in each download, not TensorFlow/Flax alternatives. Downloads go to a separate .partial staging directory; completed files are hashed, interrupted partial files use HTTP Range if supported, unsupported Range restarts that file. Completed verified files are reused on retry. A per-model OS file lock prevents concurrent app instances publishing the same model.

Disk check conservatively requires twice the model size plus 512MiB. All files must match pinned hashes before the installation marker and atomic directory publication. A corrupt previous managed directory is preserved under an incomplete suffix instead of being silently deleted. Cancel checks run during streaming and hashing; HTTP operations use 15-second timeouts. Download failures retain staging data and emit user-readable messages; no incomplete model is selectable. Startup does cheap marker/size checks, not multi-GB rehashing. Same-size post-install disk corruption therefore requires repair/re-download; it is not proactively detected every launch.

Model sizes: small about 0.486GB, large-v3 about 3.091GB, translation about 0.315GB. Download only connects to public Hugging Face endpoints; no audio/transcripts/API secrets are sent. Offline startup and installed-model use do not require network requests.

## Diagnostics and release preparation

About/Diagnostics shows the shared version and offers Copy/Save. It uses an allowlist: hardware, model IDs/installed flags, recommendation/quality choice, state and error count. It never dumps full settings, transcripts, input filenames, model paths or raw tracebacks. Detailed errors remain in local logs.

README starts with ordinary-user installation/use/storage/privacy; developer history is preserved in DEVELOPMENT.md. No fake GitHub URL is created because the project has no configured public release location. THIRD_PARTY_NOTICES.md lists core licenses and sources; build copies installed license files verbatim with an inventory. Main project LICENSE remains undecided. NVIDIA/PyAV and transitive binary distribution obligations still need review before public release.

## Validation

Validation results and artifact paths are recorded in validation/phase9. The opt-in --packaged-check entry opens the real Tk GUI, drives the existing file controller with a synthetic fixture, validates exports, exercises the actual microphone, then feeds timed synthetic audio through the existing realtime core and spawned translation process. It also checks first-run and controlled downloader failures. This developer-only entry writes validation settings; do not point it at real user data. It does not claim human speech recognition or clean Windows testing.

Clean Windows verification is prepared in distribution/CLEAN_WINDOWS_CHECKLIST.md. A development-machine run, even with Conda removed from PATH, is not a clean OS test.

## Verified result — 2026-10-10

- Repeated clean onedir build succeeded with PyInstaller 6.22.3 in Conda asr; latest build took about 259 seconds. Build log: validation/phase9/build-standalone.log.
- Output: dist/LocalASR; 6,286 files; **4,406,287,538 bytes (4.406 GB / 4.104 GiB)**. Torch occupies 3,804,840,187 bytes, followed by llvmlite 120,369,152, av.libs 65,593,344, CTranslate2 61,877,152, scipy 54,787,584 and Transformers 46,332,112. No model.bin or pytorch_model.bin is bundled. Large optional GUI/scientific backends were excluded in the spec; further aggressive pruning was deferred to preserve native reliability.
- The previous build failure was the default WebRTC hook asking for `webrtcvad` distribution metadata while the installed distribution is `webrtcvad-wheels`. The local hook fixes that exact mismatch. Marian hidden imports/data/metadata, freeze_support and bundled CUDA DLL search paths are explicit. The final runtime checks did not reveal further missing DLLs.
- Isolation launcher: distribution/validate_packaged.ps1. It copies the entire app and existing models to a new user temporary directory, copies the 11.235-second SAPI fixture, sets PATH to Windows directories only, removes Conda/Python environment variables, uses an empty HF cache and a separate LOCALAPPDATA. No model download is performed. Both full and missing-model EXE runs exited 0.
- Main-process module sampling recorded 317 loaded modules, all from the copied application or Windows. Bundled python311.dll, PortAudio, WebRTC, cuBLAS and cuDNN were actually loaded. The program, working directory, models and audio were outside <checkout>. The source checkout was not removed and the OS still has development tools installed: this proves tested-path independence, not a clean-machine certification.
- GUI automation inside the EXE instantiated both File and Realtime pages, saved config/logs in the isolated user directory, opened first-run, detected hardware and recognized all three copied models. A second empty user directory recognized none and showed the missing-model prompt without crashing.
- File ASR: real large-v3 CUDA/float16, 11.235-second synthetic English audio, Success. File work including translation took 12.12 seconds; batch including model loading 17.36 seconds. TXT/DOCX/JSON/SRT/VTT were generated. English retained; JSON contains all three aligned Chinese segments; DOCX contains Chinese. Complete manifest accepted; an isolated copy missing VTT was correctly incomplete.
- Translation: actual Marian/Transformers, SentencePiece and OpenCC on CPU; file translation complete, and spawned realtime process translated 3/3 finals. No fake translator was used for ASR/translation runtime verification.
- Realtime: PortAudio enumerated 32 device entries; actual default input started/stopped twice and captured frames. A timed synthetic replay then exercised WebRTC VAD, small CUDA/float16 and translation. Three nonempty finals and three translations aligned exactly; zero dropped audio frames, zero dropped translations/errors, queues drained. Both worker sets stopped; a separate process query found zero remaining validation EXEs. This is microphone capture/lifecycle plus synthetic replay validation, **not a human-speech microphone accuracy test**.
- Replay latencies by segment (seconds): ASR endpoint-to-final **0.859 / 0.875 / 0.843**; final-to-Chinese **8.563 / 4.156 / 0.516**; endpoint-to-Chinese **9.422 / 5.031 / 1.359**. First translation includes cold initialization; the second waits behind it. These are one short fixture's observations, not general performance guarantees.
- Offline validation blocks parent-process socket connections and uses HF/Transformers offline plus local-only model loading in the spawned process. Installed-model transcription/translation and empty-model startup succeeded. No physical network disconnect/firewall test was performed. Controlled downloader checks rejected offline/corrupt data, honored a cancellation request, retried successfully, and reused the validated installation without network. Real multi-GB HTTP interruption/resume was not retested.
- Diagnostics includes shared 0.1.0 version, Windows/CPU/RAM/GPU, device/compute modes, all three model flags and generic error summary. It contains no fixture text, audio, raw traceback or user paths. Local detailed logs remain separate.
- Full regression: **187 tests passed in 19.378 seconds**, including release paths, model paths, missing runtime/forbidden bundled weights and controlled download checks. Log: validation/phase9/regression-standalone.txt. Packaged validations are additional to those 187 tests.
- Window enumeration independently observed the copied LocalASR.exe main window. The Computer Use visual-inspection request then timed out waiting for app approval; therefore no screenshot/manual visual pass is claimed in this iteration. Prior automatic-review quota failure concerned an unexecuted small network probe; it was not a code failure, and it was not bypassed. The subsequent authorized build and packaged runs succeeded.

Evidence: validation/phase9/packaged.json, startup.json, isolation.json, diagnostics.json, shutdown.json, build-size.json, packaged-runtime.log and packaged-output/. Runtime copies and model copies remain in the temporary validation directory recorded in isolation.json; no original model/input/output data was deleted.

## Remaining limits and next development

No Installer was built. Clean Windows CPU-only and NVIDIA runs, physical offline behavior, human microphone bilingual accuracy, public binary license review/signing and broad long-session stability remain unverified. Translation cold start and literal wording are known product limitations, not addressed in packaging. Before major feature work, keep this build-and-smoke path as a regression gate, preserve separate Core/GUI layers and immutable ASR timestamps, then prioritize translation warm-up/quality and long-session resource tests. Keep Installer work deferred until primary features stabilize.



