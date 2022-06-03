import sys
from PySide2.QtWidgets import QApplication, QMainWindow
from generatedwindow import Ui_MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        # The Ui_MainWindow class is far from idiomatic Python! But it's
        # generated from a template that would suit many other languages.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


if __name__ == "__main__":
    main()
