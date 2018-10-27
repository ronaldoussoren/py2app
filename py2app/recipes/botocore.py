def check(cmd, mf):
    m = mf.findNode('botocore')
    if m is None or m.filename is None:
        return None

    # Botocore contains embedded data files and
    # references those using filesystem APIs.
    # Include the entire package in the app bundle,
    # and outside of site-packages.zip.
    return dict(
        packages=['botocore'],
    )
