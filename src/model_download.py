"""Explicit, cancellable HTTPS downloads with pinned checksums and atomic publish."""
from dataclasses import dataclass
import hashlib
import json
import logging
from pathlib import Path
import shutil
import threading
import time
import urllib.request
from app_version import APP_VERSION

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelSpec:
    id: str
    name: str
    repo: str
    revision: str
    files: tuple

    @property
    def size(self): return sum(f["size"] for f in self.files)


CATALOG = {key: ModelSpec(**{**value, "files": tuple(value["files"])}) for key, value in
           json.loads(Path(__file__).with_name("model_catalog.json").read_text(encoding="utf-8")).items()}


class DownloadCancelled(Exception): pass
class DownloadError(Exception): pass


def cancelled(event):
    if event.is_set():
        raise DownloadCancelled("下载已取消，可稍后重试。")


def file_valid(path, entry, event=None):
    if not path.is_file() or path.stat().st_size != entry["size"]:
        return False
    digest = hashlib.sha256() if entry.get("sha256") else hashlib.sha1()
    if not entry.get("sha256"):
        digest.update(f"blob {entry['size']}\0".encode())
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            if event is not None: cancelled(event)
            digest.update(block)
    return digest.hexdigest() == (entry.get("sha256") or entry.get("git_sha1"))


def validate_installed(path, spec):
    """Cheap startup check; complete cryptographic validation happens at publish."""
    try:
        marker = json.loads((path / "installed.json").read_text(encoding="utf-8"))
        return (marker == {"revision": spec.revision, "files": list(spec.files)} and
                all((path / f["name"]).stat().st_size == f["size"] for f in spec.files))
    except (OSError, ValueError, TypeError):
        return False


class ModelDownloader:
    def __init__(self, models, downloads, *, opener=urllib.request.urlopen, disk_usage=shutil.disk_usage):
        self.models, self.downloads = Path(models), Path(downloads)
        self.opener, self.disk_usage = opener, disk_usage

    def download(self, spec, cancel=None, progress=None):
        cancel = cancel or threading.Event()
        progress = progress or (lambda value: None)
        target = self.models / spec.id / spec.revision
        if validate_installed(target, spec):
            progress((spec.id, 100, "已安装"))
            return target
        self.downloads.mkdir(parents=True, exist_ok=True)
        # OS lock is released even on crashes. Two application instances cannot publish together.
        import msvcrt
        with (self.downloads / (spec.id + ".lock")).open("a+b") as lock:
            lock.seek(0)
            if not lock.read(1):
                lock.write(b"0")
                lock.flush()
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise DownloadError("另一窗口正在下载此模型，请稍后重试。") from error
            try:
                return self._download(spec, target, cancel, progress)
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)

    def _download(self, spec, target, cancel, progress):
        cancelled(cancel)
        if self.disk_usage(self.downloads).free < spec.size * 2 + 512 * 1024**2:
            raise DownloadError("磁盘空间不足。请释放空间后重试（模型大小的两倍另加 512MB）。")
        stage = self.downloads / (spec.id + "-" + spec.revision + ".partial")
        stage.mkdir(exist_ok=True)
        done, last = 0, 0.0
        try:
            for entry in spec.files:
                cancelled(cancel)
                name = entry["name"]
                if Path(name).name != name:
                    raise DownloadError("下载清单无效。")
                dest = stage / name
                if file_valid(dest, entry, cancel):
                    done += entry["size"]
                    continue
                part = stage / (name + ".part")
                offset = part.stat().st_size if part.exists() else 0
                if offset >= entry["size"]:
                    offset = 0
                headers = {"User-Agent": f"LocalASR/{APP_VERSION}", "Accept-Encoding": "identity"}
                if offset: headers["Range"] = f"bytes={offset}-"
                url = f"https://huggingface.co/{spec.repo}/resolve/{spec.revision}/{name}"
                with self.opener(urllib.request.Request(url, headers=headers), timeout=15) as response:
                    if offset and (response.status != 206 or not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-")):
                        offset = 0
                    with part.open("ab" if offset else "wb") as output:
                        count = offset
                        while block := response.read(1024 * 1024):
                            cancelled(cancel)
                            count += len(block)
                            if count > entry["size"]: raise DownloadError("下载文件大小异常，请重试。")
                            output.write(block)
                            now = time.monotonic()
                            if now - last >= .2:
                                progress((spec.id, (done + count) * 100 / spec.size, "正在下载…"))
                                last = now
                progress((spec.id, (done + entry["size"]) * 100 / spec.size, "正在校验…"))
                if not file_valid(part, entry, cancel):
                    # Discard only our invalid partial, never an existing installed/user model.
                    part.unlink(missing_ok=True)
                    raise DownloadError("下载文件校验失败，请重试。")
                part.replace(dest)
                done += entry["size"]
            cancelled(cancel)
            (stage / "installed.json").write_text(json.dumps({"revision": spec.revision, "files": list(spec.files)}), encoding="utf-8")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target.rename(target.with_name(target.name + f".incomplete-{time.time_ns()}"))
            stage.replace(target)
            progress((spec.id, 100, "下载完成，可离线使用"))
            return target
        except (DownloadCancelled, DownloadError):
            raise
        except OSError as error:
            logger.exception("Model download failed: %s", spec.id)
            raise DownloadError("下载未完成，请检查网络连接和磁盘空间后重试。已有模型仍可离线使用。") from error
