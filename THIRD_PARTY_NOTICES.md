# Third-party notices — release review required

LocalASR original code and project content are source-available under PolyForm Noncommercial License 1.0.0. Commercial use requires a separate license; contact yehao769399481@gmail.com. This license does not replace or restrict the licenses of the third-party components below.

| Component | Version | Upstream license | Source |
| --- | --- | --- | --- |
| faster-whisper | 1.2.1 | MIT | https://github.com/SYSTRAN/faster-whisper |
| Whisper / converted small, large-v3 weights | pinned model_catalog.json revisions | MIT | https://github.com/openai/whisper ; https://huggingface.co/Systran |
| CTranslate2 | 4.8.1 | MIT | https://github.com/OpenNMT/CTranslate2 |
| PyTorch (Marian CPU inference; development CUDA build supplies ASR runtime DLLs) | optimized: 2.6.0+cpu; development: 2.6.0+cu124 | BSD-3-Clause and bundled notices | https://github.com/pytorch/pytorch/blob/v2.6.0/LICENSE |
| python-docx | 1.2.0 | MIT | https://github.com/python-openxml/python-docx |
| sounddevice / PortAudio | 0.5.4 / bundled | MIT / PortAudio license | https://github.com/spatialaudio/python-sounddevice ; https://www.portaudio.com/license.html |
| webrtcvad-wheels | 2.0.14 | MIT wrapper; WebRTC BSD-style notices | https://github.com/daanzu/py-webrtcvad-wheels |
| Transformers / Marian implementation | 5.13.1 | Apache-2.0 | https://github.com/huggingface/transformers |
| Helsinki-NLP/opus-mt-en-zh | pinned revision in model_catalog.json | Apache-2.0 model card | https://huggingface.co/Helsinki-NLP/opus-mt-en-zh |
| OpenCC Python reimplementation | 0.1.7 | Apache-2.0 | https://github.com/yichen0831/opencc-python |
| SentencePiece | 0.2.2 | Apache-2.0 | https://github.com/google/sentencepiece |
| Sacremoses | 0.1.1 | MIT (installed distribution LICENSE) | https://github.com/hplt-project/sacremoses |
| Python / Tcl / Tk | build environment versions | PSF / Tcl-Tk licenses | https://www.python.org/psf/license/ ; https://www.tcl.tk/software/tcltk/license.html |
| PyInstaller bootloader | 6.22.3 | GPL with bootloader distribution exception | https://pyinstaller.org/en/stable/license.html |
| tkinterdnd2 (native file drag/drop wrapper) | 0.6.3 | MIT | https://github.com/Eliav2/tkinterdnd2/blob/master/LICENSE |
| TkDnD (bundled native drag/drop extension) | see bundled package | Tcl/Tk-style license; retain bundled license.terms | https://github.com/petasis/tkdnd |
| PyAudioWPatch (WASAPI loopback capture) | 0.2.12.8 | Apache-2.0 wrapper; bundled PortAudio notices also apply | https://github.com/s0d3s/PyAudioWPatch |
| NumPy (PCM arrays) | 2.4.4 | BSD-3-Clause plus bundled notices | https://github.com/numpy/numpy |
| PyAV (audio/video decoding) | detected build: 18.0.0 | BSD-3-Clause wrapper; FFmpeg separately reviewed below | https://github.com/PyAV-Org/PyAV |
| FFmpeg libraries (bundled decoding) | actual PyAV wheel | REVIEW actual build: LGPL/GPL and corresponding-source obligations | https://ffmpeg.org/legal.html |
| NVIDIA CUDA / cuBLAS / cuDNN / NVRTC / JitLink (ASR GPU runtime) | selected build DLLs | NVIDIA proprietary redistribution terms; REVIEW shipped versions | https://docs.nvidia.com/cuda/eula/index.html ; https://docs.nvidia.com/deeplearning/cudnn/backend/latest/reference/eula.html |
| ONNX Runtime (faster-whisper VAD) | detected build: 1.27.0 | MIT and bundled notices | https://github.com/microsoft/onnxruntime |
| tokenizers / safetensors / huggingface_hub (tokenization, serialization, model ecosystem) | generated inventory | Apache-2.0; verify shipped distribution notices | https://github.com/huggingface/tokenizers ; https://github.com/huggingface/safetensors ; https://github.com/huggingface/huggingface_hub |
| lxml (DOCX XML) | detected build: 6.1.1 | BSD-3-Clause plus libxml2/libxslt notices | https://lxml.de/copyright.html |
| pyinstaller-hooks-contrib (build hooks) | 2026.8 | Apache-2.0 / GPL-2.0-or-later by file; build tool | https://github.com/pyinstaller/pyinstaller-hooks-contrib |

