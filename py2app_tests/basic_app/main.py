import sys


def function():
    import decimal

def import_module(name):
    try:
        exec "import %s"%(name,)
        m = eval(name)
    except ImportError, msg:
        print "* import failed"

    else:
        for k in name.split('.')[1:]:
            m = getattr(m, k)
        print m.__name__


while True:
    line = sys.stdin.readline()
    if not line:
        break

    try:
        exec line
    except SystemExit:
        raise

    except Exception, e:
        print "* Exception", e

    sys.stdout.flush()
    sys.stderr.flush()
