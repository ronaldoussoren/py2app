from setuptools import setup

setup(
    name='BasicApp',
    app=['main.py'],
    options = {
        'py2app': {
            'extra_scripts': ['helper1.py', 'helper2.py']
        }
    }
)
