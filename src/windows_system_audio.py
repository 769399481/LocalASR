"""Windows output capture; owns PortAudio resources outside the GUI/ASR threads."""
import logging
import queue
import threading
import time
from audio_sources import PCMConverter

logger = logging.getLogger(__name__)


def default_output():
    import pyaudiowpatch as pa
    with pa.PyAudio() as host:
        device = host.get_default_wasapi_loopback()
        return {k: device[k] for k in ("name", "index", "defaultSampleRate", "maxInputChannels")}


class WindowsSystemAudioSource:
    def __init__(self, config, feed, fault):
        self.config, self.feed, self.fault = config, feed, fault
        self.stop_event = threading.Event()
        self.ready = threading.Event()
        self.raw = queue.Queue(100)
        self.error = None
        self.dropped = 0
        self.name = ""
        self.thread = None
        self.state = "idle"

    def start(self):
        if self.thread is not None:
            raise RuntimeError("Audio source already started")
        self.state = "starting"
        self.thread = threading.Thread(target=self._run, name="system-audio", daemon=True)
        self.thread.start()
        if not self.ready.wait(10):
            self.stop_event.set()
            raise TimeoutError("系统音频启动超时，请检查播放设备。")
        if self.error:
            raise RuntimeError("系统音频不可用，请检查默认播放设备并重试。") from self.error

    def _run(self):
        host = stream = None
        try:
            import pyaudiowpatch as pa
            host = pa.PyAudio()
            device = host.get_default_wasapi_loopback()
            self.name = device["name"]
            rate, channels = int(device["defaultSampleRate"]), int(device["maxInputChannels"])
            converter = PCMConverter(rate, channels, self.config.frame_samples)

            def callback(data, count, timing, status):
                if self.stop_event.is_set():
                    return (None, pa.paComplete)
                try:
                    self.raw.put_nowait((bytes(data), bool(status)))
                except queue.Full:
                    self.dropped += 1
                    # Fail visibly: never splice missing source time into valid subtitles.
                    self.fault("system_audio_queue_overflow")
                    self.stop_event.set()
                    return (None, pa.paAbort)
                return (None, pa.paContinue)

            stream = host.open(format=pa.paInt16, channels=channels, rate=rate,
                input=True, input_device_index=device["index"], frames_per_buffer=max(1, rate // 100),
                stream_callback=callback)
            logger.info("System Audio output=%s rate=%s channels=%s", self.name, rate, channels)
            self.state = "running"
            self.ready.set()
            next_check = time.monotonic() + 2
            while not self.stop_event.is_set():
                try:
                    pcm, overflow = self.raw.get(timeout=.1)
                    for frame in converter.convert(pcm):
                        self.feed(frame, overflow=overflow)
                        overflow = False
                except queue.Empty:
                    pass
                if time.monotonic() >= next_check:
                    if not stream.is_active():
                        raise OSError("System output capture stopped")
                    # Re-enumeration is outside native callbacks. On route change stop
                    # visibly; the next Start binds the current default output.
                    if default_output()["name"] != self.name:
                        self.state = "failed"
                        self.fault("system_audio_device_changed")
                        break
                    next_check = time.monotonic() + 2
        except Exception as error:
            self.error = error
            self.state = "failed"
            logger.exception("System audio capture unavailable")
            self.fault("system_audio_unavailable")
        finally:
            self.ready.set()
            if stream is not None:
                try:
                    stream.stop_stream()
                finally:
                    stream.close()
            if host is not None:
                host.terminate()
            while not self.raw.empty():
                try:
                    self.raw.get_nowait()
                except queue.Empty:
                    break
            if self.state != "failed":
                self.state = "stopped"

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(5)
            if self.thread.is_alive():
                raise TimeoutError("系统音频仍在退出，请稍候。")
