from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from app_paths import resolve_paths
from app_version import APP_VERSION
from diagnostics import make_diagnostics
from gui_controller import Settings
from model_download import ModelSpec, ModelDownloader, DownloadError, DownloadCancelled, validate_installed
from model_registry import discover_models


class DistributionTests(unittest.TestCase):
    def test_release_path_without_localappdata(self):
        paths = resolve_paths(frozen=True, environment={}, home="C:/Users/example", application="D:/Portable")
        self.assertEqual(paths.data, Path("C:/Users/example/AppData/Local/LocalASR"))

    def test_explicit_validation_data_is_separate_from_resources(self):
        paths = resolve_paths(frozen=True, environment={"LOCALASR_DATA_DIR": "D:/validation/data"}, application="D:/portable")
        self.assertEqual(paths.models, Path("D:/validation/data/models"))
        self.assertEqual(paths.application, Path("D:/portable"))

    def test_translation_legacy_release_model_path(self):
        from app_paths import translation_model_path, translation_model_available
        with tempfile.TemporaryDirectory() as temp:
            paths = resolve_paths(frozen=True, environment={"LOCALASR_DATA_DIR": temp}, application="D:/portable")
            model = paths.models / "opus-mt-en-zh"
            model.mkdir(parents=True)
            with patch("app_paths.PATHS", paths):
                self.assertFalse(translation_model_available())
                for name in ("config.json", "pytorch_model.bin", "source.spm", "target.spm", "vocab.json"):
                    (model / name).write_bytes(b"fixture")
                self.assertEqual(translation_model_path(), model)
                self.assertTrue(translation_model_available())

    def test_build_helper_rejects_missing_runtime_and_bundled_weights(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_helper", Path(__file__).resolve().parents[1] / "distribution/build.py")
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(RuntimeError, "Missing build artifact"):
                helper.validate_artifacts(root)
            for name in ("LocalASR.exe", "_internal/python311.dll", "_internal/model_catalog.json", "_internal/torch/lib/torch_cpu.dll"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"fixture")
            helper.validate_artifacts(root)
            (root / "model.bin").write_bytes(b"weights")
            with self.assertRaisesRegex(RuntimeError, "Model weights"):
                helper.validate_artifacts(root)

    def test_packaged_controlled_downloader_probe(self):
        from packaged_check import downloader_check
        with tempfile.TemporaryDirectory() as temp:
            self.assertTrue(all(downloader_check(Path(temp)).values()))

    def test_frozen_paths_not_install_directory(self):
        paths = resolve_paths(frozen=True, environment={"LOCALAPPDATA": "C:/Users/test/AppData/Local"},
                              application="C:/Program Files/LocalASR")
        self.assertEqual(paths.data, Path("C:/Users/test/AppData/Local/LocalASR"))
        for path in (paths.config, paths.logs, paths.recovery, paths.models, paths.downloads, paths.cache, paths.output):
            self.assertTrue(path.is_relative_to(paths.data))
            self.assertFalse(path.is_relative_to(paths.application))

    def test_source_paths_preserve_existing_data(self):
        paths = resolve_paths(frozen=False, environment={}, application="C:/example/checkout")
        self.assertEqual(paths.models, Path("C:/example/checkout/models"))

    def test_first_run_persistence_and_version(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            self.assertFalse(Settings.load(path).setup_completed)
            replace(Settings(), setup_completed=True).save(path)
            self.assertTrue(Settings.load(path).setup_completed)
            self.assertEqual(make_diagnostics()["version"], APP_VERSION)

    def test_diagnostics_excludes_raw_error_and_paths(self):
        from hardware import HardwareInfo
        from model_registry import ModelEntry
        from recommendation import recommend
        info = HardwareInfo(cpu="test", errors=("secret transcript C:/private.wav",))
        models = (ModelEntry("small", "small", "C:/private/user", "x", .5, "both", True),)
        result = json.dumps(make_diagnostics((info, models, recommend(info, models)), error_count=1))
        self.assertNotIn("secret", result)
        self.assertNotIn("private", result)
        self.assertIn("recent_errors", result)


class DownloaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.contents = {"config.json": b"{}", "tokenizer.json": b"{}", "model.bin": b"synthetic-model"}
        self.spec = ModelSpec("small", "Speech", "test/repo", "revision", tuple(
            {"name": n, "size": len(b), "sha256": hashlib.sha256(b).hexdigest()} for n,b in self.contents.items()))
        def open_url(request, timeout):
            stream = io.BytesIO(self.contents[request.full_url.rsplit("/", 1)[-1]])
            stream.status, stream.headers = 200, {}
            return stream
        self.opener = Mock(side_effect=open_url)
        self.downloader = ModelDownloader(self.root / "models", self.root / "downloads", opener=self.opener,
            disk_usage=lambda p: SimpleNamespace(free=10**10))

    def test_download_publish_and_registry(self):
        with patch.dict("model_download.CATALOG", small=self.spec):
            target = self.downloader.download(self.spec)
            self.assertTrue(validate_installed(target, self.spec))
            self.assertTrue(discover_models(self.root, self.root / "cache")[0].installed)
        self.assertFalse(any(self.downloader.downloads.glob("*.partial")))

    def test_existing_complete_model_does_not_use_network(self):
        target = self.downloader.download(self.spec)
        self.opener.reset_mock()
        self.assertEqual(target, self.downloader.download(self.spec))
        self.opener.assert_not_called()

    def test_network_failure_not_installed_and_retry(self):
        previous = self.opener.side_effect
        self.opener.side_effect = OSError("offline")
        with self.assertRaises(DownloadError): self.downloader.download(self.spec)
        self.assertFalse((self.downloader.models / self.spec.id / self.spec.revision).exists())
        self.opener.side_effect = previous
        self.assertTrue(validate_installed(self.downloader.download(self.spec), self.spec))

    def test_cancel_before_download(self):
        event = threading.Event()
        event.set()
        with self.assertRaises(DownloadCancelled): self.downloader.download(self.spec, event)
        self.opener.assert_not_called()

    def test_cancel_during_download_keeps_no_published_model(self):
        event = threading.Event()
        old = self.opener.side_effect
        def cancelled_open(*args, **kwargs):
            event.set()
            return old(*args, **kwargs)
        self.opener.side_effect = cancelled_open
        with self.assertRaises(DownloadCancelled): self.downloader.download(self.spec, event)
        self.assertFalse((self.downloader.models / "small/revision").exists())

    def test_corrupt_download_rejected(self):
        self.contents["model.bin"] = b"corrupted-model"
        with self.assertRaises(DownloadError): self.downloader.download(self.spec)
        self.assertFalse((self.downloader.models / "small/revision").exists())

    def test_same_size_corruption_rejected(self):
        self.contents["model.bin"] = b"x" * len(self.contents["model.bin"])
        with self.assertRaises(DownloadError): self.downloader.download(self.spec)

    def test_insufficient_disk_no_network(self):
        self.downloader.disk_usage = lambda p: SimpleNamespace(free=1)
        with self.assertRaisesRegex(DownloadError, "空间不足"): self.downloader.download(self.spec)
        self.opener.assert_not_called()

    def test_partial_without_marker_is_not_installed(self):
        path = self.downloader.models / "small/revision"
        path.mkdir(parents=True)
        (path / "model.bin").write_bytes(b"partial")
        self.assertFalse(validate_installed(path, self.spec))

    def test_offline_registry_never_downloads(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network")):
            self.assertFalse(any(m.installed for m in discover_models(self.root, self.root / "cache")))


if __name__ == "__main__": unittest.main()
