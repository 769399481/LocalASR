import logging
from pathlib import Path

from faster_whisper import WhisperModel

from config import BEAM_SIZE, COMPUTE_TYPE, DEVICE, LANGUAGE, MODEL_PATH
from result import Segment, TranscriptionResult

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, model_path=MODEL_PATH, language=LANGUAGE,
                 device=DEVICE, compute_type=COMPUTE_TYPE, on_device=None):
        self.on_device = on_device
        self.model_path = Path(model_path)
        self.language = None if language in (None, "auto") else language
        self.device = device
        self.compute_type = compute_type
        if not (self.model_path / "model.bin").is_file():
            raise FileNotFoundError(f"Local model.bin missing: {self.model_path}")
        try:
            self.model = self._load_model()
        except RuntimeError:
            if self.device != "cuda":
                raise
            logger.warning("GPU model loading failed; retrying with supported CPU compute type", exc_info=True)
            self.device, self.compute_type = "cpu", self._cpu_compute_type()
            self.model = self._load_model()

    def _load_model(self):
        logger.info("Loading local model: %s; device=%s; compute_type=%s",
                    self.model_path, self.device, self.compute_type)
        model = WhisperModel(str(self.model_path), device=self.device,
                             compute_type=self.compute_type, local_files_only=True)
        logger.info("Model loaded")
        if self.on_device:
            self.on_device(self.device, self.compute_type)
        return model

    @staticmethod
    def _cpu_compute_type():
        import ctranslate2
        from recommendation import cpu_compute
        return cpu_compute(ctranslate2.get_supported_compute_types("cpu"))

    def transcribe(self, audio_path) -> TranscriptionResult:
        try:
            return self._transcribe(audio_path)
        except RuntimeError as error:
            # CUDA failures can be deferred until the segment iterator is consumed.
            if self.device != "cuda" or not any(token in str(error).lower() for token in
                                               ("cuda", "cublas", "cudnn", "out of memory")):
                raise
            logger.warning("GPU inference failed; retrying file with supported CPU compute type", exc_info=True)
            self.model = None
            self.device, self.compute_type = "cpu", self._cpu_compute_type()
            self.model = self._load_model()
            return self._transcribe(audio_path)

    def _transcribe(self, audio_path):
        segments, info = self.model.transcribe(
            str(audio_path), language=self.language, beam_size=BEAM_SIZE, vad_filter=True)
        result_segments = tuple(Segment(float(seg.start), float(seg.end), seg.text.strip())
                                for seg in segments)
        return TranscriptionResult(
            text="\n".join(seg.text for seg in result_segments),
            language=info.language, duration=float(info.duration), segments=result_segments)
