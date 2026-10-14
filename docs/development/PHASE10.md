> 历史记录：Phase 13 已将开发机路径通用化。文中的源代码 / validation / dist 路径相对仓库根目录；原始验证数据不随 Git 提供。当前开发步骤见 [README 开发者指南](../../README.md#开发者指南)。

# Phase 10 — Distribution optimization

## Scope and dependency audit

The Phase 9 stable build is preserved at `dist/LocalASR`. All Python/build/test commands run in Conda `asr`. No installed ASR/CUDA/translation package was upgraded or replaced. No model or user input/output was deleted. One-folder remains in use, with UPX disabled. No Installer or new product feature is part of this phase.

Before changes, direct project imports of torch were in `src/config.py` (default file ASR device), `src/hardware.py` (CUDA availability/GPU information), and `src/translation.py` (Marian CPU tensors/inference/model loading). Tests also use torch to exercise the translator. The complete source import graph, installed requirements and PE import tables are retained in `validation/phase10/baseline.json`.

- Actual ASR runs in faster-whisper/CTranslate2, not PyTorch. Their installed dependency metadata does not require torch. CTranslate2's converter modules nevertheless attempt optional imports of torch/Transformers when installed. Removing a direct hardware import therefore does **not** guarantee that no indirect torch import occurs.
- A separate Conda-asr process blocked all torch Python imports and successfully transcribed the existing short fixture using small on CUDA/float16. See `asr-without-torch.json` and `.log`. This proves the ASR inference boundary; it is not a no-torch full application and still supplies the CUDA DLLs used by CT2.
- MarianMTModel currently requires torch. The translator creates CPU tensors, runs `torch.inference_mode()` and explicitly moves the model to CPU. Transformers is not a substitute inference runtime. Deleting torch would break both file and realtime translation.
- Hardware and default file configuration now use CT2 CUDA detection. NVIDIA GPU identity/VRAM comes from the existing `nvidia-smi` probe. Recommendations already prioritized CT2 and still do. The legacy `HardwareInfo.torch_cuda` field remains nullable for compatibility, is not probed and is omitted from current diagnostics. If GPU VRAM is unavailable, the existing conservative policy chooses CPU rather than guessing.

## Baseline size

Exact total: **4,406,287,538 bytes**. Main EXE: **65,082,660 bytes**. Torch tree: **3,804,840,187 bytes**. CUDA DLLs across the build: **2,529,656,264 bytes** (overlaps the torch total). Transformers: **46,332,112 bytes**. CTranslate2: **61,877,152 bytes**. Tcl/Tk including its extension: **7,400,759 bytes**.

Top-20 files and top-20 component directories, sizes and DLL import tables are in `validation/phase10/baseline.json`. `distribution/audit_build.py` regenerates this audit for any build. Dominant individual files include torch_cuda.dll (957 MB), cuDNN precompiled engines (589 MB), cuBLASLt (473 MB), cuFFT (292 MB), cuSPARSE (276 MB) and torch_cpu.dll (251 MB). Sizes are decimal unless stated otherwise.

## Candidate design

Keep the same translation model and Transformers/Marian/OpenCC code. For the **build process only**, shadow torch with the official Windows CPython 3.11 **2.6.0+cpu** wheel, the same 2.6.0 upstream release as installed 2.6.0+cu124. This is not an engine migration or a change to the developer environment. The wheel is extracted into a hash-named staging directory; a fresh asr subprocess checks its exact version and `torch.version.cuda is None` before building.

Wheel: `torch-2.6.0+cpu-cp311-cp311-win_amd64.whl`, 206,540,444 bytes. Downloaded by pip from the official CPU index, SHA256 `24c9d3d13b9ea769dd7bd5c11cfa1fc463fd7391397156565484565ca685d908`. The wheel and extracted build staging are not copied into the application as archives/development resources.

An explicit CUDA manifest in `distribution/build_support.py` retains cuBLAS/cuBLASLt, CUDA runtime, the whole existing cuDNN family, NVRTC/JitLink and zlib support files from the already-tested CUDA runtime. They go into `_internal/cuda`, separate from CPU torch. This conservatively retains dynamic cuDNN engine dependencies instead of deleting DLLs solely because a short test did not load them. CT2's own packaged native libraries are unchanged. The runtime hook searches bundled locations only. System `nvcuda.dll`/NVML/display drivers are **not** distributed.

CPU torch eliminates the CUDA torch implementation and its CUDA-only math/profiling libraries (torch_cuda, c10_cuda, cuFFT, cuSPARSE, cuSOLVER, cuRAND, CUPTI, etc.) from the candidate. CT2 cuBLAS/cuDNN stay. The spec also excludes the unused Transformers optional audio stack librosa/numba/llvmlite; current audio decoding is faster-whisper/PyAV and realtime capture is sounddevice. A full real EXE verification is required before accepting this exclusion. Existing PyInstaller hooks continue to exclude torch static `.lib` archives and headers. Notice collection now avoids unrelated Python files whose names merely contain “license”.

Transformer lazy-import source collection and torch's standard hooks are retained rather than aggressively trimming tens of MB of dynamic Python imports. Models, caches, notebooks and the vendor wheel are not app resources.

## Build and rollback

Initial CPU wheel download only (does not install anything):

```powershell
conda run -n asr python -m pip download --no-deps --only-binary=:all: --index-url https://download.pytorch.org/whl/cpu "torch==2.6.0+cpu" --dest distribution/vendor
```

```powershell
.\build.ps1 -Variant optimized
.\build.ps1 -Variant full
```

Optimized writes `dist/LocalASR-Optimized`; a new full CUDA-torch build writes `dist/LocalASR-Full`. Each has a separate `build/<variant>` work directory. Only that variant's generated paths are cleaned. Neither operation deletes the original Phase 9 `dist/LocalASR`. `build-provenance.json` records the runtime choice and wheel hash; App Version stays unified in app_version.py. The active Conda environment still has the original GPU torch.

Use `distribution/validate_packaged.ps1` with `-BuildDirectory` and `-ReportDirectory` to run the full copied EXE/model/audio isolation check. It covers GUI/first-run, both ASR models on GPU, all exports, local translation/bilingual DOCX, actual microphone start/stop and timed realtime replay, plus offline startup and controlled downloader checks. `distribution/measure_startup.ps1` records first-window and startup-probe timings in fresh processes. Windows disk cache is not cleared: these are process-cold/warm-cache observations, not reboot-cold benchmarks.

## Alternatives assessed

- **No-torch full build:** rejected; current translation requires torch. No misleading no-torch full candidate is produced.
- **CTranslate2 Marian conversion:** technically supported upstream, but changes model format, tokenizer/target-prefix integration, decoding behavior and quality validation. Deferred under this phase's prohibition on a risky translation-engine migration.
- **Optional translation component:** feasible later with a separately launched CPU runtime and versioned IPC; the realtime translator already uses a separate process. File translation still runs in-process, and distribution/loading/version coordination would need work. No plugin/component system was introduced for this audit.
- **ASR-only build:** not a release candidate because it removes a current core capability. The blocked-torch inference probe establishes the boundary without maintaining an extra incomplete app.
- **Aggressive DLL removal/UPX/one-file:** rejected for native compatibility and startup reliability. No system driver was bundled.

## Sources

- [PyTorch official previous-version CPU builds](https://docs.pytorch.org/get-started/previous-versions/)
- [faster-whisper 1.2.1 runtime and CUDA requirements](https://github.com/SYSTRAN/faster-whisper/tree/v1.2.1)
- [CT2 4.8.1 CUDA implementation](https://github.com/OpenNMT/CTranslate2/blob/v4.8.1/src/cuda/utils.cc)
- [CT2 Transformers/Marian support](https://opennmt.net/CTranslate2/guides/transformers)

## Final acceptance — 2026-10-10

Phase 10 is complete. Candidate v2 is accepted as the current standalone build at **`dist/LocalASR-Optimized/LocalASR.exe`**. The original `dist/LocalASR` remains intact for rollback. The accepted EXE SHA256 is `4FC8CAF2F5C4BD1C02CA4410A4B51A8FE40CF4D52304878382238D97546A06E3`; `dist/standalone-release.json` binds the decision to this binary and the validation evidence. A future rebuild must be validated again.

### Exact size comparison

| Component (bytes) | Phase 9 stable | Candidate v1 | Candidate v2 |
| --- | ---: | ---: | ---: |
| Total | 4,406,287,538 | 3,352,397,983 | 2,494,371,015 |
| torch directory | 3,804,840,187 | 900,077,487 | 317,392,735 |
| CUDA DLLs across directories | 2,529,656,264 | 2,283,838,416 | 1,701,153,664 |
| CTranslate2 | 61,877,152 | 61,877,152 | 61,877,152 |
| Transformers / Marian code | 46,332,112 | 46,332,112 | 46,332,112 |
| Tcl / Tk | 7,400,759 | 7,400,759 | 7,400,759 |

CUDA and torch rows overlap; they must not be added. Model weights are external and excluded. V2 saves **1,911,916,523 bytes (43.39%)** versus stable. Compared with v1, **10 duplicate DLL copies totaling 858,026,968 bytes** were removed. The build only deduplicates entries resolving to the same source file, retaining canonical copies in `cuda/` or `torch/lib/`. Post-build SHA256 checks compare each v1 alias, v1 canonical copy and retained v2 copy. Different-source/version same-name DLLs are not merged. See DLL proof（本地证据：`validation/phase10/dll-deduplication-proof.json`） and all three builds' top 20 files and directories（本地证据：`validation/phase10/SIZE_COMPARISON.md`）.

CPU torch remains essential for Marian inference. CUDA runtime retained for CT2 includes cuBLAS/cuBLASLt, CUDART, the complete existing cuDNN family (advanced, CNN, graph, heuristic, ops and engine DLLs), NVRTC/builtins, nvJitLink and zlib support. CT2's own libraries remain unchanged. No CUDA fallback or missing-DLL error occurred in v2 validation.

### Actual packaged EXE validation

The actual v2 EXE and existing models were copied outside the repository. Child processes had Windows-only PATH, no Conda/Python environment, an empty Hugging Face cache and isolated user data. Loaded-module auditing found no repository or Anaconda dependencies. Evidence is in candidate-v2（本地证据：`validation/phase10/candidate-v2/`）, with execution logs in `validation/phase10/packaged-v2.log`.

- GUI creation, hardware detection (CT2 reports one CUDA device), Model Registry, first-run setup and diagnostics passed.
- The existing 11.235-second synthetic English fixture passed file ASR with **large-v3 CUDA/float16**. TXT, DOCX, JSON, SRT and VTT were produced. Completion validation passed and correctly rejected a missing VTT.
- Real local Marian translation passed using CPU torch, Transformers, SentencePiece and OpenCC resources. Three aligned segments and bilingual DOCX/JSON were verified. English and Chinese text matched the Phase 9 result for the same fixture (`output-comparison.json`).
- Realtime **small CUDA/float16**, WebRTC VAD and timed audio replay passed: three nonempty finals and three aligned Chinese translations, no errors or dropped audio/translations, queues drained.
- PortAudio enumerated 32 device entries; the actual default microphone captured frames and completed two start/stop cycles. This verifies device lifecycle, **not human speech recognition quality**. Recognition/translation validation used repeatable synthetic speech replay.
- Offline startup passed with sockets blocked in the main validation process, offline flags and local-only model loading in spawned workers. Empty-profile startup displayed missing-model guidance. This is controlled offline validation, not physical network disconnection.
- Diagnostics privacy checks passed. Both validation runs exited with code zero; queues/workers shut down and the process audit found no remaining candidate EXEs.

### Timing observations

Windows file cache was **not cleared**. Each startup probe used a fresh process and empty user profile; these are not reboot-cold benchmarks.

| Measurement | V2 observation |
| --- | --- |
| Initial copied-build run: entry / GUI created / GUI ready | 1.276 / 1.805 / **21.269 s** |
| Repeated startup: first visible window | 0.727 / 0.641 s |
| Repeated startup: environment check complete / GUI ready | 5.931 / 4.664 s |
| large-v3 model loading | 5.527 s |
| small model loading | 1.017 s |
| Speech end to English final, three replay segments | 0.813 / 0.859 / 0.797 s |
| English final to Chinese ready | 8.312 / 3.984 / 0.469 s |
| Speech end to Chinese ready | 9.125 / 4.843 / 1.266 s |

The first translation includes model/process initialization; the next translation waits in the queue. Stable comparison probes showed first windows at 1.068 / 0.599 s and startup-probe completion at 6.323 / 4.229 s. Stable lacks the new internal ready timer, so these are not identical measurements. The initial 21.269-second candidate readiness remains an observed limitation; the later faster runs do not establish a universal startup improvement. Raw timings are in `candidate-v2-startup`, `baseline-startup` and `candidate-v2/startup.json`.

### Regression and release decision

Full Conda `asr` regression: **196 tests passed in 19.528 seconds**, recorded in regression-final.txt（本地证据：`validation/phase10/regression-final.txt`）. Packaged checks above are additional to that count. Installed development versions remain unchanged, including torch 2.6.0+cu124, CTranslate2 4.8.1 and faster-whisper 1.2.1.

All required acceptance gates passed, so v2 is selected as the current standalone build. No installer, engine replacement, aggressive native compression, further speculative DLL deletion or Phase 11 work was performed.

### Changed files and remaining limits

Runtime changes: `src/config.py`, `src/hardware.py`, `src/diagnostics.py`; packaged validation instrumentation: `src/packaged_check.py`. Build changes: `build.ps1`, `distribution/build.py`, `build_support.py`, `LocalASR.spec`, `runtime_hook.py`, `notices.py`. Audit/validation tools: `distribution/audit_build.py`, `probe_asr_without_torch.py`, `validate_packaged.ps1`, `measure_startup.ps1`, `verify_deduplication.py`, `compare_builds.py`. Tests: `tests/test_hardware.py`, `tests/test_distribution_optimization.py`. Documentation: `README.md`, `PHASE10.md`; generated evidence: `validation/phase10/` and `dist/standalone-release.json`.

No clean Windows machine, CPU-only machine, other GPU, long-duration session or human bilingual microphone recognition test was completed in this phase. Automated real Tk-window checks are not a new manual visual usability test. Existing signing and public-release licensing checks remain pending. The standalone folder excludes model weights and still requires separately installed models. These limits do not invalidate the measured local packaged acceptance, but must not be represented as broader compatibility certification.


