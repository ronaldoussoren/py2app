import sys
import Foundation

class BasicPlugin (Foundation.NSObject):
    def performCommand_(self, cmd):
        print ("+ %s"%(cmd,))
        sys.stdout.flush()
