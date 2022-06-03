import sys
from PySide2.QtWidgets import (
    QApplication,
    QDialog,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def main() -> None:
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    sys.exit(app.exec_())


class Form(QDialog):

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("My Form")
        self.edit = QLineEdit("Write my name here...")
        self.button = QPushButton("Show Greetings")

        # Organize the widgets vertically.
        layout = QVBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(self.button)
        self.setLayout(layout)

        self.button.clicked.connect(self.greetings)

    # The "signals and slots" tutorial said to always use a Splot decorator on
    # event handlers "to avoid surprises". This tutorial ignores that, and it
    # still works. What surprises await?
    def greetings(self) -> None:
        text = self.edit.text()
        print(f"Hello {text}")


if __name__ == "__main__":
    main()
