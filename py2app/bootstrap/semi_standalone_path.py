def _update_path():
    import os, sys
    resources = os.environ['RESOURCEPATH']
    sys.path.append(os.path.join(
        resources, 'lib', 'python%d.%d'%(sys.version_info[:2]), 'lib-dynload'))
    sys.path.append(os.path.join(
        resources, 'lib', 'python%d.%d'%(sys.version_info[:2])))

_update_path()
