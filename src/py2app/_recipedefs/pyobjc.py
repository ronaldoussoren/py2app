"""
Recipe(s) related to PyObjC
"""

import importlib
import typing

from modulegraph2 import BaseNode, Module, Package

from .._config import RecipeOptions
from .._modulegraph import ModuleGraph
from .._recipes import recipe

BINDINGS = (
    ("pyobjc-framework-AVFoundation", ["AVFAudio", "AVFoundation"]),
    ("pyobjc-framework-AVKit", ["AVKit"]),
    ("pyobjc-framework-AVRouting", ["AVRouting"]),
    ("pyobjc-framework-Accessibility", ["Accessibility"]),
    ("pyobjc-framework-Accounts", ["Accounts"]),
    ("pyobjc-framework-AdServices", ["AdServices"]),
    ("pyobjc-framework-AdSupport", ["AdSupport"]),
    ("pyobjc-framework-AddressBook", ["AddressBook"]),
    ("pyobjc-framework-AppTrackingTransparency", ["AppTrackingTransparency"]),
    ("pyobjc-framework-AppleScriptKit", ["AppleScriptKit"]),
    ("pyobjc-framework-AppleScriptObjC", ["AppleScriptObjC"]),
    (
        "pyobjc-framework-ApplicationServices",
        ["ApplicationServices", "HIServices", "PrintCore"],
    ),
    ("pyobjc-framework-AudioVideoBridging", ["AudioVideoBridging"]),
    ("pyobjc-framework-AuthenticationServices", ["AuthenticationServices"]),
    (
        "pyobjc-framework-AutomaticAssessmentConfiguration",
        ["AutomaticAssessmentConfiguration"],
    ),
    ("pyobjc-framework-Automator", ["Automator"]),
    ("pyobjc-framework-BackgroundAssets", ["BackgroundAssets"]),
    ("pyobjc-framework-BrowserEngineKit", ["BrowserEngineKit"]),
    ("pyobjc-framework-BusinessChat", ["BusinessChat"]),
    ("pyobjc-framework-CFNetwork", ["CFNetwork"]),
    ("pyobjc-framework-CalendarStore", ["CalendarStore"]),
    ("pyobjc-framework-CallKit", ["CallKit"]),
    ("pyobjc-framework-Carbon", ["Carbon"]),
    ("pyobjc-framework-Cinematic", ["Cinematic"]),
    ("pyobjc-framework-ClassKit", ["ClassKit"]),
    ("pyobjc-framework-CloudKit", ["CloudKit"]),
    (
        "pyobjc-framework-Cocoa",
        ["AppKit", "CGL", "Cocoa", "CoreFoundation", "Foundation", "PyObjCTools"],
    ),
    ("pyobjc-framework-Collaboration", ["Collaboration"]),
    ("pyobjc-framework-ColorSync", ["ColorSync"]),
    ("pyobjc-framework-Contacts", ["Contacts"]),
    ("pyobjc-framework-ContactsUI", ["ContactsUI"]),
    ("pyobjc-framework-CoreAudio", ["CoreAudio"]),
    ("pyobjc-framework-CoreAudioKit", ["CoreAudioKit"]),
    ("pyobjc-framework-CoreBluetooth", ["CoreBluetooth"]),
    ("pyobjc-framework-CoreData", ["CoreData"]),
    ("pyobjc-framework-CoreHaptics", ["CoreHaptics"]),
    ("pyobjc-framework-CoreLocation", ["CoreLocation"]),
    ("pyobjc-framework-CoreMIDI", ["CoreMIDI"]),
    ("pyobjc-framework-CoreML", ["CoreML"]),
    ("pyobjc-framework-CoreMedia", ["CoreMedia"]),
    ("pyobjc-framework-CoreMediaIO", ["CoreMediaIO"]),
    ("pyobjc-framework-CoreMotion", ["CoreMotion"]),
    ("pyobjc-framework-CoreServices", ["CoreServices"]),
    ("pyobjc-framework-CoreSpotlight", ["CoreSpotlight"]),
    ("pyobjc-framework-CoreText", ["CoreText"]),
    ("pyobjc-framework-CoreWLAN", ["CoreWLAN"]),
    ("pyobjc-framework-CryptoTokenKit", ["CryptoTokenKit"]),
    ("pyobjc-framework-DVDPlayback", ["DVDPlayback"]),
    ("pyobjc-framework-DataDetection", ["DataDetection"]),
    ("pyobjc-framework-DeviceCheck", ["DeviceCheck"]),
    ("pyobjc-framework-DictionaryServices", ["DictionaryServices"]),
    ("pyobjc-framework-DiscRecording", ["DiscRecording"]),
    ("pyobjc-framework-DiscRecordingUI", ["DiscRecordingUI"]),
    ("pyobjc-framework-DiskArbitration", ["DiskArbitration"]),
    ("pyobjc-framework-EventKit", ["EventKit"]),
    ("pyobjc-framework-ExceptionHandling", ["ExceptionHandling"]),
    ("pyobjc-framework-ExecutionPolicy", ["ExecutionPolicy"]),
    ("pyobjc-framework-ExtensionKit", ["ExtensionKit"]),
    ("pyobjc-framework-ExternalAccessory", ["ExternalAccessory"]),
    ("pyobjc-framework-FSEvents", ["FSEvents"]),
    ("pyobjc-framework-FSKit", ["FSKit"]),
    ("pyobjc-framework-FileProvider", ["FileProvider"]),
    ("pyobjc-framework-FileProviderUI", ["FileProviderUI"]),
    ("pyobjc-framework-FinderSync", ["FinderSync"]),
    ("pyobjc-framework-GameCenter", ["GameCenter"]),
    ("pyobjc-framework-GameController", ["GameController"]),
    ("pyobjc-framework-GameKit", ["GameKit"]),
    ("pyobjc-framework-GameplayKit", ["GameplayKit"]),
    ("pyobjc-framework-HealthKit", ["HealthKit"]),
    ("pyobjc-framework-IOBluetooth", ["IOBluetooth"]),
    ("pyobjc-framework-IOBluetoothUI", ["IOBluetoothUI"]),
    ("pyobjc-framework-IOSurface", ["IOSurface"]),
    ("pyobjc-framework-ImageCaptureCore", ["ImageCaptureCore"]),
    ("pyobjc-framework-InputMethodKit", ["InputMethodKit"]),
    ("pyobjc-framework-InstallerPlugins", ["InstallerPlugins"]),
    ("pyobjc-framework-InstantMessage", ["InstantMessage"]),
    ("pyobjc-framework-Intents", ["Intents"]),
    ("pyobjc-framework-IntentsUI", ["IntentsUI"]),
    ("pyobjc-framework-KernelManagement", ["KernelManagement"]),
    ("pyobjc-framework-LatentSemanticMapping", ["LatentSemanticMapping"]),
    ("pyobjc-framework-LaunchServices", ["LaunchServices"]),
    ("pyobjc-framework-LinkPresentation", ["LinkPresentation"]),
    ("pyobjc-framework-LocalAuthentication", ["LocalAuthentication"]),
    (
        "pyobjc-framework-LocalAuthenticationEmbeddedUI",
        ["LocalAuthenticationEmbeddedUI"],
    ),
    ("pyobjc-framework-MLCompute", ["MLCompute"]),
    ("pyobjc-framework-MailKit", ["MailKit"]),
    ("pyobjc-framework-MapKit", ["MapKit"]),
    ("pyobjc-framework-MediaAccessibility", ["MediaAccessibility"]),
    ("pyobjc-framework-MediaExtension", ["MediaExtension"]),
    ("pyobjc-framework-MediaLibrary", ["MediaLibrary"]),
    ("pyobjc-framework-MediaPlayer", ["MediaPlayer"]),
    ("pyobjc-framework-MediaToolbox", ["MediaToolbox"]),
    ("pyobjc-framework-Metal", ["Metal"]),
    ("pyobjc-framework-MetalFX", ["MetalFX"]),
    ("pyobjc-framework-MetalKit", ["MetalKit"]),
    ("pyobjc-framework-MetalPerformanceShaders", ["MetalPerformanceShaders"]),
    ("pyobjc-framework-MetalPerformanceShadersGraph", ["MetalPerformanceShadersGraph"]),
    ("pyobjc-framework-MetricKit", ["MetricKit"]),
    ("pyobjc-framework-ModelIO", ["ModelIO"]),
    ("pyobjc-framework-MultipeerConnectivity", ["MultipeerConnectivity"]),
    ("pyobjc-framework-NaturalLanguage", ["NaturalLanguage"]),
    ("pyobjc-framework-NetFS", ["NetFS"]),
    ("pyobjc-framework-Network", ["Network"]),
    ("pyobjc-framework-NetworkExtension", ["NetworkExtension"]),
    ("pyobjc-framework-NotificationCenter", ["NotificationCenter"]),
    ("pyobjc-framework-OSAKit", ["OSAKit"]),
    ("pyobjc-framework-OSLog", ["OSLog"]),
    ("pyobjc-framework-OpenDirectory", ["CFOpenDirectory OpenDirectory"]),
    ("pyobjc-framework-PHASE", ["PHASE"]),
    ("pyobjc-framework-PassKit", ["PassKit"]),
    ("pyobjc-framework-PencilKit", ["PencilKit"]),
    ("pyobjc-framework-Photos", ["Photos"]),
    ("pyobjc-framework-PhotosUI", ["PhotosUI"]),
    ("pyobjc-framework-PreferencePanes", ["PreferencePanes"]),
    ("pyobjc-framework-PubSub", ["PubSub"]),
    ("pyobjc-framework-PushKit", ["PushKit"]),
    ("pyobjc-framework-Quartz", ["Quartz"]),
    ("pyobjc-framework-QuickLookThumbnailing", ["QuickLookThumbnailing"]),
    ("pyobjc-framework-ReplayKit", ["ReplayKit"]),
    ("pyobjc-framework-SafariServices", ["SafariServices"]),
    ("pyobjc-framework-SafetyKit", ["SafetyKit"]),
    ("pyobjc-framework-SceneKit", ["SceneKit"]),
    ("pyobjc-framework-ScreenCaptureKit", ["ScreenCaptureKit"]),
    ("pyobjc-framework-ScreenSaver", ["ScreenSaver"]),
    ("pyobjc-framework-ScreenTime", ["ScreenTime"]),
    ("pyobjc-framework-ScriptingBridge", ["ScriptingBridge"]),
    ("pyobjc-framework-SearchKit", ["SearchKit"]),
    ("pyobjc-framework-Security", ["Security"]),
    ("pyobjc-framework-SecurityFoundation", ["SecurityFoundation"]),
    ("pyobjc-framework-SecurityInterface", ["SecurityInterface"]),
    ("pyobjc-framework-SensitiveContentAnalysis", ["SensitiveContentAnalysis"]),
    ("pyobjc-framework-ServiceManagement", ["ServiceManagement"]),
    ("pyobjc-framework-SharedWithYou", ["SharedWithYou"]),
    ("pyobjc-framework-SharedWithYouCore", ["SharedWithYouCore"]),
    ("pyobjc-framework-ShazamKit", ["ShazamKit"]),
    ("pyobjc-framework-Social", ["Social"]),
    ("pyobjc-framework-SoundAnalysis", ["SoundAnalysis"]),
    ("pyobjc-framework-Speech", ["Speech"]),
    ("pyobjc-framework-SpriteKit", ["SpriteKit"]),
    ("pyobjc-framework-StoreKit", ["StoreKit"]),
    ("pyobjc-framework-Symbols", ["Symbols"]),
    ("pyobjc-framework-SyncServices", ["SyncServices"]),
    ("pyobjc-framework-SystemConfiguration", ["SystemConfiguration"]),
    ("pyobjc-framework-SystemExtensions", ["SystemExtensions"]),
    ("pyobjc-framework-ThreadNetwork", ["ThreadNetwork"]),
    ("pyobjc-framework-UniformTypeIdentifiers", ["UniformTypeIdentifiers"]),
    ("pyobjc-framework-UserNotifications", ["UserNotifications"]),
    ("pyobjc-framework-UserNotificationsUI", ["UserNotificationsUI"]),
    ("pyobjc-framework-VideoSubscriberAccount", ["VideoSubscriberAccount"]),
    ("pyobjc-framework-VideoToolbox", ["VideoToolbox"]),
    ("pyobjc-framework-Virtualization", ["Virtualization"]),
    ("pyobjc-framework-Vision", ["Vision"]),
    ("pyobjc-framework-WebKit", ["JavaScriptCore", "WebKit"]),
    ("pyobjc-framework-iTunesLibrary", ["iTunesLibrary"]),
    ("pyobjc-framework-libdispatch", ["dispatch", "libdispatch"]),
    ("pyobjc-framework-libxpc", ["xpc"]),
)


