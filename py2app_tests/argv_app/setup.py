from setuptools import setup

setup(
    name='BasicApp',
    app=['main.py'],
    options=dict(py2app=dict(
        argv_emulation=True,
    )),
)
