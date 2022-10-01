"""
sys.argv emulation

This module starts a basic event loop to collect file- and url-open
AppleEvents. Those get converted to strings and stuffed into sys.argv.
When that is done we continue starting the application.

This is a workaround to convert scripts that expect filenames on the
command-line to work in a GUI environment. GUI applications should not
use this feature.

NOTE: This module uses ctypes and not the Carbon modules in the stdlib
because the latter don't work in 64-bit mode and are also not available
with python 3.x.
"""

import ctypes
import struct
import sys
import time


class AEDesc(ctypes.Structure):
    _fields_ = [
        ("descKey", ctypes.c_int),
        ("descContent", ctypes.c_void_p),
    ]


class EventTypeSpec(ctypes.Structure):
    _fields_ = [
        ("eventClass", ctypes.c_int),
        ("eventKind", ctypes.c_uint),
    ]


def _ctypes_setup() -> ctypes.CDLL:
    carbon = ctypes.CDLL("/System/Library/Carbon.framework/Carbon")

    # timer_func = ctypes.CFUNCTYPE(
    #        None, ctypes.c_void_p, ctypes.c_long)

    ae_callback = ctypes.CFUNCTYPE(
        ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
    )
    carbon.AEInstallEventHandler.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ae_callback,
        ctypes.c_void_p,
        ctypes.c_char,
    ]
    carbon.AERemoveEventHandler.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ae_callback,
        ctypes.c_char,
    ]

    carbon.AEProcessEvent.restype = ctypes.c_int
    carbon.AEProcessEvent.argtypes = [ctypes.c_void_p]

    carbon.ReceiveNextEvent.restype = ctypes.c_int
    carbon.ReceiveNextEvent.argtypes = [
        ctypes.c_long,
        ctypes.POINTER(EventTypeSpec),
        ctypes.c_double,
        ctypes.c_char,
        ctypes.POINTER(ctypes.c_void_p),
    ]

    carbon.AEGetParamDesc.restype = ctypes.c_int
    carbon.AEGetParamDesc.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(AEDesc),
    ]

    carbon.AECountItems.restype = ctypes.c_int
    carbon.AECountItems.argtypes = [
        ctypes.POINTER(AEDesc),
        ctypes.POINTER(ctypes.c_long),
    ]

    carbon.AEGetNthDesc.restype = ctypes.c_int
    carbon.AEGetNthDesc.argtypes = [
        ctypes.c_void_p,
        ctypes.c_long,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]

    carbon.AEGetDescDataSize.restype = ctypes.c_int
    carbon.AEGetDescDataSize.argtypes = [ctypes.POINTER(AEDesc)]

    carbon.AEGetDescData.restype = ctypes.c_int
    carbon.AEGetDescData.argtypes = [
        ctypes.POINTER(AEDesc),
        ctypes.c_void_p,
        ctypes.c_int,
    ]

    carbon.FSRefMakePath.restype = ctypes.c_int
    carbon.FSRefMakePath.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]

    return carbon


