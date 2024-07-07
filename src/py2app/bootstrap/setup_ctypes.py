def _setup_ctypes() -> None:
    import os
    import sys
    from ctypes.macholib import dyld

    frameworks = os.path.join(sys.py2app_bundle_resources, "..", "Frameworks")  # type: ignore[attr-defined]
    dyld.DEFAULT_FRAMEWORK_FALLBACK.insert(0, frameworks)
    dyld.DEFAULT_LIBRARY_FALLBACK.insert(0, frameworks)


_setup_ctypes()
