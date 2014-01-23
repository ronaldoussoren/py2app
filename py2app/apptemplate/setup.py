import os
import re
import sys
import distutils.sysconfig
import distutils.util

gPreBuildVariants = [
    {
        'name': 'main-universal',
        'target': '10.5',
        'cflags': '-g -isysroot /Developer/SDKs/MacOSX10.5.sdk -arch i386 -arch ppc -arch ppc64 -arch x86_64',
        'cc': 'gcc-4.2',
    },
    {
        'name': 'main-ppc64',
        'target': '10.5',
        'cflags': '-g -isysroot /Developer/SDKs/MacOSX10.5.sdk -arch ppc64',
        'cc': 'gcc-4.2',
    },
    {
        'name': 'main-x86_64',
        'target': '10.5',
        'cflags': '-g -arch x86_64',
        'cc': '/usr/bin/clang',
    },
    {
        'name': 'main-fat3',
        'target': '10.5',
        'cflags': '-g -isysroot / -arch i386 -arch ppc -arch x86_64',
        'cc': 'gcc-4.2',
    },
    {
        'name': 'main-intel',
        'target': '10.5',
        'cflags': '-g -arch i386 -arch x86_64 -fexceptions',
        'cc': '/usr/bin/clang',
    },
    {
        'name': 'main-i386',
        'target': '10.4',
        'cflags': '-g -arch i386',
        'cc': '/usr/bin/clang',
    },
    {
        'name': 'main-ppc',
        'target': '10.3',
        'cflags': '-g -isysroot /Developer/SDKs/MacOSX10.4u.sdk -arch ppc',
        'cc': 'gcc-4.0',
    },
    {
        'name': 'main-fat',
        'target': '10.3',
        'cflags': '-g -isysroot /Developer/SDKs/MacOSX10.4u.sdk -arch i386 -arch ppc',
        'cc': 'gcc-4.0',
    },
]


def main(all=False, arch=None, secondary=False):
    basepath = os.path.dirname(__file__)
    builddir = os.path.join(basepath, 'prebuilt')
    if not os.path.exists(builddir):
        os.makedirs(builddir)
    src = os.path.join(basepath, 'src', 'main.c')

    cfg = distutils.sysconfig.get_config_vars()

    BASE_CFLAGS = cfg['CFLAGS']
    BASE_CFLAGS = BASE_CFLAGS.replace('-dynamic', '')
    while True:
        x = re.sub('-arch\s+\S+', '', BASE_CFLAGS)
        if x == BASE_CFLAGS:
            break
        BASE_CFLAGS=x

    while True:
        x = re.sub('-isysroot\s+\S+', '', BASE_CFLAGS)
        if x == BASE_CFLAGS:
            break
        BASE_CFLAGS=x

    if arch is None:
        arch = distutils.util.get_platform().split('-')[-1]
        if sys.prefix.startswith('/System') and \
            sys.version_info[:2] == (2,5):
            arch = "fat"

    name = 'main-' + arch
    root = None

    if all:
        for entry in gPreBuildVariants:
            dest = os.path.join(builddir, entry['name'])

            for replace in (0, 1):
                if replace:
                    dest = os.path.join(builddir, entry['name'].replace('main', 'secondary'))

                if not os.path.exists(dest) or (
                        os.stat(dest).st_mtime < os.stat(src).st_mtime):
                    if root is None:
                        fp = os.popen('xcode-select -print-path', 'r')
                        root = fp.read().strip()
                        fp.close()

                    print ("rebuilding %s"%(os.path.basename(dest),))

                    CC=os.path.join(root, 'usr', 'bin', entry['cc'])
                    CFLAGS = BASE_CFLAGS + ' ' + entry['cflags'].replace('@@XCODE_ROOT@@', root)
                    if replace:
                        CFLAGS += " -DPY2APP_SECONDARY"
                    os.environ['MACOSX_DEPLOYMENT_TARGET'] = entry['target']
                    os.system('"%(CC)s" -o "%(dest)s" "%(src)s" %(CFLAGS)s -framework Cocoa' % locals())

    if secondary:
        name = 'secondary-'
    else:
        name = 'main-'

    dest = os.path.join(
            builddir,
            name + arch
    )

    return dest


if __name__ == '__main__':
    main(all=True)
