from setuptools import setup, Command, Extension
from distutils.command import build_ext as mod_build_ext

from distutils.sysconfig import get_config_var
from distutils.version import LooseVersion
import subprocess
import os
import shutil
import platform
import shlex
import re
import sys

class sharedlib (Command):
    description = "build a shared library"
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

        cmd = cc + arch_flags + root_flags + ['-dynamiclib', '-o', os.path.abspath('lib/libshared.1.dylib'), 'src/sharedlib.c']
        subprocess.check_call(cmd, env=env)
        if os.path.exists('lib/libshared.dylib'):
            os.unlink('lib/libshared.dylib')
        os.symlink('libshared.1.dylib', 'lib/libshared.dylib')

        if not os.path.exists('lib/stash'):
            os.makedirs('lib/stash')

        if os.path.exists('lib/libhalf.dylib'):
            os.unlink('lib/libhalf.dylib')

        cmd = cc + arch_flags + root_flags + ['-dynamiclib', '-o', os.path.abspath('lib/libhalf.dylib'), 'src/sharedlib.c']
        subprocess.check_call(cmd, env=env)

        os.rename('lib/libhalf.dylib', 'lib/stash/libhalf.dylib')
        os.symlink('stash/libhalf.dylib', 'lib/libhalf.dylib')


class cleanup (Command):
    description = "cleanup build stuff"
    user_options = []

    def initialize_options(self): pass
    def finalize_options(self): pass

    def run(self):
        for dn in ('lib', 'build', 'dist'):
            if os.path.exists(dn):
                shutil.rmtree(dn)

        for fn in os.listdir('.'):
            if fn.endswith('.so'):
                os.unlink(fn)

setup(
    name='BasicApp',
    app=['main.py'],
    cmdclass=dict(
        sharedlib=sharedlib,
        cleanup=cleanup,
    ),
    options=dict(
        py2app=dict(
            frameworks=['lib/libshared.dylib'],
        ),
    ),
)
