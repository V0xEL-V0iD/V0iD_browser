"""
downloads.py
Wraps Qt WebEngine's download requests, tracks progress/speed/ETA, and
persists completed download metadata to data/downloads.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

try:
    from PySide6.QtWebEngineCore import QWebEngineDownloadRequest
except ImportError:  # pragma: no cover - allows import without WebEngine present
    QWebEngineDownloadRequest = None  # type: ignore

ROOT_DIR = Path(__file__).resolve().parent
DOWNLOADS_PATH = ROOT_DIR / "data" / "downloads.json"


class DownloadItem(QObject):
    """Live state for a single in-progress or finished download."""

    progress_changed = Signal()
    state_changed = Signal()

    def __init__(self, qt_download: Any) -> None:
        super().__init__()
        self.qt_download = qt_download
        self.filename = Path(qt_download.downloadFileName()).name
        self.directory = qt_download.downloadDirectory()
        self.total_bytes = qt_download.totalBytes()
        self.received_bytes = 0
        self.start_time = time.time()
        self.state = "downloading"

        qt_download.receivedBytesChanged.connect(self._on_progress)
        qt_download.isFinishedChanged.connect(self._on_finished)
        qt_download.stateChanged.connect(self._on_state)

    def _on_progress(self) -> None:
        self.received_bytes = self.qt_download.receivedBytes()
        self.total_bytes = self.qt_download.totalBytes()
        self.progress_changed.emit()

    def _on_state(self) -> None:
        state_map = {
            0: "requested",
            1: "downloading",
            2: "completed",
            3: "cancelled",
            4: "interrupted",
        }
        self.state = state_map.get(int(self.qt_download.state()), "unknown")
        self.state_changed.emit()

    def _on_finished(self) -> None:
        self.state = "completed"
        self.state_changed.emit()

    @property
    def progress_percent(self) -> float:
        if not self.total_bytes:
            return 0.0
        return round((self.received_bytes / self.total_bytes) * 100, 1)

    @property
    def speed_bps(self) -> float:
        elapsed = max(time.time() - self.start_time, 0.001)
        return self.received_bytes / elapsed

    @property
    def eta_seconds(self) -> float:
        speed = self.speed_bps
        if speed <= 0 or not self.total_bytes:
            return -1
        remaining = self.total_bytes - self.received_bytes
        return remaining / speed

    def pause(self) -> None:
        self.qt_download.pause()

    def resume(self) -> None:
        self.qt_download.resume()

    def cancel(self) -> None:
        self.qt_download.cancel()

    @property
    def full_path(self) -> str:
        return str(Path(self.directory) / self.filename)


class DownloadManager(QObject):
    """Tracks all downloads for the session and persists history to disk."""

    download_added = Signal(object)

    def __init__(self, path: Path = DOWNLOADS_PATH) -> None:
        super().__init__()
        self.path = path
        self.items: list[DownloadItem] = []
        self._history: list[dict[str, Any]] = []
        self._load_history()

    def _load_history(self) -> None:
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as fh:
                self._history = json.load(fh)
        else:
            self._history = []

    def _save_history(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self._history, fh, indent=2)

    def handle_download(self, qt_download: Any) -> DownloadItem:
        """Called from a QWebEngineProfile.downloadRequested signal."""
        item = DownloadItem(qt_download)
        self.items.append(item)
        qt_download.accept()
        item.state_changed.connect(lambda i=item: self._maybe_record(i))
        self.download_added.emit(item)
        return item

    def _maybe_record(self, item: DownloadItem) -> None:
        if item.state == "completed":
            self._history.append(
                {
                    "filename": item.filename,
                    "path": item.full_path,
                    "size_bytes": item.total_bytes,
                }
            )
            self._save_history()

    def history(self) -> list[dict[str, Any]]:
        return list(self._history)
