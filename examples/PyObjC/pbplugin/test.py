import os
import objc
from Foundation import *
import sys

try:
    set
except NameError:
    from sets import Set as set
old_path = set(sys.path)
old_modules = set(sys.modules)
bndl = NSBundle.bundleWithPath_(os.path.abspath("dist/PyTestPlugin.pbplugin"))
NSLog(f"currentBundle = {objc.currentBundle()!r}")
PyTestPlugin = bndl.classNamed_("PyTestPlugin")
NSLog(f"PyTestPlugin = {PyTestPlugin!r}")
PyTestPlugin.alloc().init()
NSLog(f"currentBundle = {objc.currentBundle()!r}")
NSLog("paths changed: %r" % (set(sys.path) - old_path))
NSLog("new modules: %r" % (set(sys.modules) - old_modules))
