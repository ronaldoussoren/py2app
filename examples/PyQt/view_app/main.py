from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine

app = QGuiApplication([])
engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)
engine.load('main.qml')

app.exec_()
