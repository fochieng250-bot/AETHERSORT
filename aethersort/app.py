"""AetherSort native desktop MVP. Requires PySide6."""
from __future__ import annotations

import sys
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFrame, QStatusBar
)
from . import __version__
from .engine import AetherSortEngine


class ScanWorker(QThread):
    finished_plan = Signal(object, object)
    failed = Signal(str)

    def __init__(self, engine: AetherSortEngine, folder: Path):
        super().__init__()
        self.engine, self.folder = engine, folder

    def run(self):
        try:
            self.finished_plan.emit(self.engine.plan(self.folder), self.folder)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"AetherSort {__version__}")
        icon_path = Path(__file__).resolve().parent / "assets" / "aethersort.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1080, 720)
        self.engine = AetherSortEngine()
        self.folder: Path | None = None
        self.actions = []
        self.worker: ScanWorker | None = None

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        brand = QVBoxLayout()
        title = QLabel("AetherSort")
        title.setObjectName("title")
        subtitle = QLabel("A calmer, safer way to organize your files")
        subtitle.setObjectName("muted")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header.addLayout(brand)
        header.addStretch()
        self.pick_button = QPushButton("Choose folder")
        self.pick_button.setObjectName("primary")
        self.pick_button.clicked.connect(self.choose_folder)
        header.addWidget(self.pick_button)
        layout.addLayout(header)

        info = QFrame()
        info.setObjectName("info")
        info_layout = QVBoxLayout(info)
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setWordWrap(True)
        self.summary_label = QLabel("Choose a folder to preview file organization. AetherSort only scans files directly inside it.")
        self.summary_label.setObjectName("muted")
        self.summary_label.setWordWrap(True)
        info_layout.addWidget(self.folder_label)
        info_layout.addWidget(self.summary_label)
        layout.addWidget(info)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["File", "Category", "Action", "Destination"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        self.scan_button = QPushButton("Scan & preview")
        self.scan_button.clicked.connect(self.scan)
        self.sort_button = QPushButton("Organize files")
        self.sort_button.setObjectName("primary")
        self.sort_button.setEnabled(False)
        self.sort_button.clicked.connect(self.organize)
        self.undo_button = QPushButton("Undo last run")
        self.undo_button.clicked.connect(self.undo)
        buttons.addWidget(self.scan_button)
        buttons.addWidget(self.sort_button)
        buttons.addStretch()
        buttons.addWidget(self.undo_button)
        layout.addLayout(buttons)

        status = QStatusBar()
        status.showMessage("Ready · Local processing · No files moved until you confirm")
        self.setStatusBar(status)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f5f7fb; color: #172033; font-size: 14px; }
            QLabel#title { font-size: 30px; font-weight: 750; color: #101a2d; }
            QLabel#muted { color: #68758b; }
            QFrame#info { background: white; border: 1px solid #e0e6f0; border-radius: 12px; padding: 6px; }
            QPushButton { padding: 10px 16px; border: 1px solid #d5dce8; border-radius: 8px; background: white; }
            QPushButton:hover { background: #edf2fa; }
            QPushButton#primary { background: #275dad; color: white; border: 1px solid #275dad; font-weight: 600; }
            QPushButton#primary:hover { background: #1e4c91; }
            QPushButton:disabled { color: #9ba5b5; background: #eef1f6; }
            QTableWidget { background: white; border: 1px solid #e0e6f0; border-radius: 10px; gridline-color: #edf0f5; }
            QHeaderView::section { background: #edf1f7; padding: 10px; border: none; font-weight: 600; }
            QStatusBar { color: #68758b; }
        """)

    def choose_folder(self):
        selected = QFileDialog.getExistingDirectory(self, "Choose a folder to organize")
        if selected:
            self.folder = Path(selected)
            self.folder_label.setText(str(self.folder))
            self.summary_label.setText("Ready to scan. Subfolders are left untouched; existing files are never overwritten.")
            self.table.setRowCount(0)
            self.actions = []
            self.sort_button.setEnabled(False)

    def scan(self):
        if not self.folder:
            QMessageBox.information(self, "Choose a folder", "Choose a folder before scanning.")
            return
        self.scan_button.setEnabled(False)
        self.sort_button.setEnabled(False)
        self.summary_label.setText("Scanning folder and preparing a preview…")
        self.worker = ScanWorker(self.engine, self.folder)
        self.worker.finished_plan.connect(self.show_plan)
        self.worker.failed.connect(self.scan_failed)
        self.worker.finished.connect(lambda: self.scan_button.setEnabled(True))
        self.worker.start()

    def scan_failed(self, message: str):
        QMessageBox.critical(self, "Scan failed", message)
        self.summary_label.setText("Scan failed. No files were moved.")

    def show_plan(self, actions, folder):
        self.actions = actions
        self.table.setRowCount(0)
        moves = sum(a.status == "move" for a in actions)
        identical = sum(a.status == "identical" for a in actions)
        errors = sum(a.status == "error" for a in actions)
        for action in actions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            label = action.source.name
            destination = str(action.destination) if action.destination else "—"
            status = {"move": "Move", "identical": "Skip · identical", "error": "Review · error"}.get(action.status, action.status)
            values = [label, action.category, status, destination]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(action.note or value)
                if col == 2 and action.status == "error":
                    item.setForeground(Qt.GlobalColor.darkRed)
                self.table.setItem(row, col, item)
        self.summary_label.setText(f"Preview ready: {moves} file(s) to move · {identical} identical duplicate(s) to skip · {errors} item(s) need review. Nothing has been moved yet.")
        self.sort_button.setEnabled(moves > 0 and errors == 0)
        self.statusBar().showMessage("Preview ready · Review the proposed actions before organizing")

    def organize(self):
        if not self.folder or not self.actions:
            return
        moves = sum(a.status == "move" for a in self.actions)
        answer = QMessageBox.question(
            self, "Confirm organization",
            f"Move {moves} file(s) into category folders inside:\n\n{self.folder}\n\nExisting files will not be overwritten. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.sort_button.setEnabled(False)
        result = self.engine.execute(self.folder, self.actions)
        if result.errors:
            QMessageBox.warning(self, "Organization stopped", "Some actions could not be completed.\n\n" + "\n".join(result.errors))
        else:
            QMessageBox.information(self, "Organization complete", f"Moved: {result.moved}\nIdentical duplicates skipped: {result.skipped_identical}\n\nYou can use Undo last run to reverse this run.")
        self.scan()

    def undo(self):
        answer = QMessageBox.question(self, "Undo last run", "Move files from the last completed AetherSort run back to their original paths? Files will not be overwritten.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        result = self.engine.undo_last_run()
        if result.errors:
            QMessageBox.warning(self, "Undo needs attention", "\n".join(result.errors))
        else:
            QMessageBox.information(self, "Undo complete", f"Restored {result.moved} file(s) to their original paths.")
        if self.folder:
            self.scan()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AetherSort")
    app.setOrganizationName("AetherSort")
    app.setApplicationVersion(__version__)
    window = MainWindow()
    window.show()
    if window.engine.recovery_messages:
        QMessageBox.warning(
            window,
            "Recovery report",
            "AetherSort checked for interrupted operations when it started.\n\n"
            + "\n".join(window.engine.recovery_messages)
            + "\n\nPlease review the affected folder before starting another operation.",
        )
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
