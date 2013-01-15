from setuptools import setup

setup(
    name='BasicApp',
    app=['main.py'],
    options=dict(
        py2app=dict(
            include_plugins=['dummy1.qlgenerator', 'dummy2.mdimporter'],
        )
    )
)
