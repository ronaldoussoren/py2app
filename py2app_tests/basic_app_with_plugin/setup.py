from setuptools import setup, Command
from distutils.sysconfig import get_config_var
from distutils.version import LooseVersion
import subprocess
import os
import glob
import shutil
import platform
import shlex
import re
import sys

PLUGIN_NAMES = ['dummy1.qlgenerator', 'dummy2.mdimporter']

class pluginexe (Command):
    description = "Generate dummy plugin executables"
    user_options = []

    def initialize_options(self): pass
    def finalize_options(self): pass

    def run(self):
        if LooseVersion(platform.mac_ver()[0]) < LooseVersion('10.7'):
            cc = [get_config_var('CC')]
            env = dict(os.environ)
            env['MACOSX_DEPLOYMENT_TARGET'] = get_config_var('MACOSX_DEPLOYMENT_TARGET')
        else:
            cc = ['xcrun', 'clang']
            env = dict(os.environ)
            env['MACOSX_DEPLOYMENT_TARGET'] = get_config_var('MACOSX_DEPLOYMENT_TARGET')


        if not os.path.exists('lib'):
            os.mkdir('lib')
        cflags = get_config_var('CFLAGS')
        arch_flags = sum([shlex.split(x) for x in re.findall('-arch\s+\S+', cflags)], [])
        root_flags = sum([shlex.split(x) for x in re.findall('-isysroot\s+\S+', cflags)], [])


        for plugin_name in PLUGIN_NAMES:
            cmd = cc + arch_flags + root_flags + ['-dynamiclib', '-o', plugin_name, 'plugin.c']
            subprocess.check_call(cmd, env=env)


class cleanup (Command):
    description = "cleanup build stuff"
    user_options = []

    def initialize_options(self): pass
    def finalize_options(self): pass

    def run(self):
        for dn in ['build', 'dist']:
            if os.path.exists(dn):
                shutil.rmtree(dn)

        for fn in PLUGIN_NAMES:
            if os.path.exists(fn):
                os.unlink(fn)


setup(
    name='BasicApp',
    app=['main.py'],
    options=dict(
        py2app=dict(
            include_plugins=['dummy1.qlgenerator', 'dummy2.mdimporter'],
        )
    ),
    cmdclass=dict(
        pluginexe=pluginexe,
        cleanup=cleanup,
    ),
)
