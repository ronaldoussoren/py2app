import sys

import Foundation


class BasicPlugin(Foundation.NSObject):
    def performCommand_(self, cmd):
        print(f"+ {cmd}")
        sys.stdout.flush()
