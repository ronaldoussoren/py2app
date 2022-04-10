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
NSLog("currentBundle = %r" % (objc.currentBundle(),))
PyTestPlugin = bndl.classNamed_("PyTestPlugin")
NSLog("PyTestPlugin = %r" % (PyTestPlugin,))
PyTestPlugin.alloc().init()
NSLog("currentBundle = %r" % (objc.currentBundle(),))
NSLog("paths changed: %r" % (set(sys.path) - old_path))
NSLog("new modules: %r" % (set(sys.modules) - old_modules))
