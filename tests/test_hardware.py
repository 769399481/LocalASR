"""Synthetic hardware/registry scenarios; no hardware performance claims."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hardware import HardwareInfo, detect_hardware
from model_registry import ModelEntry, discover_models
from recommendation import recommend
from realtime_audio import RealtimeWhisper
from realtime_config import RealtimeConfig
from exporter import Exporter
from result import Segment, TranscriptionResult


class HardwareTests(unittest.TestCase):
    def test_probes_ct2_independently_of_torch(self):
        torch = SimpleNamespace(cuda=Mock(is_available=Mock(return_value=False)))
        ct2 = SimpleNamespace(get_cuda_device_count=lambda: 1,
                              get_supported_compute_types=lambda device, *args: {"float16"} if device == "cuda" else {"int8"})
        with patch.dict(sys.modules, torch=torch, ctranslate2=ct2), patch("hardware.system_memory_gb", return_value=16), \
             patch("hardware.subprocess.run", return_value=SimpleNamespace(stdout="RTX mock, 6144\n")):
            info = detect_hardware()
        self.assertTrue(info.nvidia_present)
        self.assertFalse(info.torch_cuda)
        self.assertEqual(info.ct2_cuda_devices, 1)
        self.assertEqual(info.cuda_compute_types, ("float16",))
        self.assertEqual(info.vram_gb, 6)
        torch.cuda.is_available.assert_not_called()

    def test_probe_failures_are_data_not_crash(self):
        torch = SimpleNamespace(cuda=Mock(is_available=Mock(side_effect=RuntimeError("broken"))))
        ct2 = SimpleNamespace(get_supported_compute_types=Mock(side_effect=RuntimeError("DLL")))
        with patch.dict(sys.modules, torch=torch, ctranslate2=ct2), patch("hardware.system_memory_gb", side_effect=OSError()), \
             patch("hardware.subprocess.run", side_effect=FileNotFoundError()):
            info = detect_hardware()
        self.assertEqual(info.ct2_cuda_devices, 0)
        self.assertEqual(len(info.errors), 3)
        torch.cuda.is_available.assert_not_called()

    def test_file_default_device_uses_ct2_with_cpu_torch(self):
        from config import default_asr_device
        with patch.dict(sys.modules, torch=None, ctranslate2=SimpleNamespace(get_cuda_device_count=lambda: 1)):
            self.assertEqual(default_asr_device(), "cuda")

    def test_file_default_device_cpu_on_ct2_failure(self):
        from config import default_asr_device
        with patch.dict(sys.modules, ctranslate2=SimpleNamespace(get_cuda_device_count=Mock(side_effect=RuntimeError("driver")))):
            self.assertEqual(default_asr_device(), "cpu")


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        self.info = HardwareInfo(ram_gb=16, nvidia_present=True, vram_gb=6, torch_cuda=True,
            ct2_cuda_devices=1, cuda_compute_types=("float16", "float32"), cpu_compute_types=("int8", "float32"))
        self.models = (ModelEntry("small", "Small", "small-local", "mock", .5, "both", True),
                       ModelEntry("large-v3", "Large", "large-local", "mock", 3, "file", True, realtime_compatible=False))

    def test_current_hardware_defaults(self):
        result = recommend(self.info, self.models)
        self.assertEqual(result.file_default, "Accurate")
        self.assertEqual(result.file_modes["Accurate"].device, "cuda")
        self.assertEqual(result.realtime_modes["Balanced"].compute_type, "float16")

    def test_cpu_without_gpu(self):
        result = recommend(replace(self.info, nvidia_present=False, vram_gb=0, torch_cuda=False, ct2_cuda_devices=0), self.models)
        self.assertEqual(result.file_default, "Fast")
        self.assertEqual(result.file_modes["Fast"].device, "cpu")
        self.assertEqual(result.file_modes["Fast"].compute_type, "int8")
        self.assertIn("CPU", result.message)

    def test_torch_cuda_is_not_sufficient(self):
        result = recommend(replace(self.info, ct2_cuda_devices=0), self.models)
        self.assertEqual(result.file_modes["Fast"].device, "cpu")

    def test_cuda_compute_probe_failed(self):
        result = recommend(replace(self.info, cuda_compute_types=()), self.models)
        self.assertEqual(result.file_modes["Fast"].device, "cpu")

    def test_low_vram_uses_small_gpu(self):
        result = recommend(replace(self.info, vram_gb=4), self.models)
        self.assertEqual(result.file_default, "Fast")
        self.assertEqual(result.file_modes["Fast"].device, "cuda")
        self.assertNotIn("Accurate", result.file_modes)

    def test_very_low_or_unknown_vram_uses_cpu(self):
        for memory in (0, 1):
            with self.subTest(memory=memory):
                result = recommend(replace(self.info, vram_gb=memory), self.models)
                self.assertEqual(result.file_modes["Fast"].device, "cpu")

    def test_cpu_uses_only_supported_compute(self):
        result = recommend(replace(self.info, ct2_cuda_devices=0, cpu_compute_types=("float32",)), self.models)
        self.assertEqual(result.file_modes["Fast"].compute_type, "float32")

    def test_large_missing_selects_installed_small(self):
        result = recommend(self.info, (self.models[0], replace(self.models[1], installed=False)))
        self.assertEqual(result.file_default, "Fast")

    def test_missing_models_have_no_selectable_modes(self):
        result = recommend(self.info, tuple(replace(m, installed=False) for m in self.models))
        self.assertEqual(result.file_modes, {})
        self.assertEqual(result.realtime_modes, {})
        self.assertIn("本地模型", result.message)

    def test_insufficient_ram_rejects_small(self):
        result = recommend(replace(self.info, ram_gb=2, ct2_cuda_devices=0), self.models)
        self.assertEqual(result.file_modes, {})


class RegistryTests(unittest.TestCase):
    def make_model(self, path):
        path.mkdir(parents=True)
        (path / "model.bin").write_bytes(b"fixture")
        (path / "config.json").write_text("{}")
        (path / "tokenizer.json").write_text("{}")

    def test_local_large_and_cached_small(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_model(root / "models/large-v3")
            small = root / "cache/models--Systran--faster-whisper-small/snapshots/snapshot"
            self.make_model(small)
            models = discover_models(root, root / "cache")
            self.assertTrue(all(m.installed for m in models))
            self.assertEqual(models[0].path, str(small))
            self.assertFalse(models[1].realtime_compatible)

    def test_missing_and_incomplete_are_unavailable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_model(root / "models/small")
            (root / "models/small/config.json").write_text("broken")
            self.assertFalse(any(m.installed for m in discover_models(root, root / "cache")))


class ModelCompletionTests(unittest.TestCase):
    def test_changed_model_or_language_is_not_skipped(self):
        result = TranscriptionResult("Hello", "en", 1, (Segment(0, 1, "Hello"),))
        request = {"model": "small", "model_path": "local-small", "language": "en"}
        with tempfile.TemporaryDirectory() as temp:
            Exporter.export("audio", result, temp, ("txt", "json"), transcription_request=request)
            self.assertTrue(Exporter.is_complete("audio", temp, ("txt", "json"), transcription_request=request))
            for changed in ({**request, "model": "large-v3"}, {**request, "language": "auto"}):
                self.assertFalse(Exporter.is_complete("audio", temp, ("txt", "json"), transcription_request=changed))
            self.assertTrue(Exporter.is_complete("audio", temp, ("txt", "json")))  # Legacy API unchanged.

    def test_old_completion_without_model_requires_gui_retry(self):
        result = TranscriptionResult("Hello", "en", 1, (Segment(0, 1, "Hello"),))
        with tempfile.TemporaryDirectory() as temp:
            Exporter.export("audio", result, temp, ("txt",))
            self.assertFalse(Exporter.is_complete("audio", temp, ("txt",), transcription_request={"model": "small"}))


class RealtimeFallbackTests(unittest.TestCase):
    def test_gpu_load_failure_uses_cpu_and_reports_mode(self):
        status = Mock()
        with patch("faster_whisper.WhisperModel", side_effect=[RuntimeError("CUDA missing"), Mock()]) as model, \
             patch("ctranslate2.get_supported_compute_types", return_value={"float32"}):
            with self.assertLogs("realtime_audio", level="WARNING"):
                engine = RealtimeWhisper(RealtimeConfig(device="cuda", allow_cpu_fallback=True), status)
        self.assertEqual(engine.device, "cpu")
        self.assertEqual(model.call_args.kwargs["compute_type"], "float32")
        self.assertTrue(model.call_args.kwargs["local_files_only"])
        status.assert_called_once_with("cpu", "float32")

    def test_deferred_gpu_inference_retries_once_on_cpu(self):
        def broken():
            raise RuntimeError("CUDA out of memory")
            yield
        gpu = Mock()
        gpu.transcribe.return_value = (broken(), None)
        cpu = Mock()
        cpu.transcribe.return_value = (iter([SimpleNamespace(text="Hello")]), None)
        with patch("faster_whisper.WhisperModel", side_effect=[gpu, cpu]) as model:
            engine = RealtimeWhisper(RealtimeConfig(device="cuda", allow_cpu_fallback=True))
            with self.assertLogs("realtime_audio", level="WARNING"):
                self.assertEqual(engine.transcribe(bytes(960)), "Hello")
        self.assertEqual(engine.device, "cpu")
        self.assertEqual(model.call_count, 2)

    def test_non_cuda_error_does_not_reload(self):
        with patch("faster_whisper.WhisperModel") as model:
            model.return_value.transcribe.side_effect = RuntimeError("bad audio")
            engine = RealtimeWhisper(RealtimeConfig(device="cuda", allow_cpu_fallback=True))
            with self.assertRaisesRegex(RuntimeError, "bad audio"):
                engine.transcribe(bytes(960))
            self.assertEqual(model.call_count, 1)


if __name__ == "__main__":
    unittest.main()
