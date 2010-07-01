import os
import re
import distutils.sysconfig
import distutils.util

gPreBuildVariants = [
    {
        'name': 'main-universal',
        'target': '10.5',
        'cflags': '-isysroot /Developer/SDKs/MacOSX10.5.sdk -arch i386 -arch ppc -arch ppc64 -arch x86_64',
        'cc': 'gcc-4.2',
    },
    {
        'name': 'main-fat3',
        'target': '10.5',
        'cflags': '-isysroot / -arch i386 -arch ppc -arch x86_64',
        'cc': 'gcc-4.2',
    },
    {
        'name': 'main-intel',
        'target': '10.5',
        'cflags': '-isysroot / -arch i386 -arch x86_64',
        'cc': 'gcc-4.2',
    },
    {
        'name': 'main-32bit',
        'target': '10.3',
        'cflags': '-isysroot /Developer/SDKs/MacOSX10.4u.sdk -arch i386 -arch ppc',
        'cc': 'gcc-4.0',
    },
]


def main():
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

    for entry in gPreBuildVariants:
        CC=entry['cc']
        CFLAGS = BASE_CFLAGS + ' ' + entry['cflags']
        os.environ['MACOSX_DEPLOYMENT_TARGET'] = entry['target']
        dest = os.path.join(builddir, entry['name'])
        if not os.path.exists(dest) or (
                os.stat(dest).st_mtime < os.stat(src).st_mtime):
            os.system('"%(CC)s" -arch i386 -arch ppc -o "%(dest)s" "%(src)s" %(CFLAGS)s' % locals())

    dest = os.path.join(
            builddir,
            'main-' + distutils.util.get_platform().split('-')[-1]
    )

    return dest


if __name__ == '__main__':
    main()
