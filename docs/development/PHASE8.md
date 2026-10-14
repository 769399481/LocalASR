> 历史记录：Phase 13 已将开发机路径通用化。文中的源代码 / validation / dist 路径相对仓库根目录；原始验证数据不随 Git 提供。当前开发步骤见 [README 开发者指南](../../README.md#开发者指南)。

# Phase 8 — Hardware Detection + Smart Defaults + UI Polish

本阶段保持 Tkinter/ttk、既有文件/实时 ASR、CPU 翻译和会话恢复架构。没有新增或升级依赖，没有下载模型。所有 Python 验证在 Conda `asr` 内执行。

## 启动与选择

GUI 启动后立即显示两页；后台检测 Windows、CPU、总 RAM、NVIDIA GPU/显存、PyTorch CUDA、CTranslate2 CUDA 设备与 CPU/GPU compute types。检查期间禁止开始 ASR，窗口继续处理事件。

`hardware.py` 返回不可变 `HardwareInfo`，分别使用 Windows 注册表/GlobalMemoryStatusEx、5 秒超时的隐藏 nvidia-smi、PyTorch 和 CTranslate2。探测失败写入结构化 errors 和日志，PyTorch CUDA 成功不等于 CTranslate2 可用。CUDA compute query 也不等于模型已经加载，实际初始化/推理仍有 CPU 回退。

`model_registry.py` 只读扫描项目 models、已有自定义路径及 HF 本地缓存（支持 HF_HUB_CACHE / HUGGINGFACE_HUB_CACHE / HF_HOME）。检查 model.bin 非空、config.json 可解析、tokenizer.json 存在，不调用下载器。注册 small、large-v3，记录 ID、显示名、路径、来源、近似权重大小、用途、安装状态、文件/实时兼容性、MIT 许可。当前约 0.484GB / 3.09GB 是权重文件体积，并非运行内存。

`recommendation.py` 是独立纯策略，可注入模拟硬件与模型清单：

| 页面 | 可用模式 | 内部映射 |
| --- | --- | --- |
| 文件 | Fast | 已安装 small |
| 文件 | Accurate | 已安装且硬件允许的 large-v3 |
| 实时 | Balanced | 已安装 small |

Auto 不是额外模型：文件优先 Accurate，否则 Fast；实时选 Balanced。当前模型数量不足以为每页提供三个不同档位，因此不展示重复/不可用档位。质量与 CUDA、compute type、模型路径分离，普通用户不操作内部参数。硬件变更导致旧手选档位不可用时回到 Auto 并提示；无适合模型则禁用对应开始按钮，恢复/导出仍可用。

## 资源依据与边界

以下是保守产品策略，不是所有机器的最低运行保证：

- [faster-whisper 官方 benchmark](https://github.com/SYSTRAN/faster-whisper#benchmark)：large-v2、FP16、beam 5、非批推理约 4525MB VRAM；small CPU int8 约 1477MB RAM，float32 约 2257MB。该 GPU 数据来自 RTX 3070 Ti，且模型是 large-v2，不能冒充本项目 large-v3 的跨机器测量。
- large-v3 GPU 门槛使用 5.5GiB 总 VRAM、8GiB RAM、float16 支持：由上述同量级 large 基准留出约 1GiB 余量，并由当前 6GiB 机器的真实 large-v3 文件测试佐证。8GiB RAM 是主机加载和系统余量的保守门槛，不是官方最小值。
- small GPU 门槛 2GiB：参考 [Whisper 官方 small 约 2GB 的内存量级](https://github.com/openai/whisper#available-models-and-languages)，作为本阶段保守筛选值；该表不是 CTranslate2 实测。本机已长期使用 small。低于 2GiB 或显存未知时选择 CPU。
- small 要求已知总 RAM 不低于 4GiB：在 CT2 small CPU 上述实测占用之外为 Windows/应用保留空间。RAM 探测失败时允许 small 尝试运行并在日志保留探测错误；不允许推荐 large。
- [CTranslate2 compute type 查询](https://opennmt.net/CTranslate2/python/ctranslate2.get_supported_compute_types.html) 决定精度选项，GPU 优先 float16、int8_float16、int8；无这些支持则 CPU。CPU 按支持情况选择 int8、int8_float32、float32。

不自动启用 large int8、medium 或其他未经本阶段验证的档位，不下载新模型。注册表的 large-v3 实时兼容性为 false 是产品策略，不表示 Whisper 技术上不能实时处理。

## 回退和线程

GUI 文件任务显式传入推荐设备、精度、模型。实时任务取消原先硬编码 cuda，传入独立 RealtimeConfig；只有 GUI 开启新的 allow_cpu_fallback，既有 CLI 的显式设备语义保留。GPU 初始化失败或延迟发生的 CUDA/cuBLAS/cuDNN/OOM 推理错误会释放当前模型引用，重试同模型的 CPU 支持精度，并通过线程安全事件显示 CPU 降速提示。CPU 重试仍可能失败，按原有错误处理收尾；不保证低端 CPU 达到实时速度。

文件、实时模型仍互斥运行；翻译继续 CPU。探测/模型加载/推理/保存均不在 Tk 主线程，后台只投递事件。模型首次加载状态与运行状态分开；Controller 管理 Idle → Loading → Running → Stopping → Stopped，停止期间不能重启。关闭继续等待既有安全清理，不强杀文件输出过程。

## GUI 与偏好

- 两页各有质量下拉框；实时翻译开关与质量同行，统一开始/停止/导出命名。
- 页脚简洁显示 GPU/CPU 和任务状态；文件页有空状态，空会话禁用导出和清空。
- 硬件检查、模型加载、停止期间避免重复启动，未添加文件不可开始。
- 为 partial、翻译状态和页脚优先保留空间，文本区域可滚动，紧凑窗口测试检查实际映射后的控件位置。
- 在原有 UTF-8 原子替换配置中追加 file_quality / realtime_quality，空字符串表示 Auto；保留输出目录、语言、翻译、格式、麦克风等偏好。不保存硬件对象、设备/精度推荐、队列或线程状态；损坏配置安全回到默认并提示。
- GUI 文件任务的 completion manifest 增加可选 transcription 请求（模型 ID/路径、语言）。切换模型或语言不再误跳过旧结果；旧清单首次 GUI 使用会重算。不改变旧 CLI 不传该字段时的完成判断，不改变五种导出格式或转录 JSON schema。

## 修改文件

新增：src/hardware.py、src/model_registry.py、src/recommendation.py、tests/test_hardware.py、tests/manual_hardware_gui_smoke.py、PHASE8.md。

修改：src/gui.py、src/gui_controller.py、src/realtime_config.py、src/realtime_audio.py、src/transcriber.py、src/batch.py、src/exporter.py、tests/test_gui.py、tests/manual_gui_session_replay.py、README.md。旧回放驱动仅补充等待硬件检查完成，避免与新启动流程竞争。

## 验证方式

```powershell
conda run -n asr --no-capture-output python -m unittest discover -s tests -q
conda run -n asr --no-capture-output python tests/manual_hardware_gui_smoke.py --run-file
```

第二条使用现有 11.235 秒 Windows SAPI 合成英文 WAV，真实 large-v3 GPU 推理和 GUI 文件流程；不会打开麦克风，每次写独立 validation/phase8 时间目录。可加 --auto-close 自动关闭。

本机：Windows 11 build 26300，AMD Ryzen 7 5800H，15.4GiB RAM，RTX 3060 Laptop 6GiB，PyTorch CUDA=True，CT2 CUDA device count=1，支持 float16/int8_float16 等精度。默认文件 large-v3 CUDA/float16，实时 small CUDA/float16。

最终完整回归：166 项通过，20.263 秒；日志 validation/phase8/regression-final.txt。包含 Phase 1–7 回归和新增 27 项测试；硬件组合/故障为 mock，GUI 使用真实 Tk 控件配合假 Core worker。开发中先发现并修复紧凑窗口字幕/状态区域被挤压，以及布局测试未等待 Windows 映射窗口的问题，再运行完整回归通过。

首次真实文件测试：Success，TXT/DOCX/JSON/SRT/VTT 全部生成；模型加载约 10.17 秒，文件处理/导出约 2.69 秒。GUI 50ms 定时器持续推进，最大观测间隔 0.672 秒（包括启动/原生库加载）；后台化不等于消除所有原生库/GIL 短暂停顿。报告见 validation/phase8/20261010-065140-207007/report.json。最终回归及窗口复核另记录在 validation/phase8。

最终代码短文件复验同样 Success，五种格式齐全，completion 清单正确记录 large-v3/路径/en；报告 validation/phase8/20261010-065759-950302/report.json，最大 UI 定时器间隔 0.688 秒。使用 Windows computer-use 实际切换文件/实时页、展开质量菜单，确认 Fast/Accurate 与 Balanced 按页显示、GPU 状态正确、partial/翻译状态可见、空会话 Clear/Export 禁用，并安全关闭窗口。紧凑尺寸由自动 Tk 测试验证；未将窗口检查声称为真实麦克风 ASR 验证。

## 已知限制与下一阶段

- 当前只注册 small / large-v3，不提供模型安装器。目录完整性检查不等于权重校验或模型加载成功。
- 显存策略使用总容量，不做占用预测或压力基准；运行时资源竞争仍可能回退 CPU。主要针对单 NVIDIA GPU/默认设备 0，未验证多 GPU、MIG、重映射设备组合。
- 尚未在真实无 GPU/低显存电脑上测性能；这些路径为 mock 验证。没有在本阶段重新进行真人麦克风双语验证，也没有长时间压力测试。
- 建议下一阶段进行少量不同 Windows/CPU/GPU 真机兼容性测试，收集启动与短音频延迟，再决定是否增加更轻模型档位及分发方案。当前停止在 Phase 8。


