from setuptools import setup

plist = dict(
    NSPrincipleClass="BasicPlugin"
)

setup(
    name='BasicPlugin',
    plugin=['main.py'],
    options=dict(py2app=dict(
        extension=".bundle",
        plist=plist,
    )),
)
