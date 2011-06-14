from setuptools import setup

setup(
    name='BasicApp',
    app=['main.py'],
    options=dict(py2app=dict(
        emulate_shell_environment=True,
    )),
)
