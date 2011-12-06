"""
sys.argv emulation

This module starts a basic event loop to collect file- and url-open AppleEvents. Those get
converted to strings and stuffed into sys.argv. When that is done we continue starting 
the application.

This is a workaround to convert scripts that expect filenames on the command-line to work 
in a GUI environment. GUI applications should not use this feature.

NOTE: This module uses ctypes and not the Carbon modules in the stdlib because the latter
don't work in 64-bit mode and are also not available with python 3.x.
"""

import sys
import os

if sys.version_info[0] == 3:
    def B(value):
        return value.encode('ascii')
else:
    def B(value):
        return value

import ctypes
import struct

class AEDesc (ctypes.Structure):
    _fields_ = [
        ('descKey', ctypes.c_int),
        ('descContent', ctypes.c_void_p),
    ]

def _ctypes_setup():
    carbon = ctypes.CDLL('/System/Library/Carbon.framework/Carbon')
    cf = ctypes.CDLL('/System/Library/CoreFoundation.framework/CoreFoundation')

    timer_func = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_long)

    cf.CFAbsoluteTimeGetCurrent.restype = ctypes.c_double
    cf.CFRunLoopTimerCreate.restype = ctypes.c_void_p
    cf.CFRunLoopTimerCreate.argtypes = [
            ctypes.c_void_p,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_long,
            ctypes.c_long,
            timer_func,
            ctypes.c_long,
        ]
    cf.CFRelease.argtypes = [ctypes.c_void_p]
    cf.CFRunLoopGetCurrent.restype = ctypes.c_void_p
    cf.CFRunLoopAddTimer.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    cf.CFRunLoopRemoveTimer.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

    ae_callback = ctypes.CFUNCTYPE(ctypes.c_short, ctypes.c_void_p, 
        ctypes.c_void_p, ctypes.c_void_p)
    carbon.AEInstallEventHandler.argtypes = [ 
            ctypes.c_int, ctypes.c_int, ae_callback,
            ctypes.c_void_p, ctypes.c_char ]
    carbon.AERemoveEventHandler.argtypes = [ 
            ctypes.c_int, ctypes.c_int, ae_callback,
            ctypes.c_char ]

    
    carbon.AEGetParamDesc.restype = ctypes.c_int
    carbon.AEGetParamDesc.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(AEDesc)]

    carbon.AECountItems.restype = ctypes.c_int
    carbon.AECountItems.argtypes = [ ctypes.POINTER(AEDesc),
            ctypes.POINTER(ctypes.c_long) ]

    carbon.AEGetNthDesc.restype = ctypes.c_int
    carbon.AEGetNthDesc.argtypes = [ 
            ctypes.c_void_p, ctypes.c_long, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_void_p ]

    carbon.AEGetDescDataSize.restype = ctypes.c_int
    carbon.AEGetDescDataSize.argtypes = [ ctypes.POINTER(AEDesc) ]

    carbon.AEGetDescData.restype = ctypes.c_int
    carbon.AEGetDescData.argtypes = [ 
            ctypes.POINTER(AEDesc),
            ctypes.c_void_p,
            ctypes.c_int,
            ]


    carbon.FSRefMakePath.restype = ctypes.c_int
    carbon.FSRefMakePath.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]

    return carbon, cf

