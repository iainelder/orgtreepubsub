import sys
from PySide2.QtWidgets import QApplication, QPushButton
from PySide2.QtCore import Slot

# Greetings
@Slot()
def say_hello() -> None:
    print("Button clicked, Hello!")

# Create the Qt Application
app = QApplication(sys.argv)

# Create a button
button = QPushButton("Click me")

# Connect the button to the function
button.clicked.connect(say_hello)

# Show the button
button.show()
# Run the main Qt loop
app.exec_()
