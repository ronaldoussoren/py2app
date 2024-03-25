"""
Automatic compilation of CoreData model files
"""

import os
import typing

from py2app.util import mapc, momc


def convert_datamodel(
    source: typing.Union[os.PathLike[str], str],
    destination: typing.Union[os.PathLike[str], str],
    dry_run: bool = False,
) -> None:
    """
    Convert an .xcdatamodel to a .mom
    """
    destination = os.path.splitext(destination)[0] + ".mom"

    if dry_run:
        return

    momc(source, destination)


def convert_mappingmodel(
    source: typing.Union[os.PathLike[str], str],
    destination: typing.Union[os.PathLike[str], str],
    dry_run: bool = False,
) -> None:
    """
    Convert an .xcmappingmodel to a .cdm
    """
    destination = os.path.splitext(destination)[0] + ".cdm"

    if dry_run:
        return

    mapc(source, destination)