def _run_argvemulator(timeout = 60):
    if int(os.uname()[2].split('.')[0]) < 10 and sys.maxint > 2**32:
        # See https://bitbucket.org/ronaldoussoren/py2app/issue/28
        print >>sys.stderr, "argv emulator doesn't work in 64-bit on OSX < 10.6"
        return
    

    # Configure ctypes
    carbon, cf = _ctypes_setup()

    # Global variables
    kCFRunLoopCommonModes = ctypes.c_void_p.in_dll(cf, 'kCFRunLoopCommonModes')

    # Create a timer that will exit the temporary runloop when we 
    # don't find arguments soon enough.
    timer_func = cf.CFRunLoopTimerCreate.argtypes[5]

    @timer_func
    def delayedQuit(runloop, info):
        carbon.QuitApplicationEventLoop()


    qtimer = cf.CFRunLoopTimerCreate(
        0,
        cf.CFAbsoluteTimeGetCurrent() + timeout,
        0, 
        0, 
        0,
        delayedQuit,
        0,
    )
    cf.CFRunLoopAddTimer(cf.CFRunLoopGetCurrent(), qtimer, kCFRunLoopCommonModes)

    # Configure AppleEvent handlers
    ae_callback = carbon.AEInstallEventHandler.argtypes[2]

    kAEInternetSuite,   = struct.unpack('>i', B('GURL'))
    kAEISGetURL,        = struct.unpack('>i', B('GURL'))
    kCoreEventClass,    = struct.unpack('>i', B('aevt'))
    kAEOpenApplication, = struct.unpack('>i', B('oapp'))
    kAEOpenDocuments,   = struct.unpack('>i', B('odoc'))
    keyDirectObject,    = struct.unpack('>i', B('----'))
    typeAEList,         = struct.unpack('>i', B('list'))
    typeChar,           = struct.unpack('>i', B('TEXT'))
    typeFSRef,          = struct.unpack('>i', B('fsrf'))
    FALSE               = B('\0')


    @ae_callback
    def open_app_handler(message, reply, refcon):
        carbon.QuitApplicationEventLoop()
        return 0

    carbon.AEInstallEventHandler(kCoreEventClass, kAEOpenApplication,
            open_app_handler, 0, FALSE)

    @ae_callback
    def open_file_handler(message, reply, refcon):
        listdesc = AEDesc()
        sts = carbon.AEGetParamDesc(message, keyDirectObject, typeAEList,
                ctypes.byref(listdesc))
        if sts != 0:
            print >>sys.stderr, "argvemulator warning: cannot unpack open document event"
            carbon.QuitApplicationEventLoop()
            return

        item_count = ctypes.c_long()
        sts = carbon.AECountItems(ctypes.byref(listdesc), ctypes.byref(item_count))
        if sts != 0:
            print >>sys.stderr, "argvemulator warning: cannot unpack open document event"
            carbon.QuitApplicationEventLoop()
            return

        desc = AEDesc()
        for i in range(item_count.value):
            sts = carbon.AEGetNthDesc(ctypes.byref(listdesc), i+1, typeFSRef, 0, ctypes.byref(desc))
            if sts != 0:
                print >>sys.stderr, "argvemulator warning: cannot unpack open document event"
                carbon.QuitApplicationEventLoop()
                return

            sz = carbon.AEGetDescDataSize(ctypes.byref(desc))
            buf = ctypes.create_string_buffer(sz)
            sts = carbon.AEGetDescData(ctypes.byref(desc), buf, sz)
            if sts != 0:
                print >>sys.stderr, "argvemulator warning: cannot extract open document event"
                continue

            fsref = buf

            buf = ctypes.create_string_buffer(1024)
            sts = carbon.FSRefMakePath(ctypes.byref(fsref), buf, 1023)
            if sts != 0:
                print >>sys.stderr, "argvemulator warning: cannot extract open document event"
                continue

            print >>sys.stderr, "Adding: %s"%(repr(buf.value.decode('utf-8')),)

            if sys.version_info[0] > 2:
                sys.argv.append(buf.value.decode('utf-8'))
            else:
                sys.argv.append(buf.value)

        carbon.QuitApplicationEventLoop()
        return 0

    carbon.AEInstallEventHandler(kCoreEventClass, kAEOpenDocuments,
            open_file_handler, 0, FALSE)

    @ae_callback
    def open_url_handler(message, reply, refcon):
        listdesc = AEDesc()
        ok = carbon.AEGetParamDesc(message, keyDirectObject, typeAEList,
                ctypes.byref(listdesc))
        if ok != 0:
            print >>sys.stderr, "argvemulator warning: cannot unpack open document event"
            carbon.QuitApplicationEventLoop()
            return

        item_count = ctypes.c_long()
        sts = carbon.AECountItems(ctypes.byref(listdesc), ctypes.byref(item_count))
        if sts != 0:
            print >>sys.stderr, "argvemulator warning: cannot unpack open url event"
            carbon.QuitApplicationEventLoop()
            return

        desc = AEDesc()
        for i in range(item_count.value):
            sts = carbon.AEGetNthDesc(ctypes.byref(listdesc), i+1, typeChar, 0, ctypes.byref(desc))
            if sts != 0:
                print >>sys.stderr, "argvemulator warning: cannot unpack open URL event"
                carbon.QuitApplicationEventLoop()
                return

            sz = carbon.AEGetDescDataSize(ctypes.byref(desc))
            buf = ctypes.create_string_buffer(sz)
            sts = carbon.AEGetDescData(ctypes.byref(desc), buf, sz)
            if sts != 0:
                print >>sys.stderr, "argvemulator warning: cannot extract open URL event"

            else:
                if sys.version_info[0] > 2:
                    sys.argv.append(buf.value.decode('utf-8'))
                else:
                    sys.argv.append(buf.value)

        carbon.QuitApplicationEventLoop()
        return 0
    
    carbon.AEInstallEventHandler(kAEInternetSuite, kAEISGetURL,
            open_url_handler, 0, FALSE)



    # Remove the funny -psn_xxx_xxx argument
    if len(sys.argv) > 1 and sys.argv[1][:4] == '-psn':
        del sys.argv[1]

    # Now run the eventloop to collect arguments
    carbon.RunApplicationEventLoop()

    # Clean up 
    cf.CFRunLoopRemoveTimer(
            cf.CFRunLoopGetCurrent(), qtimer, kCFRunLoopCommonModes)
    cf.CFRelease(qtimer)

    carbon.AERemoveEventHandler(kCoreEventClass, kAEOpenApplication, 
            open_app_handler, FALSE)
    carbon.AERemoveEventHandler(kCoreEventClass, kAEOpenDocuments,
            open_file_handler, FALSE)
    carbon.AERemoveEventHandler(kAEInternetSuite, kAEISGetURL,
            open_url_handler, FALSE)

def _argv_emulation():
    import sys
    # only use if started by LaunchServices
    for arg in sys.argv[1:]:
        if arg.startswith('-psn'):
            _run_argvemulator()
            break
_argv_emulation()
