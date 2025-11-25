from distutils.errors import DistutilsOptionError
import os

try:
    basestring
except NameError:
    basestring = str


def finalize_distribution_options(dist):
    """
    setuptools.finalize_distribution_options extension
    point for py2app, to deail with autodiscovery in
    setuptools 61.

    This addin will set the name and py_modules attributes
    when a py2app distribution is detected that does not
    yet have these attributes.
    are not already set
    """
    if getattr(dist, "app", None) is None and getattr(dist, "plugin", None) is None:
        return

    if getattr(dist.metadata, "py_modules", None) is None:
        dist.py_modules = []

    name = getattr(dist.metadata, "name", None)
    if name is None or name == "UNKNOWN":
        if dist.app:
            targets = FixupTargets(dist.app, "script")
        else:
            targets = FixupTargets(dist.plugin, "script")

        if not targets:
            return

        base = targets[0].get_dest_base()
        name = os.path.basename(base)

        dist.metadata.name = name


def validate_target(dist, attr, value):
    res = FixupTargets(value, "script")
    other = {"app": "plugin", "plugin": "app"}
    if res and getattr(dist, other[attr]):
        raise DistutilsOptionError("You must specify either app or plugin, not both")


def FixupTargets(targets, default_attribute):
    if not targets:
        return targets
    try:
        targets = eval(targets)
    except:  # noqa: E722,B001
        pass
    ret = []
    for target_def in targets:
        if isinstance(target_def, basestring):
            # Create a default target object, with the string as the attribute
            target = Target(**{default_attribute: target_def})
        else:
            d = getattr(target_def, "__dict__", target_def)

            if default_attribute not in d:
                raise DistutilsOptionError(
                    "This target class requires an attribute '%s'"
                    % (default_attribute,)
                )
            target = Target(**d)
        target.validate()
        ret.append(target)
    return ret


# A very loosely defined "target".  We assume either a "script" or "modules"
# attribute.  Some attributes will be target specific.
class Target(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # If modules is a simple string, assume they meant list
        m = self.__dict__.get("modules")
        if m and isinstance(m, basestring):
            self.modules = [m]

    def __repr__(self):
        return "<Target %s>" % (self.__dict__,)

    def get_dest_base(self):
        dest_base = getattr(self, "dest_base", None)
        if dest_base:
            return dest_base

        script = getattr(self, "script", None)
        if script:
            return os.path.basename(os.path.splitext(script)[0])
        modules = getattr(self, "modules", None)
        assert modules, "no script, modules or dest_base specified"
        return modules[0].split(".")[-1]

    def validate(self):
        resources = getattr(self, "resources", [])
        for r_filename in resources:
            if not os.path.isfile(r_filename):
                raise DistutilsOptionError(
                    "Resource filename '%s' does not exist" % (r_filename,)
                )
