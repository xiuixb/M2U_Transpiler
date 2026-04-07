from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("PySide6 is required. Install dependencies in the mclparser environment first.")
        return 1

    from src.presentation.controller import FrontendController
    from src.presentation.main_window import MainWindow

    app = QApplication(sys.argv)
    controller = FrontendController()
    window = MainWindow(controller)
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
