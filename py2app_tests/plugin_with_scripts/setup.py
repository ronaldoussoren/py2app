from setuptools import setup

plist = dict(
    NSPrincipleClass="BasicPlugin"
)

setup(
    name='BasicPlugin',
    plugin=['main.py'],
    options=dict(py2app=dict(
        extra_scripts=['helper1.py', 'helper2.py'],
        extension=".bundle",
        plist=plist,
    )),
)
