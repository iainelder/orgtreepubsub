import sys
from pathlib import Path
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, QIODevice


root_path = Path(__file__).parent
view_path = root_path / "declarativewindow.ui"


# Generates the folloing terminal output: Qt WebEngine seems to be initialized
# from a plugin. Please set Qt::AA_ShareOpenGLContexts using
# QCoreApplication::setAttribute before constructing QGuiApplication.

def main() -> None:
    app = QApplication(sys.argv)

    ui_file_name = str(view_path)
    ui_file = QFile(ui_file_name)

    if not ui_file.open(QIODevice.ReadOnly):
        print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
        sys.exit(-1)

    loader = QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()

    if not window:
        print(loader.errorString())
        sys.exit(-1)

    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
