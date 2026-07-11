"""
ui/downloads_popup.py
Live downloads popup: progress, speed, ETA, pause/resume/cancel, and a
"reveal in folder" hint, driven entirely from downloads.DownloadManager.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QLabel

from popup import FloatingPopup
from downloads import DownloadManager


def _human_size(num_bytes: float) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}TB"


class DownloadsPopup(FloatingPopup):
    def __init__(self, parent, download_manager: DownloadManager) -> None:
        super().__init__(parent, width_ratio=0.45, height=420, anchor="center")
        self.download_manager = download_manager

        self.header = QLabel("Downloads  (P: pause/resume, X: cancel)")
        self.header.setObjectName("dimLabel")
        self.results = QListWidget()

        self.layout_.addWidget(self.header)
        self.layout_.addWidget(self.results)

        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._refresh)

    def open(self) -> None:
        self._refresh()
        self.show_animated()
        self._timer.start()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._timer.stop()
        super().closeEvent(event)

    def _refresh(self) -> None:
        self.results.clear()
        if not self.download_manager.items:
            item = QListWidgetItem("No active downloads.")
            self.results.addItem(item)
            for entry in self.download_manager.history()[-10:]:
                self.results.addItem(QListWidgetItem(f"✓ {entry['filename']}  ({_human_size(entry.get('size_bytes', 0))})"))
            return

        for i, dl in enumerate(self.download_manager.items):
            eta = dl.eta_seconds
            eta_str = f"{int(eta)}s" if eta >= 0 else "--"
            line = (
                f"{dl.filename}  [{dl.progress_percent:.0f}%]  "
                f"{_human_size(dl.speed_bps)}/s  ETA {eta_str}  ({dl.state})"
            )
            item = QListWidgetItem(line)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.results.addItem(item)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        item = self.results.currentItem()
        index = item.data(Qt.ItemDataRole.UserRole) if item else None
        if index is not None and 0 <= index < len(self.download_manager.items):
            dl = self.download_manager.items[index]
            if event.key() == Qt.Key.Key_P:
                dl.resume() if dl.state == "paused" else dl.pause()
                return
            if event.key() == Qt.Key.Key_X:
                dl.cancel()
                return
        super().keyPressEvent(event)
