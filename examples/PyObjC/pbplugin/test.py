import os
import sys

import objc
from Foundation import NSBundle, NSLog

old_path = set(sys.path)
old_modules = set(sys.modules)
bndl = NSBundle.bundleWithPath_(os.path.abspath("dist/PyTestPlugin.pbplugin"))
NSLog(f"currentBundle = {objc.currentBundle()!r}")
PyTestPlugin = bndl.classNamed_("PyTestPlugin")
NSLog(f"PyTestPlugin = {PyTestPlugin!r}")
PyTestPlugin.alloc().init()
NSLog(f"currentBundle = {objc.currentBundle()!r}")
NSLog(f"paths changed: {set(sys.path) - old_path!r}")
NSLog(f"new modules: {set(sys.modules) - old_modules!r}")
