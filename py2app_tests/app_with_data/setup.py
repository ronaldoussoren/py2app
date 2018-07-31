from setuptools import setup

setup(
    name='BasicApp',
    app=['main.py'],
    options = dict(py2app=dict(
        plist = dict(
            CFBundleName               = "SimpleApp",
            CFBundleShortVersionString = "1.0",
            CFBudleGetInfoString       = "SimpleApp 1.0",
        ),
        iconfile = "main.icns",
        resources = "data3/source.c",
    )),
    data_files = [
        ( 'sub1', [ 'data1/file1.txt', 'data1/file2.txt', 'data1/file3.sh' ]),
        'data2'
    ]
)
