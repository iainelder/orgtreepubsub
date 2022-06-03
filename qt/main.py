from pathlib import Path
from PySide2.QtWidgets import QApplication
from PySide2.QtQuick import QQuickView
from PySide2.QtCore import QUrl

root_path = Path(__file__).parent
view_path = root_path / "view.qml"

app = QApplication([])
view = QQuickView()
url = QUrl(str(view_path))

# From the tutorial: "If you are programming for desktop, you should consider
# adding view.setResizeMode(QQuickView.SizeRootObjectToView) before showing the
# view." Doing so makes the view fill the window when you resize it, like the
# sticky setting in Tkinter.
view.setResizeMode(QQuickView.SizeRootObjectToView)
view.setSource(url)
view.show()
app.exec_()
