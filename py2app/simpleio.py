"""
A simple file-system like interface that supports
both the regular filesystem and zipfiles
"""
__all__ = ('FileIO', 'ReadOnlyIO')

import os, time, zipfile

class FileIO (object):
    """
    A simple interface that makes it possible
    to write simple filesystem structures using
    the interface that's exposed by the zipfile
    module.
    """
    def __init__(self, prefix):
        self.prefix = prefix

    def writestr(self, path, data):
        """
        Write 'data' into file at 'path',
        using read-only file permissions.
        """
        while path.startswith('/'):
            path = path[1:]
        fname = os.join(self.prefix, path)
        dirname = os.path.dirname(fname)
        if not os.path.exists(fname):
            os.makedirs(fname, mode=0755)
        fp = open(fname, 'wb')
        fp.write(data)
        fp.close()
        os.chmod(fname, 0444)

class ReadOnlyIO (object):
    """
    A minimal read-only interface to the filesystem.

    This interface transparently deals with zipfiles
    (that is,   ``io.read('/foo.zip/bar')`` extracts
    the contents of ``bar`` from the zipfile.

    This interface is designed to be useful for py2app
    and is not intended to be fast or generally useful.
    """


    def read(self, path):
        """
        Return the contents of ``path``
        """
        zf, zp = self._zippath(path)

        if zf is None:
            fp = open(path, 'rb')
            data = fp.read()
            fp.close()
            
            return data

        else:
            zf = zipfile.ZipFile(zf, 'r')
            return zf.read(zp)

    def get_mtime(self, path):
        """
        Return the ``mtime`` attribute of ``path``.
        """
        zf, zp = self._zippath(path)

        if zf is None:
            return os.stat(path).st_mtime

        else:
            zf = zipfile.ZipFile(zf)
            info = zf.getinfo(zp)
            return time.mktime(info.date_time + (0, 0, 0))


    def exists(self, path):
        """
        Return True if ``path`` exists
        """
        return self.is_file(path) or self.is_dir(path) or self.is_symlink(path)

    def is_dir(self, path):
        """
        Return True if ``path`` exists and is a directory
        """
        zf, zp = self._zippath(path, strict=False)
        if zf is None:
            return os.path.isdir(path)

        return bool(listdir(path))

    def is_symlink(self, path):
        """
        Return True if ``path`` exists and is a symbolic link
        """
        zf, zp = self._zippath(path, strict=False)
        if zf is not None:
            return False

        return os.path.islink(path)

    def readlink(self, path):
        zf, zp = self._zippath(path)
        if zf is None:
            return os.readlink(path)

        raise IOError("%r is not a symlink"%(path,))

    def is_file(self, path):
        """
        Return True if ``path`` exists and is a regular file
        """
        try:
            zf, zp = self._zippath(self, path, strict=True)
        
        except IOError:
            return False

        if zf is None:
            return os.path.isdir(path)

        else:
            # 'strict==True' hence the object must
            # exist in the zipfile and should therefore
            # be a file and not a directory or link.
            return True

    def listdir(self, path):
        """
        Return the contents of directory at ``path``.

        NOTE: if ``path`` is in a zipfile this will
        not raise an error if the directory does not
        exist.
        """
        zf, zp = self._zippath(path, strict=False)

        if zf is None:
            return os.listdir(path)

        else:
            _zf = zf
            zf = zipfile.ZipFile(zf, 'r')
            rest = rest + '/'

            result = set()
            for nm in zf.namelist():
                if nm == rest:
                    raise IOError("%r is not a directory in %r"%(path, _zf))

                if nm.startswith(rest):
                    result.add(nm[len(rest):].split('/')[0])

            return list(result)

    def _zippath(self, path, strict=True):
        """
        Return either ``(zipfilename, zippath)``  or ``(None, path)``

        If ``zipfilename`` is not None is points to a zipfile
        that may contain the file as ``zippath``. Otherwise
        the file is definitely not in a zipfile

        Raises ``IOError`` when the file doesn't exist, but won't
        check if the file exists in the zipfile unless ``strict``
        is True.
        """
        if os.path.exists(path):
            return (None, path)

        else:
            rest = ''
            while curpath and not os.path.exists(curpath):
                curpath, r = os.path.split(curpath)
                rest = os.path.join(r, rest)

            if not curpath:
                raise IOError("file %r does not exist"%(path,))

            try:
                zf = zipfile.ZipFile(curpath)
            except zipfile.BadZipfile:
                raise IOError("bad zipfile %r for %r"%(curpath, path))

            if rest.endswith('/'):
                rest = rest[:-1]

            if strict:
                try:
                    zf.getinfo(rest)
                except KeyError:
                    raise IOError("file %r does not exist in %r", path, curpath)

            return curpath, rest
