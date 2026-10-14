"""Phase 2 regression tests; no model, audio or user output is modified."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from batch import BatchProcessor
from config import OUTPUT_FORMATS
from exporter import Exporter
from result import Segment, TranscriptionResult


def transcript():
    segments = (Segment(0.12345, 1.56789, "Hello, 世界！"),
                Segment(3661.25, 3663.75, "Second segment. 第二段。"))
    return TranscriptionResult("Hello, 世界！\nSecond segment. 第二段。", "en", 3664.5, segments)


class TimestampTests(unittest.TestCase):
    def test_srt_and_vtt_boundaries(self):
        cases = ((0, "00:00:00,000"), (1.234, "00:00:01,234"),
                 (59.9994, "00:00:59,999"), (59.9995, "00:01:00,000"),
                 (3599.9995, "01:00:00,000"), (3661.25, "01:01:01,250"),
                 (90061.001, "25:01:01,001"), (360000, "100:00:00,000"))
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(Exporter.timestamp(value), expected)
                self.assertEqual(Exporter.timestamp(value, vtt=True), expected.replace(",", "."))

    def test_invalid_timestamps(self):
        for value in (-1, float("nan"), float("inf"), True, "1.5"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Exporter.timestamp(value)


class StructuredExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="asr-phase2-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "output"
        self.input = self.root / "input"
        self.input.mkdir()

    def export(self, result=None, formats=OUTPUT_FORMATS):
        return Exporter.export("meeting.wav", transcript() if result is None else result,
                               self.output, formats=formats)

    def read(self, suffix):
        return (self.output / f"meeting.wav.{suffix}").read_text(encoding="utf-8")

    def test_json_preserves_original_fields_precision_and_unicode(self):
        paths = self.export()
        self.assertEqual(len(paths), 5)
        source = self.read("json")
        self.assertIn("世界", source)
        data = json.loads(source)
        self.assertEqual(data, {
            "language": "en", "duration": 3664.5,
            "text": "Hello, 世界！\nSecond segment. 第二段。",
            "segments": [{"start": 0.12345, "end": 1.56789, "text": "Hello, 世界！"},
                         {"start": 3661.25, "end": 3663.75, "text": "Second segment. 第二段。"}]})

    def test_srt_exact_real_timings_and_multiple_cues(self):
        self.export()
        self.assertEqual(self.read("srt"),
                         "1\n00:00:00,123 --> 00:00:01,568\nHello, 世界！\n\n"
                         "2\n01:01:01,250 --> 01:01:03,750\nSecond segment. 第二段。\n\n")

    def test_vtt_header_and_exact_timings(self):
        self.export()
        self.assertEqual(self.read("vtt"),
                         "WEBVTT\n\n1\n00:00:00.123 --> 00:00:01.568\nHello, 世界！\n\n"
                         "2\n01:01:01.250 --> 01:01:03.750\nSecond segment. 第二段。\n\n")

    def test_empty_segment_list_is_valid_complete_output(self):
        self.export(TranscriptionResult("", "en", 0.0, ()))
        self.assertEqual(json.loads(self.read("json"))["segments"], [])
        self.assertEqual(self.read("srt"), "")
        self.assertEqual(self.read("vtt"), "WEBVTT\n\n")
        self.assertTrue(Exporter.is_complete("meeting.wav", self.output))

    def test_blank_zero_duration_and_submillisecond_segments(self):
        segments = (Segment(0, 1, " \n "), Segment(1, 1, "zero"),
                    Segment(2.0001, 2.0002, "too short"), Segment(3, 4, "Visible"))
        result = TranscriptionResult("zero too short Visible", "en", 4, segments)
        with self.assertLogs("exporter", level="WARNING"):
            self.export(result)
        self.assertEqual(len(json.loads(self.read("json"))["segments"]), 4)
        self.assertEqual(self.read("srt"), "1\n00:00:03,000 --> 00:00:04,000\nVisible\n\n")

    def test_vtt_escapes_markup_and_removes_blank_payload_lines(self):
        result = TranscriptionResult("<b>Literal</b> & -->", "en", 1,
                                     (Segment(0, 1, "<b>Literal</b> & -->\n\n中文"),))
        self.export(result)
        self.assertIn("&lt;b&gt;Literal&lt;/b&gt; &amp; --&gt;\n中文\n\n", self.read("vtt"))
        self.assertEqual(json.loads(self.read("json"))["segments"][0]["text"], result.segments[0].text)

    def test_invalid_segment_end_and_nonfinite_values_fail_before_publication(self):
        for segment in (Segment(2, 1, "bad"), Segment(-1, 2, "bad"),
                        Segment(0, float("nan"), "bad")):
            with self.subTest(segment=segment), self.assertRaises(ValueError):
                self.export(TranscriptionResult("bad", "en", 2, (segment,)))
        self.assertFalse(self.output.exists())

    def test_unsorted_subtitles_fail_and_overlapping_segments_are_allowed(self):
        with self.assertRaises(ValueError):
            self.export(TranscriptionResult("bad", "en", 3,
                                           (Segment(2, 3, "late"), Segment(0, 1, "early"))))
        self.assertEqual(list(self.output.iterdir()), [])
        self.export(TranscriptionResult("overlap", "en", 3,
                                       (Segment(0, 2, "first"), Segment(1, 3, "second"))))
        self.assertTrue(Exporter.is_complete("meeting.wav", self.output))

    def test_each_required_file_missing_or_changed_is_incomplete(self):
        paths = self.export()
        self.assertTrue(Exporter.is_complete("meeting.wav", self.output))
        for path in paths:
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.unlink()
                self.assertFalse(Exporter.is_complete("meeting.wav", self.output))
                path.write_bytes(b"corrupt")
                with self.assertLogs("exporter", level="WARNING"):
                    self.assertFalse(Exporter.is_complete("meeting.wav", self.output))
                path.write_bytes(original)
                self.assertTrue(Exporter.is_complete("meeting.wav", self.output))

    def test_format_subset_and_configuration_expansion(self):
        self.export(formats=("json", "vtt"))
        self.assertTrue(Exporter.is_complete("meeting.wav", self.output, formats=("json", "vtt")))
        self.assertFalse(Exporter.is_complete("meeting.wav", self.output))
        self.export()
        self.assertTrue(Exporter.is_complete("meeting.wav", self.output))
        self.assertTrue(Exporter.is_complete("meeting.wav", self.output, formats=("txt", "docx")))

    def test_old_untracked_outputs_and_corrupt_manifest_are_incomplete(self):
        self.export()
        manifest = self.output / "meeting.wav.complete.json"
        manifest.unlink()
        self.assertFalse(Exporter.is_complete("meeting.wav", self.output))
        manifest.write_text("broken", encoding="utf-8")
        with self.assertLogs("exporter", level="WARNING"):
            self.assertFalse(Exporter.is_complete("meeting.wav", self.output))

    def test_staging_failure_preserves_all_existing_outputs(self):
        self.export()
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        for method in ("save_json", "save_srt", "save_vtt"):
            with self.subTest(method=method), patch.object(Exporter, method, side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    self.export()
            self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_partial_publication_and_manifest_failure_recover(self):
        self.export()
        original_replace = Path.replace
        for failed_name in ("transcript.json", "transcript.srt", "transcript.vtt", "complete.json"):
            def fail(source, target):
                if source.name == failed_name:
                    raise PermissionError("file locked")
                return original_replace(source, target)

            with self.subTest(failed_name=failed_name), patch.object(Path, "replace", fail):
                with self.assertRaises(PermissionError):
                    self.export()
            self.assertFalse(Exporter.is_complete("meeting.wav", self.output))
            self.export()
            self.assertTrue(Exporter.is_complete("meeting.wav", self.output))

    def test_no_timestamps_are_invented_for_plain_strings(self):
        with self.assertRaises(TypeError):
            self.export("plain text")
        self.assertFalse(self.output.exists())
        paths = self.export("plain text", formats=("txt", "docx"))
        self.assertEqual(len(paths), 2)

    def test_invalid_format_configuration(self):
        for formats in ((), ("pdf",), "txt"):
            with self.subTest(formats=formats), self.assertRaises(ValueError):
                self.export(formats=formats)
        self.assertFalse(self.output.exists())

    def test_batch_all_formats_then_skip_without_loading_model(self):
        (self.input / "meeting.wav").touch()
        factory = Mock(return_value=Mock(transcribe=Mock(return_value=transcript())))
        summary = BatchProcessor(self.input, self.output, transcriber_factory=factory).run()
        self.assertEqual((summary.success, summary.failed), (1, 0))
        self.assertTrue(Exporter.is_complete("meeting.wav", self.output))
        not_loaded = Mock(side_effect=AssertionError("must not load"))
        summary = BatchProcessor(self.input, self.output, transcriber_factory=not_loaded).run()
        self.assertEqual((summary.skipped, summary.processed), (1, 0))
        not_loaded.assert_not_called()

    def test_batch_format_expansion_reprocesses_and_reports_export_failure(self):
        (self.input / "meeting.wav").touch()
        self.export(formats=("txt", "docx"))
        factory = Mock(return_value=Mock(transcribe=Mock(return_value=transcript())))
        with patch.object(Exporter, "save_vtt", side_effect=OSError("disk full")):
            with self.assertLogs("batch", level="ERROR"):
                summary = BatchProcessor(self.input, self.output, transcriber_factory=factory).run()
        self.assertEqual((summary.failed, summary.skipped, summary.success), (1, 0, 0))
        self.assertEqual(summary.failures, ["meeting.wav"])
        self.assertFalse(Exporter.is_complete("meeting.wav", self.output))
        summary = BatchProcessor(self.input, self.output, transcriber_factory=factory).run()
        self.assertEqual(summary.success, 1)


if __name__ == "__main__":
    unittest.main()
