from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QPushButton, QApplication
from PyQt4.QtDeclarative import QDeclarativeView

# This example uses a QML file to show a scrolling list containing
# all the items listed into dataList.

dataList = ["Item 1", "Item 2", "Item 3", "Item 4"]

app = QApplication([])
view = QDeclarativeView()

ctxt = view.rootContext()
ctxt.setContextProperty("myModel", dataList)

url = QUrl('view.qml') # <-- Problem seems to be here, the file gets copied correctly to Resources folder
view.setSource(url)
view.show()
app.exec_()
