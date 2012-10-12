def _site_packages(prefix, real_prefix, global_site_packages):
    import site, sys, os
    paths = []
    prefixes = [sys.prefix]

    paths.append(os.path.join(prefix, 'lib', 'python' + sys.version[:3],
        'site-packages'))
    if os.path.join('.framework', '') in os.path.join(prefix, ''):
        home = os.environ.get('HOME')
        if home:
            paths.append(os.path.join(home, 'Library', 'Python',
                sys.version[:3], 'site-packages'))


    # Work around for a misfeature in setuptools: easy_install.pth places
    # site-packages way to early on sys.path and that breaks py2app bundles.
    # NOTE: this is hacks into an undocumented feature of setuptools and
    # might stop to work without warning.
    sys.__egginsert = len(sys.path)

    for path in paths:
        site.addsitedir(path)


    # Ensure that the global site packages get placed on sys.path after
    # the site packages from the virtual environment (this functionality
    # is also in virtualenv)
    sys.__egginsert = len(sys.path)

    if global_site_packages:
        site.addsitedir(os.path.join(real_prefix, 'lib', 'python' + sys.version[:3],
            'site-packages'))
