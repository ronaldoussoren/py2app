from distutils.core import setup, Extension, Command
from distutils import sysconfig
from distutils.command.build_ext import build_ext
import os, shutil, re, subprocess


class my_build_ext (build_ext):
    def run(self):
        cmd = self.reinitialize_command('build_dylib')
        cmd.run()
        build_ext.run(self)


class build_dylib (Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def get_arch_flags(self):
        cflags = sysconfig.get_config_var('CFLAGS')
        result = []
        for item in re.findall('(-arch\s+\S+)', cflags):
            result.extend(item.split())
        return result

    def run(self):
        print("running build_dylib")
        bdir = 'build/libdir'
        if os.path.exists(bdir):
            shutil.rmtree(bdir)

        os.makedirs(bdir)
        cflags = self.get_arch_flags()
        cc = sysconfig.get_config_var('CC')


        subprocess.check_call([cc] + cflags + [
            '-c', '-o', os.path.join(bdir, 'libfoo.o'),
            'src/libfoo.c'])

        subprocess.check_call(['libtool',
            '-dynamic', '-o', os.path.join(bdir, 'libfoo.dylib'),
            '-install_name', os.path.abspath(os.path.join(bdir, 'libfoo.dylib')),
            os.path.join(os.path.join(bdir, 'libfoo.o'))])
        
setup(
    cmdclass = {
        'build_dylib': build_dylib,
        'build_ext': my_build_ext,
    },
    ext_modules=[
        Extension("foo", ["src/modfoo.c"],
            extra_link_args=["-L%s"%(os.path.abspath("build/libdir"),), "-lfoo"])
    ],
    options={
        'build_ext': {
            'inplace': True
        },
    },
)
