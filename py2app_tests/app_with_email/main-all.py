import sys
from email import *

def import_module(name):
    try:
        exec ("import %s"%(name,))
        m = eval(name)
    except ImportError:
        print ("* import failed")

    else:
        print (m.__name__)

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
