from ui_strings import tr
"""GUI application services. No Tk imports; core imports occur on workers."""
from dataclasses import asdict, dataclass
import json
import logging
import os
from pathlib import Path
import queue
import tempfile
import threading
from app_paths import PATHS, translation_model_path
ROOT = PATHS.data
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Settings:
    file_model: str = str(ROOT / 'models/large-v3')
    realtime_model: str = 'small'
    output_dir: str = str(ROOT / 'output')
    formats: tuple = ('txt', 'docx')
    language: str = 'auto'
    translation: bool = False
    target_language: str = 'zh-Hans'
    microphone: str = 'Default microphone'
    file_quality: str = ''
    realtime_quality: str = ''
    setup_completed: bool = False
    audio_source: str = 'microphone'
    overlay: dict | None = None
    global_hotkeys: bool = False

    def validate(self):
        if self.audio_source not in ('microphone', 'system'):
            raise ValueError(tr('ui_110'))
        if self.overlay:
            from subtitle_overlay import OverlayPreferences
            OverlayPreferences(**self.overlay).validate()
        if self.file_quality not in ('', 'Fast', 'Balanced', 'Accurate') or self.realtime_quality not in ('', 'Fast', 'Balanced', 'Accurate'):
            raise ValueError(tr('ui_111'))
        if not self.file_model.strip() or not self.realtime_model.strip() or (not self.output_dir.strip()):
            raise ValueError(tr('ui_112'))
        if not self.formats or not set(self.formats) <= {'txt', 'docx', 'json', 'srt', 'vtt'}:
            raise ValueError(tr('ui_113'))
        if self.language not in ('en', 'zh', 'auto') or self.target_language != 'zh-Hans':
            raise ValueError(tr('ui_114'))

    def save(self, path):
        self.validate()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(path)

    @classmethod
    def load(cls, path):
        path = Path(path)
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding='utf-8'))
        data['formats'] = tuple(data['formats'])
        settings = cls(**data)
        settings.validate()
        return settings

def friendly_error(error):
    from ui_errors import error_message
    return error_message(error)

class FileJob:
    """Adapt arbitrary selected files to the existing BatchProcessor, one at a time.

    The same batch object retains its lazy ASR/translation instances. Export,
    checkpoint, completion and per-file failures stay entirely in Core.
    """

    def __init__(self, settings, post, selection=None):
        from batch import BatchProcessor
        from transcriber import Transcriber
        from translation import TranslationOptions

        class SelectedBatch(BatchProcessor):

            def get_audio_files(self):
                return [self.current]

        def engine():
            post('status', tr('ui_115'))
            try:
                kwargs = dict(model_path=settings.file_model, language=settings.language)
                if selection:
                    kwargs.update(model_path=selection.model_path, device=selection.device, compute_type=selection.compute_type)
                model = Transcriber(**kwargs, on_device=lambda device, compute: post('acceleration', tr('ui_116') if device == 'cuda' else tr('ui_117')))
            except Exception as error:
                post('error', friendly_error(error))
                raise
            post('status', tr('ui_118'))
            post('state', 'Running')
            return model

        def translator(options):
            from translation import create_translator
            post('status', tr('ui_119'))
            return create_translator(options)
        self.batch = SelectedBatch(output_dir=settings.output_dir, transcriber_factory=engine, output_formats=settings.formats, translator_factory=translator, transcription_request={'model': selection.model_id if selection else settings.file_model, 'model_path': selection.model_path if selection else settings.file_model, 'language': settings.language}, translation_options=TranslationOptions(settings.translation, 'en', settings.target_language, 'marian_local', translation_model_path()))

    def run(self, path):
        self.batch.current = Path(path)
        result = self.batch.run()
        if result.failed:
            return ('Failed', tr('ui_120') if result.translation_failed else tr('ui_121'))
        return ('Skipped' if result.skipped else 'Success', '')

def realtime_factory(settings, device, callback, selection=None, post=None):
    from realtime_config import RealtimeConfig
    from realtime_audio import RealtimeWhisper
    from realtime_translation import RealtimeTranslationConfig, TranslatedRealtimeSession
    config = RealtimeConfig(model=selection.model_path if selection else settings.realtime_model, device=selection.device if selection else 'auto', microphone_device=device, compute_type=selection.compute_type if selection else None, allow_cpu_fallback=True, audio_source=settings.audio_source)
    return TranslatedRealtimeSession(callback, config, RealtimeTranslationConfig(enabled=settings.translation, target_language=settings.target_language, model_path=translation_model_path(), prewarm=True), engine_factory=lambda: RealtimeWhisper(config, status_callback=lambda device, compute: post and post('acceleration', tr('ui_116') if device == 'cuda' else tr('ui_122'))))