def _run_argvemulator(timeout: float = 60.0) -> None:

    # Configure ctypes
    carbon = _ctypes_setup()

    # Is the emulator running?
    running = True

    # Configure AppleEvent handlers
    ae_callback = ctypes.CFUNCTYPE(
        ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
    )

    (kAEInternetSuite,) = struct.unpack(">i", b"GURL")
    (kAEISGetURL,) = struct.unpack(">i", b"GURL")
    (kCoreEventClass,) = struct.unpack(">i", b"aevt")
    (kAEOpenApplication,) = struct.unpack(">i", b"oapp")
    (kAEOpenDocuments,) = struct.unpack(">i", b"odoc")
    (keyDirectObject,) = struct.unpack(">i", b"----")
    (typeAEList,) = struct.unpack(">i", b"list")
    (typeChar,) = struct.unpack(">i", b"TEXT")
    (typeFSRef,) = struct.unpack(">i", b"fsrf")
    FALSE = b"\0"
    TRUE = b"\1"
    eventLoopTimedOutErr = -9875

    (kEventClassAppleEvent,) = struct.unpack(">i", b"eppc")
    kEventAppleEvent = 1

    @ae_callback
    def open_app_handler(
        message: ctypes.c_int, reply: ctypes.c_void_p, refcon: ctypes.c_void_p
    ) -> ctypes.c_void_p:
        # Got a kAEOpenApplication event, which means we can
        # start up. On some OSX versions this event is even
        # sent when an kAEOpenDocuments or kAEOpenURLs event
        # is sent later on.
        #
        # Therefore don't set running to false, but reduce the
        # timeout to at most two seconds beyond the current time.
        nonlocal timeout
        timeout = min(timeout, time.time() - start + 2)
        return ctypes.c_void_p(0)

    carbon.AEInstallEventHandler(
        kCoreEventClass, kAEOpenApplication, open_app_handler, 0, FALSE
    )

    @ae_callback
    def open_file_handler(
        message: ctypes.c_int, reply: ctypes.c_void_p, refcon: ctypes.c_void_p
    ) -> ctypes.c_void_p:
        nonlocal running
        listdesc = AEDesc()
        sts = carbon.AEGetParamDesc(
            message, keyDirectObject, typeAEList, ctypes.byref(listdesc)
        )
        if sts != 0:
            print("argvemulator warning: cannot unpack open document event")
            running = False
            return ctypes.c_void_p(0)

        item_count = ctypes.c_long()
        sts = carbon.AECountItems(ctypes.byref(listdesc), ctypes.byref(item_count))
        if sts != 0:
            print("argvemulator warning: cannot unpack open document event")
            running = False
            return ctypes.c_void_p(0)

        desc = AEDesc()
        for i in range(item_count.value):
            sts = carbon.AEGetNthDesc(
                ctypes.byref(listdesc), i + 1, typeFSRef, 0, ctypes.byref(desc)
            )
            if sts != 0:
                print("argvemulator warning: cannot unpack open document event")
                running = False
                return ctypes.c_void_p(0)

            sz = carbon.AEGetDescDataSize(ctypes.byref(desc))
            buf = ctypes.create_string_buffer(sz)
            sts = carbon.AEGetDescData(ctypes.byref(desc), buf, sz)
            if sts != 0:
                print("argvemulator warning: cannot extract open document event")
                continue

            fsref = buf

            buf = ctypes.create_string_buffer(1024)
            sts = carbon.FSRefMakePath(ctypes.byref(fsref), buf, 1023)
            if sts != 0:
                print("argvemulator warning: cannot extract open document event")
                continue

            sys.argv.append(buf.value.decode("utf-8"))

        running = False
        return ctypes.c_void_p(0)

    carbon.AEInstallEventHandler(
        kCoreEventClass, kAEOpenDocuments, open_file_handler, 0, FALSE
    )

    @ae_callback
    def open_url_handler(
        message: ctypes.c_int, reply: ctypes.c_void_p, refcon: ctypes.c_void_p
    ) -> ctypes.c_void_p:
        nonlocal running

        listdesc = AEDesc()
        ok = carbon.AEGetParamDesc(
            message, keyDirectObject, typeAEList, ctypes.byref(listdesc)
        )
        if ok != 0:
            print("argvemulator warning: cannot unpack open document event")
            running = False
            return ctypes.c_void_p(0)

        item_count = ctypes.c_long()
        sts = carbon.AECountItems(ctypes.byref(listdesc), ctypes.byref(item_count))
        if sts != 0:
            print("argvemulator warning: cannot unpack open url event")
            running = False
            return ctypes.c_void_p(0)

        desc = AEDesc()
        for i in range(item_count.value):
            sts = carbon.AEGetNthDesc(
                ctypes.byref(listdesc), i + 1, typeChar, 0, ctypes.byref(desc)
            )
            if sts != 0:
                print("argvemulator warning: cannot unpack open URL event")
                running = False
                return ctypes.c_void_p(0)

            sz = carbon.AEGetDescDataSize(ctypes.byref(desc))
            buf = ctypes.create_string_buffer(sz)
            sts = carbon.AEGetDescData(ctypes.byref(desc), buf, sz)
            if sts != 0:
                print("argvemulator warning: cannot extract open URL event")

            else:
                sys.argv.append(buf.value.decode("utf-8"))

        running = False
        return ctypes.c_void_p(0)

    carbon.AEInstallEventHandler(
        kAEInternetSuite, kAEISGetURL, open_url_handler, 0, FALSE
    )

    # Remove the funny -psn_xxx_xxx argument
    if len(sys.argv) > 1 and sys.argv[1].startswith("-psn_"):
        del sys.argv[1]

    start = time.time()
    now = time.time()
    eventType = EventTypeSpec()
    eventType.eventClass = kEventClassAppleEvent
    eventType.eventKind = kEventAppleEvent

    while running and now - start < timeout:
        event = ctypes.c_void_p()

        sts = carbon.ReceiveNextEvent(
            1,
            ctypes.byref(eventType),
            start + timeout - now,
            TRUE,
            ctypes.byref(event),
        )

        if sts == eventLoopTimedOutErr:
            break

        elif sts != 0:
            print("argvemulator warning: fetching events failed")
            break

        sts = carbon.AEProcessEvent(event)
        if sts != 0:
            print("argvemulator warning: processing events failed")
            break

    carbon.AERemoveEventHandler(
        kCoreEventClass, kAEOpenApplication, open_app_handler, FALSE
    )
    carbon.AERemoveEventHandler(
        kCoreEventClass, kAEOpenDocuments, open_file_handler, FALSE
    )
    carbon.AERemoveEventHandler(kAEInternetSuite, kAEISGetURL, open_url_handler, FALSE)


def _argv_emulation() -> None:
    import os

    # only use if started by LaunchServices
    if os.environ.get("_PY2APP_LAUNCHED_"):
        _run_argvemulator()


_argv_emulation()
