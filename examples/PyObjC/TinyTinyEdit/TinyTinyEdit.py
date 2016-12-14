"""TinyTinyEdit -- A minimal Document-based Cocoa application."""

from Cocoa import NSDocument
from PyObjCTools import AppHelper
import objc
import sys

class TinyTinyDocument(NSDocument):
    textView = objc.IBOutlet()

    path = None

    def windowNibName(self):
        return "TinyTinyDocument"

    def readFromFile_ofType_(self, path, tp):
        if self.textView is None:
            # we're not yet fully loaded
            self.path = path
        else:
            # "revert"
            self.readFromUTF8_(path)
        return True

    def writeToFile_ofType_(self, path, tp):
        f = file(path, "w")
        text = self.textView.string()
        f.write(text.encode("utf8"))
        f.close()
        return True

    def windowControllerDidLoadNib_(self, controller):
        if self.path:
            self.readFromUTF8_(self.path)
        else:
            if hasattr(sys, 'maxint'):
                maxint = sys.maxint
                maxint_label = 'maxint'
            else:
                maxint = sys.maxsize
                maxint_label = 'maxsize'

            self.textView.setString_("Welcome to TinyTinyEdit in Python\nVersion: %s\nsys.%s: %d\nbyteorder: %s\nflags: %s"%(
                sys.version, maxint_label, maxint, sys.byteorder, sys.flags))

    def readFromUTF8_(self, path):
        f = file(path)
        text = unicode(f.read(), "utf8")
        f.close()
        self.textView.setString_(text)


if __name__ == "__main__":
    AppHelper.runEventLoop()
