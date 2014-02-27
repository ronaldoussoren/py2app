import sys
import ctypes
import ctypes.util


def find_library(name):
    print(ctypes.util.find_library(name))

mod = None
def _load():
    global mod
    if mod is None:
        mod = ctypes.CDLL(ctypes.util.find_library("libshared.dylib"))
    return mod

def half(v):
    return _load().half(v)

def double(v):
    return _load().doubled(v)

def square(v):
    return _load().squared(v)

def import_module(name):
    try:
        exec ("import %s"%(name,))
        m = eval(name)
    except ImportError:
        print ("* import failed")

    else:
        #for k in name.split('.')[1:]:
        #    m = getattr(m, k)
        print (m.__name__)

def print_path():
    print(sys.path)

while True:
    line = sys.stdin.readline()
    if not line:
        break

    try:
        exec (line)
    except SystemExit:
        raise

    except Exception:
        print ("* Exception " + str(sys.exc_info()[1]))

    sys.stdout.flush()
    sys.stderr.flush()