def make_framework_recipe(dist: str, modules: typing.List[str]) -> None:
    """
    Define a recipe for handling globals in the specified
    framework bindings.
    """

    @recipe(f"{dist} globals", distribution=dist, modules=modules)
    def framework(graph: ModuleGraph, options: RecipeOptions) -> None:
        for mod in modules:
            node = graph.find_node(mod)
            if node is None:
                continue

            try:
                found = importlib.import_module(mod)  # noqa: F841
            except ImportError:
                pass

            else:
                pass
                # XXX:
                # - update globals_written of various module with names
                #   exported (this based on incoming 'in_fromlist' imports)


@recipe("objc globals", distribution="pyobjc-core", modules=["objc"])
def objc(graph: ModuleGraph, options: RecipeOptions) -> None:
    """
    Recipe for _`pyobjc-core <https://pypi.org/project/pyobjc-core`.
    """
    node = graph.find_node("objc")
    if not isinstance(node, BaseNode) or node.filename is None:
        return

    try:
        import objc  # type: ignore  # no type annotations at this point
    except ImportError:
        return

    else:
        # 'objc.__init__' contains a number of '*' imports,
        # including from an extension module.
        #
        # Update the 'globals_written' attribute with all
        # public names in the package to enable better error
        # reporting.
        assert isinstance(node, Package)
        assert isinstance(node.init_module, Module)
        node.init_module.globals_written.update(dir(objc))


# for dist, modules in BINDINGS:
#    make_framework_recipe(dist, modules)
