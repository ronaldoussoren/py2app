"""
Automatic compilation of CoreData model files
"""
import os

from py2app.util import mapc, momc


def convert_datamodel(source, destination, dry_run=0):
    """
    Convert an .xcdatamodel to a .mom
    """
    destination = os.path.splitext(destination)[0] + ".mom"

    if dry_run:
        return

    momc(source, destination)


def convert_mappingmodel(source, destination, dry_run=0):
    """
    Convert an .xcmappingmodel to a .cdm
    """
    destination = destination[:-4] + ".cdm"

    if dry_run:
        return

    mapc(source, destination)