class Controller:

    def __init__(self, *, file_factory=FileJob, session_factory=realtime_factory, runtime_probe=None):
        self.file_factory, self.session_factory = (file_factory, session_factory)
        self.events = queue.Queue(512)
        self.thread = None
        self.stop_requested = threading.Event()
        self.overflow = threading.Event()
        self.documents = None
        self.runtime = None
        self.runtime_probe = runtime_probe
        self.state = 'Idle'

    def initialize_runtime(self, settings):
        from recommendation import inspect_runtime
        try:
            self.runtime = (self.runtime_probe or inspect_runtime)(settings)
            self.post('status', tr('checking_models'))
            self.post('runtime', self.runtime)
        except Exception:
            logger.exception('Hardware initialization failed')
            self.post('runtime_failed', None)
            self.post('error', tr('ui_123'))

    def selection(self, settings, kind):
        if self.runtime is None:
            self.initialize_runtime(settings)
        if self.runtime is None:
            raise ValueError(tr('ui_124'))
        policy = self.runtime[2]
        modes = getattr(policy, kind + '_modes')
        quality = getattr(settings, kind + '_quality') or getattr(policy, kind + '_default')
        if quality not in modes:
            raise ValueError(tr('ui_125'))
        selected = modes[quality]
        logger.info('Selected %s quality=%s: %s', kind, quality, selected)
        self.post('acceleration', policy.message)
        return selected

    def transition(self, state):
        self.state = state
        self.post('state', state)

    @property
    def busy(self):
        return self.thread is not None and self.thread.is_alive()

    def post(self, kind, value):
        if kind == 'state':
            if value == 'Running' and self.stop_requested.is_set():
                return
            self.state = value
        try:
            self.events.put_nowait((kind, value))
        except queue.Full:
            self.overflow.set()
            self.stop_requested.set()
            logger.error('GUI event queue full; stopping task')

    def drain(self):
        items = []
        for _ in range(100):
            try:
                items.append(self.events.get_nowait())
            except queue.Empty:
                break
        if self.overflow.is_set():
            self.overflow.clear()
            items.append(('error', tr('ui_126')))
        return items

    def _launch(self, action, task=False):
        if self.busy:
            raise ValueError(tr('ui_127'))
        self.stop_requested.clear()
        if task:
            self.transition('Loading')

        def work():
            try:
                action()
            except Exception as error:
                logger.exception('GUI task failed')
                self.post('error', friendly_error(error))
            finally:
                if task:
                    self.transition('Stopped')
                self.post('done', None)
        self.thread = threading.Thread(target=work, name='gui-core-owner', daemon=False)
        self.thread.start()

    def start_files(self, paths, settings):
        settings.validate()
        if settings.translation and settings.language != 'en':
            raise ValueError(tr('ui_128'))
        paths = tuple((Path(path) for path in paths))
        if not paths:
            raise ValueError(tr('ui_129'))
        if len({p.name.casefold() for p in paths}) != len(paths):
            raise ValueError(tr('ui_130'))

        def work():
            self.post('status', tr('ui_131'))
            try:
                directory = Path(settings.output_dir)
                directory.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryFile(dir=directory) as probe:
                    probe.write(b'test')
                job = FileJob(settings, self.post, self.selection(settings, 'file')) if self.file_factory is FileJob else self.file_factory(settings, self.post)
            except Exception as error:
                for path in paths:
                    self.post('file', (str(path), 'Failed', friendly_error(error)))
                raise
            for index, path in enumerate(paths):
                if self.stop_requested.is_set():
                    break
                self.post('file', (str(path), 'Processing', ''))
                if self.file_factory is not FileJob and (not self.stop_requested.is_set()):
                    self.transition('Running')
                self.post('status', tr('ui_132', arg0=index + 1, arg1=len(paths), arg2=path.name))
                try:
                    if not path.is_file():
                        raise FileNotFoundError(path)
                    state, error = job.run(path)
                except Exception as exc:
                    logger.exception('GUI file task failed')
                    state, error = ('Failed', friendly_error(exc))
                self.post('file', (str(path), state, error))
                self.post('progress', (index + 1, len(paths)))
            self.post('status', tr('ui_133') if self.stop_requested.is_set() else tr('ui_134'))
        self._launch(work, task=True)

    def start_realtime(self, settings, device=None):
        settings.validate()

        def work():
            session = None
            try:
                self.post('status', tr('ui_067'))

                def receive(event):
                    if self.documents is not None:
                        self.documents.accept(event)
                    self.post('realtime', event)
                session = realtime_factory(settings, device, receive, self.selection(settings, 'realtime'), self.post) if self.session_factory is realtime_factory else self.session_factory(settings, device, receive)
                session.start()
                if not self.stop_requested.is_set():
                    self.transition('Running')
                    self.post('status', tr('ui_135') if settings.audio_source == 'system' else tr('ui_136'))
                while not self.stop_requested.wait(0.1) and session.running:
                    pass
            finally:
                if session is not None:
                    self.transition('Stopping')
                    self.post('status', tr('ui_137'))
                    while True:
                        try:
                            session.stop()
                            break
                        except TimeoutError:
                            logger.exception('GUI shutdown still waiting')
                            self.post('error', tr('ui_138'))
                            threading.Event().wait(0.5)
                    self.post('metrics', session.metrics())
                if self.documents is not None:
                    self.documents.finish()
            self.post('status', tr('ui_139'))
        self._launch(work, task=True)

    def system_output(self):
        from audio_sources import capability
        try:
            if not capability('system').available:
                self.post('system_output', tr('ui_140'))
                return
            from windows_system_audio import default_output
            self.post('system_output', default_output()['name'].replace(' [Loopback]', ''))
        except Exception:
            logger.exception('System output inspection failed')
            self.post('system_output', tr('ui_141'))

    def devices(self):

        def work():
            import sounddevice as sd
            self.post('devices', [(i, d['name']) for i, d in enumerate(sd.query_devices()) if d['max_input_channels'] > 0])
        self._launch(work)

    def open_output(self, directory):

        def work():
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            os.startfile(str(path.resolve()))
        self._launch(work)

    def stop(self):
        self.stop_requested.set()
        if self.busy and self.state in ('Loading', 'Running'):
            self.transition('Stopping')
