import sys
import traceback

if sys.version_info[0] == 3:
    def B(value):
        return value.encode('ascii')
    kAEInternetSuite=B('gurl')
    kAEISGetURL=B('gurl')
    kCoreEventClass=B('aevt')
    kAEOpenApplication=B('oapp')
    kAEOpenDocuments=B('odoc')
    keyDirectObject=B('----')

    typeAEList=B('list')
    typeChar=B('TEXT')
    typeAlias=B('alis')

    highLevelEventMask=1024 
    kHighLevelEvent=23

    #import ctypes

    # TODO: Reimplement useful bits of AE, Evt and File using ctypes,
    # when than works drop the 2.x part and use this everywhere.
else:
    from Carbon import AE
    from Carbon.AppleEvents import kCoreEventClass, kAEOpenApplication, \
        kAEOpenDocuments, keyDirectObject, typeAEList, typeAlias, \
        kAEInternetSuite, kAEISGetURL, typeChar
    from Carbon import Evt
    from Carbon import File
    from Carbon.Events import highLevelEventMask, kHighLevelEvent





def _get_argvemulator():
    """argvemulator - create sys.argv from OSA events. Used by applets that
    want unix-style arguments.
    """


    class ArgvCollector:

        """A minimal FrameWork.Application-like class"""

        def __init__(self):
            self.quitting = 0

            AE.AEInstallEventHandler(kCoreEventClass, kAEOpenApplication,
                self.__runapp)
            AE.AEInstallEventHandler(kCoreEventClass, kAEOpenDocuments,
                self.__openfiles)
            AE.AEInstallEventHandler(kAEInternetSuite, kAEISGetURL,
                    self.__geturl)

            # The definition of kAEInternetSuite seems to be wrong,
            # the lines below ensures that the code will work anyway.
            AE.AEInstallEventHandler('GURL', 'GURL', self.__geturl)

        def close(self):
            AE.AERemoveEventHandler(kCoreEventClass, kAEOpenApplication)
            AE.AERemoveEventHandler(kCoreEventClass, kAEOpenDocuments)
            AE.AERemoveEventHandler(kAEInternetSuite, kAEISGetURL)
            AE.AERemoveEventHandler('GURL', 'GURL')

        def mainloop(self, mask = highLevelEventMask, timeout = 1*60):
            # Note: this is not the right way to run an event loop in OSX or
            # even "recent" versions of MacOS9. This is however code that has
            # proven itself.

            # Remove the funny -psn_xxx_xxx argument
            if len(sys.argv) > 1 and sys.argv[1][:4] == '-psn':
                del sys.argv[1]

            stoptime = Evt.TickCount() + timeout
            while not self.quitting and Evt.TickCount() < stoptime:
                self._dooneevent(mask, timeout)

            if not self.quitting:
                print "argvemulator: timeout waiting for arguments"

            self.close()

        def _dooneevent(self, mask = highLevelEventMask, timeout = 1*60):
            got, event = Evt.WaitNextEvent(mask, timeout)
            if got:
                self._lowlevelhandler(event)

        def _lowlevelhandler(self, event):
            what, message, when, where, modifiers = event
            h, v = where
            if what == kHighLevelEvent:
                try:
                    AE.AEProcessAppleEvent(event)
                except AE.Error, err:
                    msg = "High Level Event: %r %r" % (hex(message),
                        hex(h | (v<<16)))
                    print 'AE error: ', err
                    print 'in', msg
                    traceback.print_exc()
                return
            else:
                print "Unhandled event:", event


        def _quit(self):
            self.quitting = 1

        def __runapp(self, requestevent, replyevent):
            self._quit()

        def __openfiles(self, requestevent, replyevent):
            try:
                listdesc = requestevent.AEGetParamDesc(keyDirectObject,
                    typeAEList)
                for i in range(listdesc.AECountItems()):
                    aliasdesc = listdesc.AEGetNthDesc(i+1, typeAlias)[1]
                    alias = File.Alias(rawdata=aliasdesc.data)
                    fsref = alias.FSResolveAlias(None)[0]
                    pathname = fsref.as_pathname()
                    sys.argv.append(pathname)
            except Exception, e:
                print "argvemulator.py warning: can't unpack an open document event"
                import traceback
                traceback.print_exc()

            self._quit()

        def __geturl(self, requestevent, replyevent):
            try:
                listdesc = requestevent.AEGetParamDesc(keyDirectObject, typeAEList)
                for i in range(listdesc.AECountItems()):
                    desc = listdesc.AEGetNthDesc(i+1, typeChar)[1]
                    #url = desc.data.decode('utf8')
                    url = desc.data
                    sys.argv.append(url)
            except Exception, e:
                print "argvemulator.py warning: can't unpack a GetURL event"
                import traceback
                traceback.print_exc()

            self._quit()

    return ArgvCollector()

def _argv_emulation():
    import sys
    # only use if started by LaunchServices
    for arg in sys.argv[1:]:
        if arg.startswith('-psn'):
            _get_argvemulator().mainloop()
            break
_argv_emulation()

