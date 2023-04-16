import sys
import typing

import py2app

__all__ = ["infoPlistDict"]


def infoPlistDict(CFBundleExecutable: str, plist: typing.Optional[dict] = None) -> dict:
    if plist is None:
        plist = {}
    CFBundleExecutable = CFBundleExecutable
    NSPrincipalClass = "".join(CFBundleExecutable.split())
    version = ".".join(map(str, sys.version_info[:2]))
    pdict = {
        "CFBundleDevelopmentRegion": "English",
        "CFBundleDisplayName": plist.get("CFBundleName", CFBundleExecutable),
        "CFBundleExecutable": CFBundleExecutable,
        "CFBundleIconFile": CFBundleExecutable,
        "CFBundleIdentifier": f"org.pythonmac.unspecified.{NSPrincipalClass}",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": CFBundleExecutable,
        "CFBundlePackageType": "BNDL",
        "CFBundleShortVersionString": plist.get("CFBundleVersion", "0.0"),
        "CFBundleSignature": "????",
        "CFBundleVersion": "0.0",
        "LSHasLocalizedDisplayName": False,
        "NSAppleScriptEnabled": False,
        "NSHumanReadableCopyright": "Copyright not specified",
        "NSMainNibFile": "MainMen",
        "NSPrincipalClass": NSPrincipalClass,
        "PyMainFileNames": ["__boot__"],
        "PyResourcePackages": [
            (s % version)
            for s in [
                "lib/python%s",
                "lib/python%s/lib-dynload",
                "lib/python%s/site-packages.zip",
            ]
        ]
        + ["lib/python%s.zip" % version.replace(".", "")],
        "PyRuntimeLocations": [
            (s % version)
            for s in [
                (
                    "@executable_path/../Frameworks/Python.framework"
                    "/Versions/%s/Python"
                ),
                "~/Library/Frameworks/Python.framework/Versions/%s/Python",
                "/Library/Frameworks/Python.framework/Versions/%s/Python",
                "/Network/Library/Frameworks/Python.framework/Versions/%s/Python",
                "/System/Library/Frameworks/Python.framework/Versions/%s/Python",
            ]
        ],
    }
    pdict.update(plist)
    pythonInfo = pdict.setdefault("PythonInfoDict", {})
    pythonInfo.update(
        {
            "PythonLongVersion": sys.version,
            "PythonShortVersion": ".".join(str(x) for x in sys.version_info[:2]),
            "PythonExecutable": sys.executable,
        }
    )
    py2appInfo = pythonInfo.setdefault("py2app", {})
    py2appInfo.update({"version": py2app.__version__, "template": "bundle"})
    return pdict