The build copies installed third-party license/notice files without modifying them into `_internal/third_party_licenses/`, plus a version/license inventory. This inventory includes build-environment packages and is a superset, not an SBOM proving exactly which code is shipped.

PyTorch includes NVIDIA CUDA/cuDNN/cuBLAS redistributables subject to NVIDIA license terms; bundled license texts must remain with the distribution. PyAV may bundle FFmpeg components under LGPL/GPL terms depending on its build. Verify the actual binary build flags and corresponding-source obligations before public distribution. Bundled transitive dependencies also require a release review. This document does not relicense third-party code or claim legal clearance.

Models are downloaded separately from their pinned upstream repositories with their model cards. No model weights are embedded in the standalone package. See `distribution/third_party_licenses/inventory.json` after building for detected installed dependency versions. Generated notices and vendor runtimes are excluded from source Git, but notices must remain in a distributed binary package. Phase 14 adds an Inno Setup installer; all third-party notices remain in the installed application.

## Model license verification — 2026-10-12

| Exact model | Pinned revision / evidence | License status |
| --- | --- | --- |
| Systran/faster-whisper-small | [Pinned card](https://huggingface.co/Systran/faster-whisper-small/blob/536b0662742c02347bc0e980a01041f333bce120/README.md) | MIT, verified card metadata; converted OpenAI Whisper weights |
| Systran/faster-whisper-large-v3 | [Pinned card](https://huggingface.co/Systran/faster-whisper-large-v3/blob/edaa852ec7e145841d8ffdb056a99866b5f0a478/README.md) | MIT, verified card metadata; converted OpenAI Whisper weights |
| Helsinki-NLP/opus-mt-en-zh | `408d9bc410a388e1d9aef112a2daba955b945255`; [upstream card](https://huggingface.co/Helsinki-NLP/opus-mt-en-zh) plus locally preserved README matching catalog Git blob hash | Apache-2.0, verified upstream and pinned local card |

The model catalog records revisions and file integrity metadata, not a replacement license grant. Keep the model cards with separately downloaded models. [OpenAI Whisper license](https://github.com/openai/whisper/blob/main/LICENSE) is distinct from the faster-whisper software license.

This is a preparation inventory, not a complete binary SBOM or legal clearance. Installed license files support the dependency labels above; public model cards and tkinterdnd2 upstream were checked for this phase. Final binary release still requires review of actual transitive native components, FFmpeg build flags/source obligations and NVIDIA redistribution terms. No long license text is copied here.


## Installer and compatibility review (Phase 14)

Inno Setup 6.7.3 is a build/distribution tool under its own [Inno Setup License](https://jrsoftware.org/files/is/license.txt). It permits use for commercial applications, subject to preserving its notices and not misrepresenting origin. LocalASR does not relicense Inno Setup.

MIT/BSD/Apache-2.0 components listed above (faster-whisper, CTranslate2, PyTorch, Transformers, Marian, OpenCC, tkinterdnd2, WebRTC wrapper/notices, sounddevice/PortAudio, python-docx) retain their original licenses and notices. No obvious obligation in those license families alone requires LocalASR's original source to use the same license; this is an engineering inventory, not legal advice or a blanket compatibility clearance.

[PyInstaller's bootloader exception](https://pyinstaller.org/en/stable/license.html) permits bundled applications under other licenses while requiring dependency compliance. PyInstaller modifications, if any, have their own obligations. We do not modify its bootloader.

**LEGAL REVIEW RECOMMENDED before public binary distribution**: inspect actual PyAV/FFmpeg build flags and LGPL/GPL corresponding-source/relinking obligations; CUDA/cuDNN/cuBLAS and other NVIDIA redistribution permissions; bundled Microsoft VC runtime rights; and the full set of native/transitive notices. A PolyForm license for LocalASR does not supersede any of these obligations. Third-party copyright texts are not removed or changed.
