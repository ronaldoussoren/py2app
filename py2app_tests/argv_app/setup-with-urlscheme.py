from setuptools import setup

# A custom plist for letting it associate with a URL protocol.
URLTYPES = [
     {
        'CFBundleURLName' : "MyUrl",
        'CFBundleURLSchemes' : [ "myurl" ]
    }
]

plist = dict(
    NSAppleScriptEnabled = 'YES',
    CFBundleIdentifier = 'com.myurl',
    LSMinimumSystemVersion = "10.4",
    CFBundleURLTypes = URLTYPES
)


setup(
    name='BasicApp',
    app=['main.py'],
    options=dict(py2app=dict(
        argv_emulation=True,
        plist=plist,
    )),
)
