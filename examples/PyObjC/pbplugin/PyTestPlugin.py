from Foundation import NSObject
import objc
import sys


class PyTestPlugin(NSObject):
    """docstring"""

    def init(self):
        self = super().init()
        print("class load!!")
        print("Hello from py2app")
        print("frozen", repr(getattr(sys, "frozen", None)))
        return self


class PyTestPlugin2(NSObject):
    """docstring"""

    pass


print("PyTestPlugin", __name__)
print(f"[inside] currentBundle {objc.currentBundle()!r}")
