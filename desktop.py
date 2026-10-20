"""Native desktop host for the original GAME ENGEN editor UI.

The UI and Three.js editor are kept intact during the Python migration. This
host opens the bundled legacy_web/index.html inside Qt WebEngine so the desktop
application retains the original editor's panels and workflows instead of
substituting a reduced demo.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

ROOT = Path(__file__).resolve().parent
EDITOR_HTML = ROOT / "legacy_web" / "index.html"


class EditorPage(QWebEnginePage):
    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame: bool) -> bool:
        # Keep local editor navigation embedded. Open external links in the
        # user's default browser rather than unexpectedly replacing the editor.
        if url.scheme() in ("http", "https") and is_main_frame and url.host() not in (
            "cdn.jsdelivr.net", "127.0.0.1", "localhost"
        ):
            QDesktopServices.openUrl(url)
            return False
        return True


class GameEngenWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GAME ENGEN — Narrative RPG Studio")
        self.resize(1600, 1000)
        self.setMinimumSize(1024, 680)

        self.view = QWebEngineView(self)
        self.profile = QWebEngineProfile("GameEngenDesktop", self)
        self.page = EditorPage(self.profile, self.view)
        self.view.setPage(self.page)

        settings = self.page.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        self.setCentralWidget(self.view)

        downloads = ROOT / "downloads"
        downloads.mkdir(exist_ok=True)
        self.profile.downloadRequested.connect(
            lambda item: self._download(item, downloads)
        )

        if not EDITOR_HTML.is_file():
            QMessageBox.critical(
                self, "GAME ENGEN files missing",
                f"Cannot find the bundled editor UI:\n{EDITOR_HTML}\n\n"
                "Restore legacy_web/index.html from the repository."
            )
            raise FileNotFoundError(EDITOR_HTML)

        self.view.load(QUrl.fromLocalFile(str(EDITOR_HTML)))

    @staticmethod
    def _download(item: QWebEngineDownloadRequest, folder: Path) -> None:
        suggested = Path(item.downloadFileName()).name or "game-engen-export.json"
        target = folder / suggested
        if target.exists():
            target = folder / f"{target.stem}-{int(__import__('time').time())}{target.suffix}"
        item.setDownloadDirectory(str(folder))
        item.setDownloadFileName(target.name)
        item.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("GAME ENGEN")
    app.setOrganizationName("GAME ENGEN")
    window = GameEngenWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
