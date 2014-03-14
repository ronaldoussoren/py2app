import sys
from PySide import QtGui
import platform

# We instantiate a QApplication passing the arguments of the script to it:
a = QtGui.QApplication(sys.argv)

# Add a basic widget to this application:
# The first argument is the text we want this QWidget to show, the second
# one is the parent widget. Since Our "hello" is the only thing we use (the
# so-called "MainWidget", it does not have a parent.
hello = QtGui.QLabel("<h2>Hello, World</h2>")

# ... and that it should be shown.
hello.show()

# Now we can start it.
a.exec_()
