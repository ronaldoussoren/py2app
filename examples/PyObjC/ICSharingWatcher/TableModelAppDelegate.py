import os
from Cocoa import *
import objc
import leases

FILENAME = '/var/db/dhcpd_leases'

def getLeases(fn):
    if os.path.exists(fn):
        lines = file(fn, 'U')
    else:
        lines = leases.EXAMPLE.splitlines()
    return list(leases.leases(lines))

class TableModelAppDelegate (NSObject):
    mainWindow = objc.IBOutlet()

    def awakeFromNib(self):
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(1.0, self, 'pollLeases:', {}, True)

    def pollLeases_(self, timer):
        if not os.path.exists(FILENAME):
            return
        d = timer.userInfo()
        newtime = os.stat(FILENAME).st_mtime
        oldtime = d.get('st_mtime', 0)
        if newtime > oldtime:
            d['st_mtime'] = newtime
            self.setLeases_(getLeases(FILENAME))

    def leases(self):
        if not hasattr(self, '_cachedleases'):
            self._cachedleases = getLeases(FILENAME)
        return self._cachedleases

    def setLeases_(self, leases):
        self._cachedleases = leases

    def windowWillClose_(self, sender):
        if sender is self.mainWindow:
            NSApp().terminate()
