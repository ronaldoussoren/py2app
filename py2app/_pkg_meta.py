import os

IGNORED_DISTINFO = set(["installed-files.txt", "RECORD"])  # noqa: C405


def update_metadata_cache(infos, dist_info_path):
    """
    Update mapping from filename to dist_info directory
    for all files installed by the package described
    in dist_info
    """
    fn = os.path.join(dist_info_path, "installed-files.txt")
    if os.path.exists(fn):
        with open(fn, "r") as stream:
            for line in stream:
                infos[
                    os.path.realpath(os.path.join(dist_info_path, line.rstrip()))
                ] = dist_info_path

    fn = os.path.join(dist_info_path, "RECORD")
    if os.path.exists(fn):
        with open(fn, "r") as stream:
            for ln in stream:
                # The RECORD file is a CSV file according to PEP 376, but
                # the wheel spec is silent on this and the wheel tool
                # creates files that aren't necessarily correct CSV files
                # (See issue #280 at https://github.com/pypa/wheel)
                #
                # This code works for all filenames, except those containing
                # line seperators.
                relpath = ln.rsplit(",", 2)[0]

                if relpath.startswith('"') and relpath.endswith('"'):
                    # The record file is a CSV file that can contain quoted strings.
                    relpath = relpath[1:-1].replace('""', '"')

                infos[
                    os.path.realpath(
                        os.path.join(os.path.dirname(dist_info_path), relpath)
                    )
                ] = dist_info_path


def scan_for_metadata(path):
    """
    Scan the importlib search path *path* for dist-info/egg-info
    directories and return a mapping from absolute paths of installed
    files to their egg-info location
    """
    infos = {}
    for dirname in path:
        if not os.path.isdir(dirname):
            continue
        for nm in os.listdir(dirname):
            if nm.endswith(".egg-info") or nm.endswith(".dist-info"):
                update_metadata_cache(infos, os.path.join(dirname, nm))

    return infos
