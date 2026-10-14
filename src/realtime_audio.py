"""Concrete local audio/VAD/ASR adapters; no translation or file-ASR imports."""

import logging

logger = logging.getLogger(__name__)


class Microphone:
    def __init__(self, config, feed, fault):
        import sounddevice as sd

        def callback(data, frames, timing, status):
            try:
                # Only copy/enqueue here. No VAD, Whisper, user callback or disk I/O.
                feed(bytes(data), overflow=bool(status.input_overflow))
            except Exception:
                fault("capture_callback_exception")
                raise sd.CallbackAbort

        self.fault = fault
        self.closing = False
        self.stream = sd.RawInputStream(
            samplerate=config.sample_rate, blocksize=config.frame_samples,
            channels=1, dtype="int16", device=config.microphone_device,
            callback=callback, finished_callback=self._finished)

    def _finished(self):
        if not self.closing:
            self.fault("microphone_disconnected")

    def start(self):
        self.stream.start()

    def close(self):
        self.closing = True
        try:
            self.stream.stop()
        finally:
            self.stream.close()


class WebRtcVad:
    def __init__(self, config):
        import webrtcvad
        self.vad = webrtcvad.Vad(config.vad_mode)
        self.rate = config.sample_rate

    def is_speech(self, pcm):
        return self.vad.is_speech(pcm, self.rate)


class RealtimeWhisper:
    def __init__(self, config, status_callback=None):
        import ctranslate2
        from faster_whisper import WhisperModel

        device = config.device
        if device == "auto":
            try:
                device = "cuda" if ctranslate2.get_cuda_device_count() else "cpu"
            except RuntimeError:
                device = "cpu"
        self.config = config
        self.status_callback = status_callback
        self.cpu_type = next((t for t in ("int8", "int8_float32", "float32")
                              if t in ctranslate2.get_supported_compute_types("cpu")), "float32")
        compute_type = config.compute_type or ("float16" if device == "cuda" else self.cpu_type)
        try:
            self.model = WhisperModel(config.model, device=device, compute_type=compute_type,
                                      local_files_only=True)
        except RuntimeError:
            if (config.device != "auto" and not config.allow_cpu_fallback) or device != "cuda":
                raise
            logger.warning("Realtime GPU initialization failed; using CPU/%s", self.cpu_type, exc_info=True)
            device, compute_type = "cpu", self.cpu_type
            self.model = WhisperModel(config.model, device=device, compute_type=compute_type,
                                      local_files_only=True)
        self.device, self.compute_type = device, compute_type
        logger.info("Realtime model=%s device=%s compute_type=%s", config.model, device, compute_type)
        if self.status_callback:
            self.status_callback(device, compute_type)

    def transcribe(self, pcm):
        try:
            return self._transcribe(pcm)
        except RuntimeError as error:
            if (self.device != "cuda" or not self.config.allow_cpu_fallback or
                not any(t in str(error).lower() for t in ("cuda", "cublas", "cudnn", "out of memory"))):
                raise
            from faster_whisper import WhisperModel
            logger.warning("Realtime CUDA inference failed; falling back to CPU", exc_info=True)
            self.model = None
            self.device, self.compute_type = "cpu", self.cpu_type
            self.model = WhisperModel(self.config.model, device="cpu", compute_type=self.cpu_type, local_files_only=True)
            if self.status_callback:
                self.status_callback(self.device, self.compute_type)
            return self._transcribe(pcm)

    def _transcribe(self, pcm):
        import numpy as np
        if not pcm:
            return ""
        audio = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        segments, _ = self.model.transcribe(
            audio, language="en", beam_size=1, temperature=0.0,
            vad_filter=False, condition_on_previous_text=False, without_timestamps=True)
        return " ".join(segment.text.strip() for segment in segments).strip()
