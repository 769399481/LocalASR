from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "distribution"))
from build_support import CUDA_NAMES, CPU_WHEEL_NAME, cuda_binaries, generated_paths, prepare_cpu_torch, deduplicate_runtime_binaries


class OptimizationTests(unittest.TestCase):
    def test_deduplicate_only_same_source_dll(self):
        entries = [("cuda/cublas.dll", "source/cublas.dll", "BINARY"),
                   ("torch/lib/cublas.dll", "source/cublas.dll", "BINARY"),
                   ("torch/lib/torch_cpu.dll", "cpu/torch_cpu.dll", "BINARY"),
                   ("torch_cpu.dll", "cpu/torch_cpu.dll", "BINARY"),
                   ("ctranslate2/cublas.dll", "other-version/cublas.dll", "BINARY")]
        kept, removed = deduplicate_runtime_binaries(entries)
        self.assertEqual(kept, [entries[0], entries[2], entries[4]])
        self.assertEqual(removed, [entries[1], entries[3]])

    def test_do_not_deduplicate_unregistered_locations(self):
        entries = [("a/data.dll", "same/data.dll", "BINARY"), ("b/data.dll", "same/data.dll", "BINARY")]
        self.assertEqual(deduplicate_runtime_binaries(entries), (entries, []))

    def test_variants_preserve_phase9_and_each_other(self):
        root = Path(__file__).resolve().parents[1]
        full_work, full_output = generated_paths(root, "full")
        opt_work, opt_output = generated_paths(root, "optimized")
        self.assertNotEqual(full_work, opt_work)
        self.assertNotEqual(full_output, opt_output)
        self.assertNotIn(root / "dist/LocalASR", (full_output, opt_output))
        for path in (full_work, opt_work, full_output, opt_output):
            self.assertTrue(path.is_relative_to(root))
        with self.assertRaises(ValueError): generated_paths(root, "../models")

    def test_cuda_collection_requires_explicit_files(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, "Missing explicit CUDA"):
                cuda_binaries(temp)
            for name in CUDA_NAMES: (Path(temp) / name).write_bytes(b"fixture")
            collected = cuda_binaries(temp)
            self.assertEqual(len(collected), len(CUDA_NAMES))
            self.assertTrue(all(destination == "cuda" for _, destination in collected))
            self.assertFalse(any(Path(path).name.lower() in ("nvcuda.dll", "nvml.dll", "torch_cuda.dll") for path, _ in collected))

    def test_missing_cpu_wheel_does_not_modify_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, "Download the pinned"):
                prepare_cpu_torch(temp)

    def test_cpu_wheel_staging_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            with zipfile.ZipFile(Path(temp) / CPU_WHEEL_NAME, "w") as wheel:
                wheel.writestr("torch/fixture.txt", "fixture")
            stage, digest = prepare_cpu_torch(temp)
            self.assertEqual((stage / "torch/fixture.txt").read_text(), "fixture")
            self.assertEqual(prepare_cpu_torch(temp), (stage, digest))

    def test_unsafe_wheel_path_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with zipfile.ZipFile(Path(temp) / CPU_WHEEL_NAME, "w") as wheel:
                wheel.writestr("../../outside.txt", "fixture")
            with self.assertRaisesRegex(ValueError, "Unsafe wheel"):
                prepare_cpu_torch(temp)


if __name__ == "__main__": unittest.main()
