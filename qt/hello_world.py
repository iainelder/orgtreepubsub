import sys
import random
from PySide2 import QtCore, QtWidgets, QtGui

def main() -> None:
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec_())


class MyWidget(QtWidgets.QWidget):

    def __init__(self) -> None:
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel(
            "Hello World", alignment=QtCore.Qt.AlignCenter
        )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

        self.button.clicked.connect(self.magic)
    
    @QtCore.Slot()
    def magic(self) -> None:
        self.text.setText(random.choice(self.hello))


if __name__ == "__main__":
    main()
