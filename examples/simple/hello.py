import sys, os
import pprint

print(__file__)

__version__ = '1.0'

def somefunc():
    print ("Hello from py2app")

    print ("frozen: %s"%(repr(getattr(sys, "frozen", None)),))

    import __main__
    print (__main__.__file__)
    print ("sys.path: %s"%(sys.path,))
    print ("sys.executable: %s"%(sys.executable,))
    print ("sys.prefix: %s"%(sys.prefix,))
    print ("sys.argv: %s"%(sys.argv,))
    print ("os.getcwd(): %s"%(os.getcwd(),))
    pprint.pprint(dict(os.environ))
    import subprocess
    subprocess.call(["/usr/bin/say", "hello"])

if __name__ == '__main__':
    somefunc()
