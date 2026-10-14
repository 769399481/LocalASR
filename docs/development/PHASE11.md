> 历史记录：Phase 13 已将开发机路径通用化。文中的源代码 / validation / dist 路径相对仓库根目录；原始验证数据不随 Git 提供。当前开发步骤见 [README 开发者指南](../../README.md#开发者指南)。

# Phase 11 — System Audio and floating subtitles

## Scope and status

Windows implementation, regression, final packaged core checks and 30-minute real system-output capture are complete. **Phase 11 NOT COMPLETE: browser/local-video and exhaustive physical overlay/hotkey interaction checks remain unverified.** Do not interpret a missing or interrupted validation as PASS. Phase 10 remains the formal rollback build at `dist/LocalASR-Optimized`; its EXE SHA256 remains `4FC8CAF2F5C4BD1C02CA4410A4B51A8FE40CF4D52304878382238D97546A06E3`.

No installer, UI redesign, AI summary, cloud service, speaker diarization, per-application capture or Phase 12 work is included.

## Architecture

`audio_sources.py` defines the AudioSource lifecycle, capability/permission model, source factory and streaming PCM conversion. The existing Microphone adapter remains in `realtime_audio.py`. `WindowsSystemAudioSource` lives in its own module; `MacSystemAudioSource` explicitly rejects unsupported native capture. Application selection is reserved in the capability model and never silently falls back to system capture.

The selected source supplies the existing bounded realtime queue, WebRTC VAD, utterance assembler, small CUDA/float16 ASR, final-only translation, RealtimeDocument, recovery writer and Exporter. System audio does not open or mix the microphone. It captures the default Windows output endpoint; applications explicitly routed elsewhere are outside that endpoint.

Windows capture uses PyAudioWPatch 0.2.12.8 and WASAPI loopback. This is the only new product dependency, installed without dependencies in Conda `asr`; existing ASR/CUDA/translation packages were not upgraded. The adapter receives PCM16 at the endpoint rate/channel count. Actual hardware reports 48 kHz stereo. Existing PyAV performs stateful resampling after float-domain mono downmix, producing exactly 480-sample (30 ms), 16 kHz mono PCM16 frames. Tests also cover 44.1 kHz and silence. Resampler history persists across input callbacks.

The native callback only copies into a bounded 100-block queue. Conversion and default-device checks run on a dedicated owner thread. Overflow stops visibly rather than splicing missing time into a valid timeline. The Core retains its existing bounded queue and overflow handling. A default-output name change, inactive stream, startup error or callback failure stops capture with a user-facing message; restarting creates a fresh source and binds the current default output. No automatic cross-device mixing is attempted.

## Overlay and hotkeys

`SubtitleOverlay` is an independent Tk Toplevel projection of existing events, not a document store. It keeps at most two final segments, plus a replaceable English partial (showing only the latest final while a partial is present). Final text cannot be overwritten by a stale partial. Late translations update matching segment IDs; a small bounded early-result map handles callback ordering. Full history remains in RealtimeDocument and recovery files.

English, 中文 and Bilingual modes are supported. Translation still runs only for finals. The window is borderless, topmost and draggable, with width, font, opacity, color-key transparent background and Top/Bottom/Custom positioning. Windows alpha applies to the whole window, including text; it is not a separately composited opaque-text background. Watch mode uses layered/transparent/no-activate native styles and hides editing controls. The main page can always return to Edit mode. Exclusive fullscreen surfaces are not guaranteed to permit overlays.

Native operations are confined to `desktop_platform.py`. Monitor-relative work areas and signed coordinates are used; preference persistence includes x/y/width/mode. Content growth clamps the lower edge to the current work area. Display history may be visually clipped for exceptionally long content at very large fonts; the saved document remains complete.

Global hotkeys are optional and disabled by default: Ctrl+Alt+S start/stop realtime, H show/hide, L cycle language, E Edit/Watch. A dedicated thread owns RegisterHotKey and WM_HOTKEY dispatch; a bounded command queue is polled on the Tk thread. Conflicts are reported, repeated registration closes the previous registration, and shutdown unregisters all keys. A file job is not stopped by the realtime shortcut.

## Translation prewarm

When a translated realtime session starts, its existing translation worker starts Marian/OpenCC on CPU and performs one private warmup inference. It does not emit a transcript/translation event, alter segment numbering, or save a fake segment. GUI and ASR remain independent. App launch alone does not load the translator. Failure/timeouts release the warmup child and leave English ASR running.

In the 30-minute source run, prewarm took **13.765 s**; the first final-to-Chinese delay was **7.406 s**, versus the retained Phase 10 first observation **8.312 s**. This is not a controlled performance comparison and does not show elimination of cold-start delay: speech can finish before warming completes. After the first three segments, median translation delay was **0.375 s**, p95 **0.594 s**. The model was reused, not reloaded per segment.

## Valid completed 30-minute test

The interrupted agent turn did not terminate the test. Retained report records **1807.109 seconds**, **315 finals**, **315 translations**, all five exports, clean shutdown and no errors. Native Windows process inspection on resumption found no leftover validation Python/LocalASR processes.

Audio came from repeatedly playing the existing authored synthetic English WAV through the real Windows default output, then capturing that output. No source injection and no microphone were used. The test does not certify human speech accuracy, all media players or all meeting apps.

| Metric | Result |
| --- | --- |
| Captured frames | 60,209 |
| Dropped audio frames / samples | 0 / 0 |
| Dropped final utterances / translations | 0 / 0 |
| Audio / final / translation queue peak | 1 / 1 / 2 |
| Backlogs at shutdown | 0 |
| Superseded partial jobs discarded | 107; final content unaffected |
| English final latency median / p95 / max | 0.782 / 0.984 / 1.110 s |
| Speech end to Chinese median / p95 / max | 1.172 / 1.547 / 8.265 s |
| RSS process-tree start / end / peak | 1,938,137,088 / 1,845,334,016 / 1,944,088,576 bytes |
| Private bytes start / end / peak | 5,022,175,232 / 5,076,369,408 / 5,145,309,184 bytes |
| CPU approximate machine share min / median / p95 / max | 1.80 / 7.69 / 11.05 / 13.97% |

Memory/CPU use a separate native Windows observer because psutil is not installed; the in-app `observer: psutil unavailable` entries are not resource measurements. There are 163 two-process samples, from 18:27:26 to 18:54:47 on 2026-10-10 (UTC+8), starting about 150 seconds into capture. Shutdown's one-process sample is excluded. CPU is normalized by 16 logical CPUs. Build and regression work ran concurrently early in the test. These observations show no sustained runaway growth in this run, not proof against every long-session leak. A one-hour test was not performed.

Recovery JSON was parsed through the real RealtimeDocument loader and compared with exported session JSON: all 315 original texts, translations and timestamps match. Evidence: `validation/phase11/continuous-30min/`, `process-samples.csv` and `stability-summary.json`.

## Verification ledger

- Full automated regression after current fixes: **233 PASS**, 22.914 seconds (`regression-final.txt`). Includes native hotkey registration/conflict/release and real Tk widgets, plus mocked device loss/route change. These are distinct from physical UI actions.
- Short real system-output run: 9 bilingual segments, all five formats, no audio/translation drops. A transient Windows report-file sharing failure occurred after export in the first short harness; report replacement now retries. The later complete long test is the acceptance evidence.
- Final packaged candidate: full existing file/microphone/CUDA/translation/export/offline/diagnostic regression passed (`packaged-final/`, `packaged-final.log`). The EXE ran from an isolated temporary directory with no Conda/Python on PATH and local model resources. Both large-v3 and small CUDA/float16 passed; actual microphone capture was checked, not microphone speech-quality certification. This is not a clean-Windows hardware certification.
- Final packaged system-audio meeting-style run: **PASS**, 85.688 seconds, 31 finals / 31 translations, all five exports, no reported errors, clean shutdown and hotkeys released (`packaged-system/report.json`). The authored fixture uses one English synthetic voice with alternating pitch/rate and short pauses; it does not represent two distinct human speakers. Playback went through real Windows output, not direct audio injection into ASR.
- Browser video: **NOT VERIFIED**. The public W3C Sintel MP4 reached readyState 4 and visible playback progress, but subsequent browser control timed out. The external-player capture recorded zero segments in 180.594 seconds (`packaged-browser/report.json`, passed=false). Browser playback progress alone is not evidence of a successful browser-to-ASR chain. Local video fixture was created but actual native-player validation remains pending. A local browser page was blocked by browser security policy; no bypass was attempted.
- Overlay/core event projection and native hotkey registration/release pass automated and packaged harness checks. Exhaustive physical drag, positioning, opacity, font, click-through, mode/show-hide and keyboard chord interaction remain **NOT VERIFIED**. Native app interaction approval timed out; the pending approval request was not treated as approval. Automated native message dispatch is not physical keyboard testing.
- Headphone-specific validation: **NOT TESTED**, no headphones available; no further hardware request.
- Native Zoom/Teams/Meet validation: **NOT PERFORMED**. A meeting-style test is not native meeting-app certification.
- Multi-monitor physical validation: **NOT PERFORMED**; Windows reports one physical monitor. Signed-coordinate/persistence logic has tests.

Controlled output disappearance/configuration-change tests pass with simulated backend state: user-facing failure, capture stop, and a fresh default-output binding on restart. Physical device removal was not performed. Do not generalize this to every Windows audio driver.

## Remaining acceptance work and final verdict

1. Complete actual browser video and native local-video playback through system capture, with resulting English/Chinese session evidence.
2. Complete the full physical overlay interaction checklist and real keyboard shortcuts against this exact final EXE, including watching an underlying application receive clicks in Watch mode.
3. Recheck shutdown after those interactive runs. The completed long and packaged runs already record clean shutdown; missing interaction evidence is not a code-test failure.

Headphones, physical multi-monitor, native Zoom/Teams/Meet, macOS hardware and the optional one-hour run remain explicitly untested. No extra hardware is requested. These exclusions must not be advertised as tested features.

The candidate remains separate and **is not promoted to the formal standalone release**. Phase 10 stays available unchanged. Work stops within Phase 11; no Phase 12, installer or product UI polish is included.

## macOS and capture limitations

**macOS architecture prepared; native backend and hardware validation remain pending.** PermissionStatus includes granted, denied, not_requested, restricted and unsupported. The macOS system source reports unsupported cleanly. The native implementation must choose ScreenCaptureKit or Core Audio process taps, implement permission requests and denial/restriction handling, configure usage descriptions/entitlements as appropriate, and validate native overlay/hotkeys on Mac hardware. No macOS package or native implementation is claimed.

System output may include notification sounds/music and any app on the selected default endpoint. Existing WebRTC VAD/Whisper filtering is retained; no new music classifier or promise of zero false captions is introduced. Partially protected content and special audio routes may not be capturable. No DRM bypass is implemented.

## Build and reproducibility

All Python, tests and builds use Conda `asr`. Build only the isolated candidate:

```powershell
conda run -n asr --no-capture-output python distribution/build.py --variant optimized --phase11
conda run -n asr --no-capture-output python -m unittest discover -s tests -q
```

Output: `dist/LocalASR-Phase11`. Work: `build/phase11`. The Phase 10 optimized CPU-torch plus explicit CT2 CUDA runtime manifest and same-source DLL deduplication are retained. PyAudioWPatch binaries/metadata are collected. Whole-directory distribution is still required; model weights remain external.

Final size before acceptance: **2,494,297,628 bytes**, effectively unchanged from Phase 10's 2,494,371,015 bytes (net −73,387 bytes; packaging/compression also varies). No further trimming was attempted.

Final candidate EXE SHA256: `992B748EA9FB6C462B9177D7A0D0A7DE05BA36F9C30338835C8D1C2FA72DC5E3`.

Resumption changes were limited to narrow overlay-toolbar layout/height handling, realtime hotkey state handling, destroyed-widget cleanup, validation harness/audit/fixtures and regression tests. Primary affected files: `src/subtitle_overlay.py`, `src/gui.py`, `src/system_audio_check.py`, `tests/test_system_audio.py`, `tests/test_gui.py`, `distribution/phase11_audit.py`, `distribution/make_phase11_video.py`, this report and README. Earlier Phase 11 architecture was retained.

Sources used for platform boundaries: [PyAudioWPatch example](https://github.com/s0d3s/PyAudioWPatch/blob/master/examples/pawp_record_wasapi_loopback.py), [Apple ScreenCaptureKit](https://developer.apple.com/documentation/screencapturekit), [Apple Core Audio taps](https://developer.apple.com/documentation/coreaudio/capturing-system-audio-with-core-audio-taps), [W3C public HTML video sample](https://www.w3.org/2010/05/video/mediaevents.html).


