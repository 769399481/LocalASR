"""User-safe errors: technical exception detail stays in the logger."""
import errno
from ui_strings import tr

def error_message(error=None, category=None):
    detail = str(error).lower()
    if category is None:
        if isinstance(error, PermissionError): category = 'permission'
        elif isinstance(error, OSError) and error.errno == errno.ENOSPC: category = 'disk'
        elif isinstance(error, FileNotFoundError): category = 'missing'
        elif isinstance(error, TimeoutError): category = 'stopping'
        elif 'device_changed' in detail: category = 'device_changed'
        elif 'system_audio' in detail: category = 'system_audio'
        elif 'microphone' in detail or 'portaudio' in detail: category = 'microphone'
        elif 'cuda' in detail or 'cublas' in detail: category = 'gpu'
        else: category = 'generic'
    return tr('error_' + category)
