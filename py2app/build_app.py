"""
Mac OS X .app build command for distutils

Originally (loosely) based on code from py2exe's build_exe.py by Thomas Heller.
"""
from __future__ import print_function

import imp
import sys
import os
import zipfile
import plistlib
import shlex
import shutil
import textwrap
import pkg_resources

from py2app.apptemplate.setup import main as script_executable
from py2app.util import mergecopy, make_exec


try:
    import sysconfig
except ImportError:
    sysconfig = None

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from itertools import chain


from setuptools import Command
from distutils.util import convert_path
from distutils import log
from distutils.errors import *


from modulegraph.find_modules import find_modules, parse_mf_results, find_needed_modules
from modulegraph.modulegraph import SourceModule, Package, Script
from modulegraph import zipio

import macholib.dyld
import macholib.MachOStandalone

from py2app.create_appbundle import create_appbundle
from py2app.create_pluginbundle import create_pluginbundle
from py2app.util import \
    fancy_split, byte_compile, make_loader, imp_find_module, \
    copy_tree, fsencoding, strip_files, in_system_path, makedirs, \
    iter_platform_files, find_version, skipscm, momc, copy_file, \
    copy_resource
from py2app.filters import \
    not_stdlib_filter, not_system_filter, has_filename_filter
from py2app import recipes

from distutils.sysconfig import get_config_var
PYTHONFRAMEWORK=get_config_var('PYTHONFRAMEWORK')

try:
    basestring
except NameError:
    basestring = str


def get_zipfile(dist, semi_standalone=False):
    if sys.version_info[0] == 3:
        if semi_standalone:
            return "python%d.%d/site-packages.zip"%(sys.version_info[:2])
        else:
            return "python%d%d.zip"%(sys.version_info[:2])
    return getattr(dist, "zipfile", None) or "site-packages.zip"

def framework_copy_condition(src):
    # Skip Headers, .svn, and CVS dirs
    return skipscm(src) and os.path.basename(src) != 'Headers'

class PythonStandalone(macholib.MachOStandalone.MachOStandalone):
    def __init__(self, appbuilder, *args, **kwargs):
        super(PythonStandalone, self).__init__(*args, **kwargs)
        self.appbuilder = appbuilder

    def copy_dylib(self, src):
        dest = os.path.join(self.dest, os.path.basename(src))
        if os.path.islink(src):
            dest = os.path.join(self.dest, os.path.basename(os.path.realpath(src)))

            # Ensure that the orginal name also exists, avoids problems when
            # the filename is used from Python (see issue #65)
            # 
            # NOTE: The if statement checks that the target link won't 
            #       point to itself, needed for systems like homebrew that
            #       store symlinks in "public" locations that point to
            #       files of the same name in a per-package install location.
            link_dest = os.path.join(self.dest, os.path.basename(src))
            if os.path.basename(link_dest) != os.path.basename(dest):
                os.symlink(os.path.basename(dest), link_dest)

        else:
            dest = os.path.join(self.dest, os.path.basename(src))
        return self.appbuilder.copy_dylib(src, dest)

    def copy_framework(self, info):
        destfn = self.appbuilder.copy_framework(info, self.dest)
        dest = os.path.join(self.dest, info['shortname'] + '.framework')
        self.pending.append((destfn, iter_platform_files(dest)))
        return destfn

def iterRecipes(module=recipes):
    for name in dir(module):
        if name.startswith('_'):
            continue
        check = getattr(getattr(module, name), 'check', None)
        if check is not None:
            yield (name, check)

# A very loosely defined "target".  We assume either a "script" or "modules"
# attribute.  Some attributes will be target specific.
class Target(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # If modules is a simple string, assume they meant list
        m = self.__dict__.get("modules")
        if m and isinstance(m, basestring):
            self.modules = [m]

    def get_dest_base(self):
        dest_base = getattr(self, "dest_base", None)
        if dest_base: return dest_base
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
                    "Resource filename '%s' does not exist" % (r_filename,))


def validate_target(dist, attr, value):
    res = FixupTargets(value, "script")
    other = {"app": "plugin", "plugin": "app"}
    if res and getattr(dist, other[attr]):
        # XXX - support apps and plugins?
        raise DistutilsOptionError(
            "You must specify either app or plugin, not both")

def FixupTargets(targets, default_attribute):
    if not targets:
        return targets
    try:
        targets = eval(targets)
    except:
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
                    % (default_attribute,))
            target = Target(**d)
        target.validate()
        ret.append(target)
    return ret

def normalize_data_file(fn):
    if isinstance(fn, basestring):
        fn = convert_path(fn)
        return ('', [fn])
    return fn

def is_system(executable=None):
    if executable is None:
        executable = sys.executable
    return in_system_path(executable)

def installation_info(executable=None, version=None):
    if version is None:
        version = sys.version
    if is_system(executable):
        return version[:3] + " (FORCED: Using vendor Python)"
    else:
        return version[:3]

class py2app(Command):
    description = "create a Mac OS X application or plugin from Python scripts"
    # List of option tuples: long name, short name (None if no short
    # name), and help string.

    user_options = [
        ("app=", None,
         "application bundle to be built"),
        ("plugin=", None,
         "puglin bundle to be built"),
        ('optimize=', 'O',
         "optimization level: -O1 for \"python -O\", "
         "-O2 for \"python -OO\", and -O0 to disable [default: -O0]"),
        ("includes=", 'i',
         "comma-separated list of modules to include"),
        ("packages=", 'p',
         "comma-separated list of packages to include"),
        ("iconfile=", None,
         "Icon file to use"),
        ("excludes=", 'e',
         "comma-separated list of modules to exclude"),
        ("dylib-excludes=", 'E',
         "comma-separated list of frameworks or dylibs to exclude"),
        ("datamodels=", None,
         "xcdatamodels to be compiled and copied into Resources"),
        ("mappingmodels=", None,
          "xcmappingmodels to be compiled and copied into Resources"),
        ("resources=", 'r',
         "comma-separated list of additional data files and folders to include (not for code!)"),
        ("frameworks=", 'f',
         "comma-separated list of additional frameworks and dylibs to include"),
        ("plist=", 'P',
         "Info.plist template file, dict, or plistlib.Plist"),
        ("extension=", None,
         "Bundle extension [default:.app for app, .plugin for plugin]"),
        ("graph", 'g',
         "output module dependency graph"),
        ("xref", 'x',
         "output module cross-reference as html"),
        ("no-strip", None,
         "do not strip debug and local symbols from output"),
        #("compressed", 'c',
        # "create a compressed zipfile"),
        ("no-chdir", 'C',
         "do not change to the data directory (Contents/Resources) [forced for plugins]"),
        #("no-zip", 'Z',
        # "do not use a zip file (XXX)"),
        ("semi-standalone", 's',
         "depend on an existing installation of Python " + installation_info()),
        ("alias", 'A',
         "Use an alias to current source file (for development only!)"),
        ("argv-emulation", 'a',
         "Use argv emulation [disabled for plugins]. Does not work with python 3.x"),
        ("argv-inject=", None,
         "Inject some commands into the argv"),
        ("emulate-shell-environment", None,
         "Emulate the shell environment you get in a Terminal window"),
        ("use-pythonpath", None,
         "Allow PYTHONPATH to effect the interpreter's environment"),
        ('bdist-base=', 'b',
         'base directory for build library (default is build)'),
        ('dist-dir=', 'd',
         "directory to put final built distributions in (default is dist)"),
        ('site-packages', None,
         "include the system and user site-packages into sys.path"),
        ("strip", 'S',
         "strip debug and local symbols from output (on by default, for compatibility)"),
        ("prefer-ppc", None,
         "Force application to run translated on i386 (LSPrefersPPC=True)"),
        ('debug-modulegraph', None,
         'Drop to pdb console after the module finding phase is complete'),
        ("debug-skip-macholib", None,
         "skip macholib phase (app will not be standalone!)"),
        ("arch=", None, "set of architectures to use (fat, fat3, universal, intel, i386, ppc, x86_64; default is the set for the current python binary)"),
        ("qt-plugins=", None, "set of Qt plugins to include in the application bundle (default None)"),
        ("matplotlib-backends=", None, "set of matplotlib backends to include (default: include entire package)"),
        ("extra-scripts=", None, "set of scripts to include in the application bundle, next to the main application script"),
        ]

    boolean_options = [
        #"compressed",
        "xref",
        "strip",
        "no-strip",
        "site-packages",
        "semi-standalone",
        "alias",
        "argv-emulation",
        #"no-zip",
        "use-pythonpath",
        "no-chdir",
        "debug-modulegraph",
        "debug-skip-macholib",
        "graph",
        "prefer-ppc",
        "emulate-shell-environment",
    ]

    def initialize_options (self):
        self.app = None
        self.plugin = None
        self.bdist_base = None
        self.xref = False
        self.graph = False
        self.no_zip = 0
        self.optimize = 0
        if hasattr(sys, 'flags'):
            self.optimize = sys.flags.optimize
        self.arch = None
        self.strip = True
        self.no_strip = False
        self.iconfile = None
        self.extension = None
        self.alias = 0
        self.argv_emulation = 0
        self.emulate_shell_environment = 0
        self.argv_inject = None
        self.no_chdir = 0
        self.site_packages = False
        self.use_pythonpath = False
        self.includes = None
        self.packages = None
        self.excludes = None
        self.dylib_excludes = None
        self.frameworks = None
        self.resources = None
        self.datamodels = None
        self.mappingmodels = None
        self.plist = None
        self.compressed = True
        self.semi_standalone = is_system()
        self.dist_dir = None
        self.debug_skip_macholib = False
        self.debug_modulegraph = False
        self.prefer_ppc = False
        self.filters = []
        self.eggs = []
        self.qt_plugins = None
        self.matplotlib_backends = None
        self.extra_scripts = None

    def finalize_options (self):
        if not self.strip:
            self.no_strip = True
        elif self.no_strip:
            self.strip = False
        self.optimize = int(self.optimize)
        if self.argv_inject and isinstance(self.argv_inject, basestring):
            self.argv_inject = shlex.split(self.argv_inject)
        self.includes = set(fancy_split(self.includes))
        self.includes.add('encodings.*')
        #if sys.version_info[:2] >= (3, 2):
        #    self.includes.add('pkgutil')
        #    self.includes.add('imp')
        self.packages = set(fancy_split(self.packages))
        for pkg in self.packages:
            if "." in pkg:
                raise DistutilsOptionError("Cannot include subpackages using the 'packages' option")

        self.excludes = set(fancy_split(self.excludes))
        self.excludes.add('readline')
        # included by apptemplate
        self.excludes.add('site')
        if getattr(self.distribution, 'install_requires', None):
            self.includes.add('pkg_resources')
            self.eggs = pkg_resources.require(self.distribution.install_requires)

        # Setuptools/distribute style namespace packages uses
        # __import__('pkg_resources'), and that import isn't detected at the
        # moment. Forcefully include pkg_resources.
        self.includes.add('pkg_resources')

        dylib_excludes = fancy_split(self.dylib_excludes)
        self.dylib_excludes = []
        for fn in dylib_excludes:
            try:
                res = macholib.dyld.framework_find(fn)
            except ValueError:
                try:
                    res = macholib.dyld.dyld_find(fn)
                except ValueError:
                    res = fn
            self.dylib_excludes.append(res)
        self.resources = fancy_split(self.resources)
        frameworks = fancy_split(self.frameworks)
        self.frameworks = []
        for fn in frameworks:
            try:
                res = macholib.dyld.framework_find(fn)
            except ValueError:
                res = macholib.dyld.dyld_find(fn)
            while res in self.dylib_excludes:
                self.dylib_excludes.remove(res)
            self.frameworks.append(res)
        if not self.plist:
            self.plist = {}
        if isinstance(self.plist, basestring):
            self.plist = plistlib.Plist.fromFile(self.plist)
        if isinstance(self.plist, plistlib.Dict):
            self.plist = dict(self.plist.__dict__)
        else:
            self.plist = dict(self.plist)

        self.set_undefined_options('bdist',
                                   ('dist_dir', 'dist_dir'),
                                   ('bdist_base', 'bdist_base'))

        if self.semi_standalone:
            self.filters.append(not_stdlib_filter)

        if self.iconfile is None and 'CFBundleIconFile' not in self.plist:
            # Default is the generic applet icon in the framework
            iconfile = os.path.join(sys.prefix, 'Resources', 'Python.app',
                'Contents', 'Resources', 'PythonApplet.icns')
            if os.path.exists(iconfile):
                self.iconfile = iconfile


        self.runtime_preferences = list(self.get_runtime_preferences())

        self.qt_plugins = fancy_split(self.qt_plugins)
        self.matplotlib_backends = fancy_split(self.matplotlib_backends)
        self.extra_scripts = fancy_split(self.extra_scripts)


        if self.datamodels:
            print("WARNING: the datamodels option is deprecated, add model files to the list of resources")

        if self.mappingmodels:
            print("WARNING: the mappingmodels option is deprecated, add model files to the list of resources")


    def get_default_plist(self):
        # XXX - this is all single target stuff
        plist = {}
        target = self.targets[0]

        version = self.distribution.get_version()
        if version == '0.0.0':
            try:
                version = find_version(target.script)
            except ValueError:
                pass

        if not isinstance(version, basestring):
            raise DistutilsOptionError("Version must be a string")

        if sys.version_info[0] > 2 and isinstance(version, type('a'.encode('ascii'))):
            raise DistutilsOptionError("Version must be a string")

        plist['CFBundleVersion'] = version

        name = self.distribution.get_name()
        if name == 'UNKNOWN':
            base = target.get_dest_base()
            name = os.path.basename(base)
        plist['CFBundleName'] = name

        return plist

    def get_runtime(self, prefix=None, version=None):
        # XXX - this is a bit of a hack!
        #       ideally we'd use dylib functions to figure this out
        if prefix is None:
            prefix = sys.prefix
        if version is None:
            version = sys.version
        version = version[:3]
        info = None
        if os.path.exists(os.path.join(prefix, ".Python")):
            # We're in a virtualenv environment, locate the real prefix
            fn = os.path.join(prefix, "lib", "python%d.%d"%(sys.version_info[:2]), "orig-prefix.txt")
            if os.path.exists(fn):
                with open(fn, 'rU') as fp:
                    prefix = fp.read().strip()

        try:
            fmwk = macholib.dyld.framework_find(prefix)
        except ValueError:
            info = None
        else:
            info = macholib.dyld.framework_info(fmwk)

        if info is not None:
            dylib = info['name']
            runtime = os.path.join(info['location'], info['name'])
        else:
            dylib = 'libpython%s.dylib' % (sys.version[:3],)
            runtime = os.path.join(prefix, 'lib', dylib)
        return dylib, runtime

    def symlink(self, src, dst):
        try:
            os.remove(dst)
        except OSError:
            pass
        os.symlink(src, dst)

    def get_runtime_preferences(self, prefix=None, version=None):
        dylib, runtime = self.get_runtime(prefix=prefix, version=version)
        yield os.path.join('@executable_path', '..', 'Frameworks', dylib)
        if self.semi_standalone or self.alias:
            yield runtime

    def run(self):
        if sysconfig.get_config_var('PYTHONFRAMEWORK') is None:
            if not sysconfig.get_config_var('Py_ENABLE_SHARED'):
                raise DistutilsPlatformError("This python does not have a shared library or framework")

            else:
                # Issue .. in py2app's tracker, and issue .. in python's tracker: a unix-style shared 
                # library build did not read the application environment correctly. The collection of
                # if statements below gives a clean error message when py2app is started, instead of
                # building a bundle that will give a confusing error message when started.
                msg = "py2app is not supported for a shared library build with this version of python"
                if sys.version_info[:2] < (2,7):
                    raise DistutilsPlatformError(msg)
                elif sys.version_info[:2] == (2,7) and sys.version[3] < 4:
                    raise DistutilsPlatformError(msg)
                elif sys.version_info[0] == 3 and sys.version_info[1] < 2:
                    raise DistutilsPlatformError(msg)
                elif sys.version_info[0] == 3 and sys.version_info[1] == 2 and sys.version_info[3] < 3:
                    raise DistutilsPlatformError(msg)
                elif sys.version_info[0] == 3 and sys.version_info[1] == 3 and sys.version_info[3] < 1:
                    raise DistutilsPlatformError(msg)

        if hasattr(self.distribution, "install_requires") \
                and self.distribution.install_requires:

            self.distribution.fetch_build_eggs(self.distribution.install_requires)


        build = self.reinitialize_command('build')
        build.build_base = self.bdist_base
        build.run()
        self.create_directories()
        self.fixup_distribution()
        self.initialize_plist()

        sys_old_path = sys.path[:]
        extra_paths = [
            os.path.dirname(target.script)
            for target in self.targets
        ]
        extra_paths.extend([build.build_platlib, build.build_lib])
        self.additional_paths = [
            os.path.abspath(p)
            for p in extra_paths
            if p is not None
        ]
        sys.path[:0] = self.additional_paths

        # this needs additional_paths
        self.initialize_prescripts()

        try:
            self._run()
        finally:
            sys.path = sys_old_path


    def iter_datamodels(self, resdir):
        for (path, files) in (normalize_data_file(fn) for fn in (self.datamodels or ())):
            path = fsencoding(path)
            for fn in files:
                fn = fsencoding(fn)
                basefn, ext = os.path.splitext(fn)
                if ext != '.xcdatamodel':
                    basefn = fn
                    fn += '.xcdatamodel'
                destfn = os.path.basename(basefn) + '.mom'
                yield fn, os.path.join(resdir, path, destfn)

    def compile_datamodels(self, resdir):
        for src, dest in self.iter_datamodels(resdir):
            print("compile datamodel", src, "->", dest)
            self.mkpath(os.path.dirname(dest))
            momc(src, dest)

    def iter_mappingmodels(self, resdir):
        for (path, files) in (normalize_data_file(fn) for fn in (self.mappingmodels or ())):
            path = fsencoding(path)
            for fn in files:
                fn = fsencoding(fn)
                basefn, ext = os.path.splitext(fn)
                if ext != '.xcmappingmodel':
                    basefn = fn
                    fn += '.xcmappingmodel'
                destfn = os.path.basename(basefn) + '.cdm'
                yield fn, os.path.join(resdir, path, destfn)

    def compile_mappingmodels(self, resdir):
        for src, dest in self.iter_mappingmodels(resdir):
            self.mkpath(os.path.dirname(dest))
            mapc(src, dest)
        
    def iter_data_files(self):
        dist = self.distribution
        allres = chain(getattr(dist, 'data_files', ()) or (), self.resources)
        for (path, files) in (normalize_data_file(fn) for fn in allres):
            path = fsencoding(path)
            for fn in files:
                fn = fsencoding(fn)
                yield fn, os.path.join(path, os.path.basename(fn))

    def collect_scripts(self):
        # these contains file names
        scripts = set()

        for target in self.targets:
            scripts.add(target.script)
            scripts.update([
                k for k in target.prescripts if isinstance(k, basestring)
            ])
            if hasattr(target, 'extra_scripts'):
                scripts.update(target.extra_scripts)

        scripts.update(self.extra_scripts)
        return scripts

    def get_plist_options(self):
        result = dict(
            PyOptions=dict(
                use_pythonpath=bool(self.use_pythonpath),
                site_packages=bool(self.site_packages),
                alias=bool(self.alias),
                argv_emulation=bool(self.argv_emulation),
                emulate_shell_environment=bool(self.emulate_shell_environment),
                no_chdir=bool(self.no_chdir),
                prefer_ppc=self.prefer_ppc,
            ),
        )
        if self.optimize:
            result['PyOptions']['optimize'] = self.optimize
        return result

    
    def initialize_plist(self):
        plist = self.get_default_plist()
        for target in self.targets:
            plist.update(getattr(target, 'plist', {}))
        plist.update(self.plist)
        plist.update(self.get_plist_options())

        if self.iconfile:
            iconfile = self.iconfile
            if not os.path.exists(iconfile):
                iconfile = iconfile + '.icns'
            if not os.path.exists(iconfile):
                raise DistutilsOptionError("icon file must exist: %r"
                    % (self.iconfile,))
            self.resources.append(iconfile)
            plist['CFBundleIconFile'] = os.path.basename(iconfile)
        if self.prefer_ppc:
            plist['LSPrefersPPC'] = True

        self.plist = plist
        return plist

    def run_alias(self):
        self.app_files = []
        for target in self.targets:

            extra_scripts = list(self.extra_scripts)
            if hasattr(target, 'extra_scripts'):
                extra_scripts.update(extra_scripts)

            dst = self.build_alias_executable(target, target.script, extra_scripts)
            self.app_files.append(dst)

            for fn in extra_scripts:
                if fn.endswith('.py'):
                    fn = fn[:-3]
                elif fn.endswith('.pyw'):
                    fn = fn[:-4]

                src_fn = script_executable(arch=self.arch)
                tgt_fn = os.path.join(target.appdir, 'Contents', 'MacOS', os.path.basename(fn))
                mergecopy(src_fn, tgt_fn)
                make_exec(tgt_fn)

    def collect_recipedict(self):
        return dict(iterRecipes())

    def get_modulefinder(self):
        if self.debug_modulegraph:
            debug = 4
        else:
            debug = 0
        return find_modules(
            scripts=self.collect_scripts(),
            includes=self.includes,
            packages=self.packages,
            excludes=self.excludes,
            debug=debug,
        )

    def collect_filters(self):
        return [has_filename_filter] + list(self.filters)

    def process_recipes(self, mf, filters, flatpackages, loader_files):
        rdict = self.collect_recipedict()
        while True:
            for name, check in rdict.items():
                rval = check(self, mf)
                if rval is None:
                    continue
                # we can pull this off so long as we stop the iter
                del rdict[name]
                print('*** using recipe: %s ***' % (name,))

                if rval.get('packages'):
                    self.packages.update(rval['packages'])
                    find_needed_modules(mf, packages=rval['packages'])

                for pkg in rval.get('flatpackages', ()):
                    if isinstance(pkg, basestring):
                        pkg = (os.path.basename(pkg), pkg)
                    flatpackages[pkg[0]] = pkg[1]
                filters.extend(rval.get('filters', ()))
                loader_files.extend(rval.get('loader_files', ()))
                newbootstraps = map(self.get_bootstrap,
                    rval.get('prescripts', ()))

                if rval.get('includes'):
                    find_needed_modules(mf, includes=rval['includes'])

                if rval.get('resources'):
                    self.resources.extend(rval['resources'])

                for fn in newbootstraps:
                    if isinstance(fn, basestring):
                        mf.run_script(fn)
                for target in self.targets:
                    target.prescripts.extend(newbootstraps)
                break
            else:
                break

    def _run(self):
        try:
            if self.alias:
                self.run_alias()
            else:
                self.run_normal()
        except:
            raise
            # XXX - remove when not debugging
            #       distutils sucks
            import pdb, sys, traceback
            traceback.print_exc()
            pdb.post_mortem(sys.exc_info()[2])

    def filter_dependencies(self, mf, filters):
        print("*** filtering dependencies ***")
        nodes_seen, nodes_removed, nodes_orphaned = mf.filterStack(filters)
        print('%d total' % (nodes_seen,))
        print('%d filtered' % (nodes_removed,))
        print('%d orphaned' % (nodes_orphaned,))
        print('%d remaining' % (nodes_seen - nodes_removed,))

    def get_appname(self):
        return self.plist['CFBundleName']

    def build_xref(self, mf, flatpackages):
        for target in self.targets:
            base = target.get_dest_base()
            appdir = os.path.join(self.dist_dir, os.path.dirname(base))
            appname = self.get_appname()
            dgraph = os.path.join(appdir, appname + '.html')
            print("*** creating dependency html: %s ***"
                % (os.path.basename(dgraph),))
            with open(dgraph, 'w') as fp:
                mf.create_xref(fp)

    def build_graph(self, mf, flatpackages):
        for target in self.targets:
            base = target.get_dest_base()
            appdir = os.path.join(self.dist_dir, os.path.dirname(base))
            appname = self.get_appname()
            dgraph = os.path.join(appdir, appname + '.dot')
            print("*** creating dependency graph: %s ***"
                % (os.path.basename(dgraph),))
            with open(dgraph, 'w') as fp:
                mf.graphreport(fp, flatpackages=flatpackages)

    def finalize_modulefinder(self, mf):
        for item in mf.flatten():
            if isinstance(item, Package) and item.filename == '-':
                fn = os.path.join(self.temp_dir, 'empty_package', '__init__.py')
                if not os.path.exists(fn):
                    dn = os.path.dirname(fn)
                    if not os.path.exists(dn):
                        os.makedirs(dn)
                    with open(fn, 'w') as fp:
                        pass

                item.filename = fn

        py_files, extensions = parse_mf_results(mf)

        # Remove all top-level scripts from the list of python files,
        # those get treated differently.
        py_files = [ item for item in py_files if not isinstance(item, Script) ]

        extensions = list(extensions)
        return py_files, extensions

    def collect_packagedirs(self):
        return list(filter(os.path.exists, [
            os.path.join(os.path.realpath(self.get_bootstrap(pkg)), '')
            for pkg in self.packages
        ]))

    def run_normal(self):
        mf = self.get_modulefinder()
        filters = self.collect_filters()
        flatpackages = {}
        loader_files = []
        self.process_recipes(mf, filters, flatpackages, loader_files)

        if self.debug_modulegraph:
            import pdb
            pdb.Pdb().set_trace()

        self.filter_dependencies(mf, filters)

        if self.graph:
            self.build_graph(mf, flatpackages)
        if self.xref:
            self.build_xref(mf, flatpackages)

        py_files, extensions = self.finalize_modulefinder(mf)
        pkgdirs = self.collect_packagedirs()
        self.create_binaries(py_files, pkgdirs, extensions, loader_files)

    def create_directories(self):
        bdist_base = self.bdist_base
        if self.semi_standalone:
            self.bdist_dir = os.path.join(bdist_base,
                'python%s-semi_standalone' % (sys.version[:3],), 'app')
        else:
            self.bdist_dir = os.path.join(bdist_base,
                'python%s-standalone' % (sys.version[:3],), 'app')

        if os.path.exists(self.bdist_dir):
            shutil.rmtree(self.bdist_dir)
        
        self.collect_dir = os.path.abspath(
            os.path.join(self.bdist_dir, "collect"))
        self.mkpath(self.collect_dir)

        self.temp_dir = os.path.abspath(os.path.join(self.bdist_dir, "temp"))
        self.mkpath(self.temp_dir)

        self.dist_dir = os.path.abspath(self.dist_dir)
        self.mkpath(self.dist_dir)

        self.lib_dir = os.path.join(self.bdist_dir,
            os.path.dirname(get_zipfile(self.distribution, self.semi_standalone)))
        self.mkpath(self.lib_dir)

        self.ext_dir = os.path.join(self.lib_dir, 'lib-dynload')
        self.mkpath(self.ext_dir)

        self.framework_dir = os.path.join(self.bdist_dir, 'Frameworks')
        self.mkpath(self.framework_dir)

    def create_binaries(self, py_files, pkgdirs, extensions, loader_files):
        print("*** create binaries ***")
        dist = self.distribution
        pkgexts = []
        copyexts = []
        extmap = {}
        def packagefilter(mod, pkgdirs=pkgdirs):
            fn = os.path.realpath(getattr(mod, 'filename', None))
            if fn is None:
                return None
            for pkgdir in pkgdirs:
                if fn.startswith(pkgdir):
                    return None
            return fn
        if pkgdirs:
            py_files = list(filter(packagefilter, py_files))
        for ext in extensions:
            fn = packagefilter(ext)
            if fn is None:
                fn = os.path.realpath(getattr(ext, 'filename', None))
                pkgexts.append(ext)
            else:
                if '.' in ext.identifier:
                    py_files.append(self.create_loader(ext))
                copyexts.append(ext)
            extmap[fn] = ext

        # byte compile the python modules into the target directory
        print("*** byte compile python files ***")
        byte_compile(py_files,
                     target_dir=self.collect_dir,
                     optimize=self.optimize,
                     force=self.force,
                     verbose=self.verbose,
                     dry_run=self.dry_run)

        for item in py_files:
            if not isinstance(item, Package): continue
            self.copy_package_data(item, self.collect_dir)

        self.lib_files = []
        self.app_files = []

        # create the shared zipfile containing all Python modules
        archive_name = os.path.join(self.lib_dir,
                                    get_zipfile(dist, self.semi_standalone))

        for path, files in loader_files:
            dest = os.path.join(self.collect_dir, path)
            self.mkpath(dest)
            for fn in files:
                destfn = os.path.join(dest, os.path.basename(fn))
                if os.path.isdir(fn):
                    self.copy_tree(fn, destfn, preserve_symlinks=False)
                else:
                    self.copy_file(fn, destfn)

        arcname = self.make_lib_archive(archive_name,
            base_dir=self.collect_dir, verbose=self.verbose,
            dry_run=self.dry_run)

        # XXX: this doesn't work with python3
        #self.lib_files.append(arcname)

        # build the executables
        for target in self.targets:
            extra_scripts = list(self.extra_scripts)
            if hasattr(target, 'extra_scripts'):
                extra_scripts.extend(target.extra_scripts)
            dst = self.build_executable(
                target, arcname, pkgexts, copyexts, target.script, extra_scripts)
            exp = os.path.join(dst, 'Contents', 'MacOS')
            execdst = os.path.join(exp, 'python')
            if self.semi_standalone:
                self.symlink(sys.executable, execdst)
            else:
                if os.path.exists(os.path.join(sys.prefix, ".Python")):
                    fn = os.path.join(sys.prefix, "lib", "python%d.%d"%(sys.version_info[:2]), "orig-prefix.txt")
                    if os.path.exists(fn):
                        with open(fn, 'rU') as fp:
                            prefix = fp.read().strip()

                    rest_path = os.path.normpath(sys.executable)[len(os.path.normpath(sys.prefix))+1:]
                    if rest_path.startswith('.'):
                        rest_path = rest_path[1:]

                    if PYTHONFRAMEWORK:
                        # When we're using a python framework bin/python refers to a stub executable
                        # that we don't want use, we need the executable in Resources/Python.app
                        dpath = os.path.join(prefix, 'Resources', 'Python.app', 'Contents', 'MacOS')
                        self.copy_file(os.path.join(dpath, PYTHONFRAMEWORK), execdst)


                    else:
                        self.copy_file(os.path.join(prefix, rest_path), execdst)

                else:
                    self.copy_file(sys.executable, execdst)
            if not self.debug_skip_macholib:
                mm = PythonStandalone(self, dst, executable_path=exp)
                dylib, runtime = self.get_runtime()
                if self.semi_standalone:
                    mm.excludes.append(runtime)
                else:
                    mm.mm.run_file(runtime)
                for exclude in self.dylib_excludes:
                    info = macholib.dyld.framework_info(exclude)
                    if info is not None:
                        exclude = os.path.join(
                            info['location'], info['shortname'] + '.framework')
                    mm.excludes.append(exclude)
                for fmwk in self.frameworks:
                    mm.mm.run_file(fmwk)
                platfiles = mm.run()
                if self.strip:
                    platfiles = self.strip_dsym(platfiles)
                    self.strip_files(platfiles)
            self.app_files.append(dst)

    def copy_package_data(self, package, target_dir):
        """
        Copy any package data in a python package into the target_dir.

        This is a bit of a hack, it would be better to identify python eggs
        and copy those in whole.
        """
        exts = [ i[0] for i in imp.get_suffixes() ]
        exts.append('.py')
        exts.append('.pyc')
        exts.append('.pyo')
        def datafilter(item):
            for e in exts:
                if item.endswith(e):
                    return False
            return True

        target_dir = os.path.join(target_dir, *(package.identifier.split('.')))
        for dname in package.packagepath:
            filenames = list(filter(datafilter, zipio.listdir(dname)))
            for fname in filenames:
                if fname in ('.svn', 'CVS', '.hg', '.git'):
                    # Scrub revision manager junk
                    continue
                if fname in ('__pycache__',):
                    # Ignore PEP 3147 bytecode cache
                    continue
                if fname.startswith('.') and fname.endswith('.swp'):
                    # Ignore vim(1) temporary files
                    continue
                if fname.endswith('~') or fname.endswith('.orig'):
                    # Ignore backup files for common tools (hg, emacs, ...)
                    continue
                pth = os.path.join(dname, fname)

                # Check if we have found a package, exclude those
                if zipio.isdir(pth):
                    # XXX: the 'and not' part is wrong, need to fix zipio.isdir
                    for p in zipio.listdir(pth):
                        if p.startswith('__init__.') and p[8:] in exts:
                            break

                    else:
                        if os.path.isfile(pth):
                            # Avoid extracting a resource file that happens
                            # to be zipfile.
                            # XXX: Need API in zipio for nicer code.
                            copy_file(pth, os.path.join(target_dir, fname))
                        else:
                            copy_tree(pth, os.path.join(target_dir, fname))
                    continue

                elif zipio.isdir(pth) and (
                        zipio.isfile(os.path.join(pth, '__init__.py'))
                     or zipio.isfile(os.path.join(pth, '__init__.pyc'))
                     or zipio.isfile(os.path.join(pth, '__init__.pyo'))):
                    # Subdirectory is a python package, these will get included later on
                    # when the subpackage itself is included, ignore for now.
                    pass

                else:
                    copy_file(pth, os.path.join(target_dir, fname))


    def strip_dsym(self, platfiles):
        """ Remove .dSYM directories in the bundled application """

        #
        # .dSYM directories are contain detached debugging information and
        # should be completely removed when the "strip" option is specified.
        #
        if self.dry_run:
            return platfiles
        for dirpath, dnames, fnames in os.walk(self.appdir):
            for nm in list(dnames):
                if nm.endswith('.dSYM'):
                    print("removing debug info: %s/%s"%(dirpath, nm))
                    shutil.rmtree(os.path.join(dirpath, nm))
                    dnames.remove(nm)
        return [file for file in platfiles if '.dSYM' not in file]

    def strip_files(self, files):
        unstripped = 0
        stripfiles = []
        for fn in files:
            unstripped += os.stat(fn).st_size
            stripfiles.append(fn)
            log.info('stripping %s', os.path.basename(fn))
        strip_files(stripfiles, dry_run=self.dry_run, verbose=self.verbose)
        stripped = 0
        for fn in stripfiles:
            stripped += os.stat(fn).st_size
        log.info('stripping saved %d bytes (%d / %d)',
            unstripped - stripped, stripped, unstripped)

    def copy_dylib(self, src, dst):
        # will be copied from the framework?
        if src != sys.executable:
            force, self.force = self.force, True
            self.copy_file(src, dst)
            self.force = force
        return dst

    def copy_versioned_framework(self, info, dst):
        # XXX - Boy is this ugly, but it makes sense because the developer
        #       could have both Python 2.3 and 2.4, or Tk 8.4 and 8.5, etc.
        #       Saves a good deal of space, and I'm pretty sure this ugly
        #       hack is correct in the general case.
        version = info['version']
        if version is None:
            return self.raw_copy_framework(info, dst)
        short = info['shortname'] + '.framework'
        infile = os.path.join(info['location'], short)
        outfile = os.path.join(dst, short)
        vsplit = os.path.join(infile, 'Versions').split(os.sep)
        def condition(src, vsplit=vsplit, version=version):
            srcsplit = src.split(os.sep)
            if (
                    len(srcsplit) > len(vsplit) and
                    srcsplit[:len(vsplit)] == vsplit and
                    srcsplit[len(vsplit)] != version and
                    not os.path.islink(src)
                ):
                return False
            # Skip Headers, .svn, and CVS dirs
            return framework_copy_condition(src)

        return self.copy_tree(infile, outfile,
            preserve_symlinks=True, condition=condition)

    def copy_framework(self, info, dst):
        force, self.force = self.force, True
        if info['shortname'] == PYTHONFRAMEWORK:
            self.copy_python_framework(info, dst)
        else:
            self.copy_versioned_framework(info, dst)
        self.force = force
        return os.path.join(dst, info['name'])

    def raw_copy_framework(self, info, dst):
        short = info['shortname'] + '.framework'
        infile = os.path.join(info['location'], short)
        outfile = os.path.join(dst, short)
        return self.copy_tree(infile, outfile,
            preserve_symlinks=True, condition=framework_copy_condition)

    def copy_python_framework(self, info, dst):
        # XXX - In this particular case we know exactly what we can
        #       get away with.. should this be extended to the general
        #       case?  Per-framework recipes?
        includedir = None
        configdir = None
        if sysconfig is not None:
            includedir = sysconfig.get_config_var('CONFINCLUDEPY')
            configdir = sysconfig.get_config_var('LIBPL')


        if includedir is None:
            includedir = 'python%d.%d'%(sys.version_info[:2])
        else:
            includedir = os.path.basename(includedir)

        if configdir is None:
            configdir = 'config'
        else:
            configdir = os.path.basename(configdir)


        indir = os.path.dirname(os.path.join(info['location'], info['name']))
        outdir = os.path.dirname(os.path.join(dst, info['name']))
        self.mkpath(os.path.join(outdir, 'Resources'))
        pydir = 'python%s.%s'%(sys.version_info[:2])

        # Create a symlink "for Python.frameworks/Versions/Current". This
        # is required for the Mac App-store.
        os.symlink(
                os.path.basename(outdir),
                os.path.join(os.path.dirname(outdir), "Current"))

        # Experiment for issue 57
        if not os.path.exists(os.path.join(indir, 'include')):
            alt = os.path.join(indir, 'Versions/Current')
            if os.path.exists(os.path.join(alt, 'include')):
                indir = alt

        # distutils looks for some files relative to sys.executable, which
        # means they have to be in the framework...
        self.mkpath(os.path.join(outdir, 'include'))
        self.mkpath(os.path.join(outdir, 'include', includedir))
        self.mkpath(os.path.join(outdir, 'lib'))
        self.mkpath(os.path.join(outdir, 'lib', pydir))
        self.mkpath(os.path.join(outdir, 'lib', pydir, configdir))


        fmwkfiles = [
            os.path.basename(info['name']),
            'Resources/Info.plist',
            'include/%s/pyconfig.h'%(includedir),
            'lib/%s/%s/Makefile'%(pydir, configdir)
        ]
        for fn in fmwkfiles:
            self.copy_file(
                os.path.join(indir, fn),
                os.path.join(outdir, fn))



    def fixup_distribution(self):
        dist = self.distribution

        # Trying to obtain app and plugin from dist for backward compatibility
        # reasons.
        app = dist.app
        plugin = dist.plugin
        # If we can get suitable values from self.app and self.plugin, we prefer
        # them.
        if self.app is not None or self.plugin is not None:
            app = self.app
            plugin = self.plugin

        # Convert our args into target objects.
        dist.app = FixupTargets(app, "script")
        dist.plugin = FixupTargets(plugin, "script")
        if dist.app and dist.plugin:
            # XXX - support apps and plugins?
            raise DistutilsOptionError(
                "You must specify either app or plugin, not both")
        elif dist.app:
            self.style = 'app'
            self.targets = dist.app
        elif dist.plugin:
            self.style = 'plugin'
            self.targets = dist.plugin
        else:
            raise DistutilsOptionError(
                "You must specify either app or plugin")
        if len(self.targets) != 1:
            # XXX - support multiple targets?
            raise DistutilsOptionError(
                "Multiple targets not currently supported")
        if not self.extension:
            self.extension = '.' + self.style

        # make sure all targets use the same directory, this is
        # also the directory where the pythonXX.dylib must reside
        paths = set()
        for target in self.targets:
            paths.add(os.path.dirname(target.get_dest_base()))

        if len(paths) > 1:
            raise DistutilsOptionError(
                  "all targets must use the same directory: %s" %
                  ([p for p in paths],))
        if paths:
            app_dir = paths.pop() # the only element
            if os.path.isabs(app_dir):
                raise DistutilsOptionError(
                      "app directory must be relative: %s" % (app_dir,))
            self.app_dir = os.path.join(self.dist_dir, app_dir)
            self.mkpath(self.app_dir)
        else:
            # Do we allow to specify no targets?
            # We can at least build a zipfile...
            self.app_dir = self.lib_dir

    def initialize_prescripts(self):
        prescripts = []
        prescripts.append('reset_sys_path')
        if self.semi_standalone:
            prescripts.append('semi_standalone_path')

        if 0 and sys.version_info[:2] >= (3, 2) and not self.alias:
            # Python 3.2 or later requires a more complicated
            # bootstrap
            prescripts.append('import_encodings')

        if os.path.exists(os.path.join(sys.prefix, ".Python")):
            # We're in a virtualenv, which means sys.path
            # will be broken in alias builds unless we fix
            # it.
            if self.alias or self.semi_standalone:
                prescripts.append("virtualenv")
                prescripts.append(StringIO('_fixup_virtualenv(%r)' % (sys.real_prefix,)))

            if self.site_packages or self.alias:
                import site
                global_site_packages = not os.path.exists(
                        os.path.join(os.path.dirname(site.__file__), 'no-global-site-packages.txt'))
                prescripts.append('virtualenv_site_packages')
                prescripts.append(StringIO('_site_packages(%r, %r, %d)' % (
                    sys.prefix, sys.real_prefix, global_site_packages)))

        elif self.site_packages or self.alias:
            prescripts.append('site_packages')

        if is_system():
            prescripts.append('system_path_extras')

        #if self.style == 'app':
        #    prescripts.append('setup_pkgresource')

        if self.emulate_shell_environment:
            prescripts.append('emulate_shell_environment')

        if self.argv_emulation and self.style == 'app':
            prescripts.append('argv_emulation')
            if 'CFBundleDocumentTypes' not in self.plist:
                self.plist['CFBundleDocumentTypes'] = [
                    {
                        'CFBundleTypeOSTypes' : [
                            '****',
                            'fold',
                            'disk',
                        ],
                        'CFBundleTypeRole': 'Viewer'
                    },
                ]

        if self.argv_inject is not None:
            prescripts.append('argv_inject')
            prescripts.append(
                StringIO('_argv_inject(%r)\n' % (self.argv_inject,)))

        if self.style == 'app' and not self.no_chdir:
            prescripts.append('chdir_resource')
        if not self.alias:
            prescripts.append('disable_linecache')
            prescripts.append('boot_' + self.style)
        else:
            if self.additional_paths:
                prescripts.append('path_inject')
                prescripts.append(
                    StringIO('_path_inject(%r)\n' % (self.additional_paths,)))
            prescripts.append('boot_alias' + self.style)
        newprescripts = []
        for s in prescripts:
            if isinstance(s, basestring):
                newprescripts.append(
                    self.get_bootstrap('py2app.bootstrap.' + s))
            else:
                newprescripts.append(s)

        for target in self.targets:
            prescripts = getattr(target, 'prescripts', [])
            target.prescripts = newprescripts + prescripts


    def get_bootstrap(self, bootstrap):
        if isinstance(bootstrap, basestring):
            if not os.path.exists(bootstrap):
                bootstrap = imp_find_module(bootstrap)[1]
        return bootstrap

    def get_bootstrap_data(self, bootstrap):
        bootstrap = self.get_bootstrap(bootstrap)
        if not isinstance(bootstrap, basestring):
            return bootstrap.getvalue()
        else:
            with open(bootstrap, 'rU') as fp:
                return fp.read()

    def create_pluginbundle(self, target, script, use_runtime_preference=True):
        base = target.get_dest_base()
        appdir = os.path.join(self.dist_dir, os.path.dirname(base))
        appname = self.get_appname()
        print("*** creating plugin bundle: %s ***" % (appname,))
        if self.runtime_preferences and use_runtime_preference:
            self.plist.setdefault(
                'PyRuntimeLocations', self.runtime_preferences)
        appdir, plist = create_pluginbundle(
            appdir,
            appname,
            plist=self.plist,
            extension=self.extension,
            arch=self.arch,
        )
        appdir = fsencoding(appdir)
        resdir = os.path.join(appdir, 'Contents', 'Resources')
        return appdir, resdir, plist

    def create_appbundle(self, target, script, use_runtime_preference=True):
        base = target.get_dest_base()
        appdir = os.path.join(self.dist_dir, os.path.dirname(base))
        appname = self.get_appname()
        print("*** creating application bundle: %s ***" % (appname,))
        if self.runtime_preferences and use_runtime_preference:
            self.plist.setdefault(
                'PyRuntimeLocations', self.runtime_preferences)
        pythonInfo = self.plist.setdefault('PythonInfoDict', {})
        py2appInfo = pythonInfo.setdefault('py2app', {}).update(dict(
            alias=bool(self.alias),
        ))
        appdir, plist = create_appbundle(
            appdir,
            appname,
            plist=self.plist,
            extension=self.extension,
            arch=self.arch,
        )
        appdir = fsencoding(appdir)
        resdir = os.path.join(appdir, 'Contents', 'Resources')
        return appdir, resdir, plist

    def create_bundle(self, target, script, use_runtime_preference=True):
        fn = getattr(self, 'create_%sbundle' % (self.style,))
        return fn(
            target,
            script,
            use_runtime_preference=use_runtime_preference
        )

    def iter_frameworks(self):
        for fn in self.frameworks:
            fmwk = macholib.dyld.framework_info(fn)
            if fmwk is None:
                yield fn
            else:
                basename = fmwk['shortname'] + '.framework'
                yield os.path.join(fmwk['location'], basename)
    
    def build_alias_executable(self, target, script, extra_scripts):
        # Build an alias executable for the target
        appdir, resdir, plist = self.create_bundle(target, script)

        # symlink python executable
        execdst = os.path.join(appdir, 'Contents', 'MacOS', 'python')
        prefixPathExecutable = os.path.join(sys.prefix, 'bin', 'python')
        if os.path.exists(prefixPathExecutable):
            pyExecutable = prefixPathExecutable
        else:
            pyExecutable = sys.executable
        self.symlink(pyExecutable, execdst)

        # make PYTHONHOME
        pyhome = os.path.join(resdir, 'lib', 'python' + sys.version[:3])
        realhome = os.path.join(sys.prefix, 'lib', 'python' + sys.version[:3])
        makedirs(pyhome)
        if self.optimize:
            self.symlink('../../site.pyo', os.path.join(pyhome, 'site.pyo'))
        else:
            self.symlink('../../site.pyc', os.path.join(pyhome, 'site.pyc'))
        self.symlink(
            os.path.join(realhome, 'config'),
            os.path.join(pyhome, 'config'))
            
        
        # symlink data files
        # XXX: fixme: need to integrate automatic data conversion
        for src, dest in self.iter_data_files():
            dest = os.path.join(resdir, dest)
            if src == dest:
                continue
            makedirs(os.path.dirname(dest))
            try:
                copy_resource(src, dest, dry_run=self.dry_run, symlink=1)
            except:
                import traceback
                traceback.print_exc()
                raise

        # symlink frameworks
        for src in self.iter_frameworks():
            dest = os.path.join(
                appdir, 'Contents', 'Frameworks', os.path.basename(src))
            if src == dest:
                continue
            makedirs(os.path.dirname(dest))
            self.symlink(os.path.abspath(src), dest)

        self.compile_datamodels(resdir)
        self.compile_mappingmodels(resdir)

        bootfn = '__boot__'
        bootfile = open(os.path.join(resdir, bootfn + '.py'), 'w')
        for fn in target.prescripts:
            bootfile.write(self.get_bootstrap_data(fn))
            bootfile.write('\n\n')
        bootfile.write("DEFAULT_SCRIPT=%r\n"%(os.path.realpath(script),))
        script_map = {}
        for fn in extra_scripts:
            tgt = os.path.realpath(fn)
            fn = os.path.basename(fn)
            if fn.endswith('.py'):
                script_map[fn[:-3]] = tgt
            elif fn.endswith('.py'):
                script_map[fn[:-4]] = tgt
            else:
                script_map[fn] = tgt

        bootfile.write("SCRIPT_MAP=%r\n"%(script_map,))
        bootfile.write('try:\n')
        bootfile.write('    _run()\n')
        bootfile.write('except KeyboardInterrupt:\n')
        bootfile.write('    pass\n')
        bootfile.close()

        target.appdir = appdir
        return appdir


    def build_executable(self, target, arcname, pkgexts, copyexts, script, extra_scripts):
        # Build an executable for the target
        appdir, resdir, plist = self.create_bundle(target, script)
        self.appdir = appdir
        self.resdir = resdir
        self.plist = plist

        for fn in extra_scripts:
            if fn.endswith('.py'):
                fn = fn[:-3]
            elif fn.endswith('.pyw'):
                fn = fn[:-4]

            src_fn = script_executable(arch=self.arch)
            tgt_fn = os.path.join(self.appdir, 'Contents', 'MacOS', os.path.basename(fn))
            mergecopy(src_fn, tgt_fn)
            make_exec(tgt_fn)


        site_path = os.path.join(resdir, 'site.py')
        byte_compile([
            SourceModule('site', site_path),
            ],
            target_dir=resdir,
            optimize=self.optimize,
            force=self.force,
            verbose=self.verbose,
            dry_run=self.dry_run)
        if not self.dry_run:
            os.unlink(site_path)


        includedir = None
        configdir = None
        if sysconfig is not None:
            includedir = sysconfig.get_config_var('CONFINCLUDEPY')
            configdir = sysconfig.get_config_var('LIBPL')


        if includedir is None:
            includedir = 'python%d.%d'%(sys.version_info[:2])
        else:
            includedir = os.path.basename(includedir)

        if configdir is None:
            configdir = 'config'
        else:
            configdir = os.path.basename(configdir)

        self.compile_datamodels(resdir)
        self.compile_mappingmodels(resdir)

        bootfn = '__boot__'
        bootfile = open(os.path.join(resdir, bootfn + '.py'), 'w')
        for fn in target.prescripts:
            bootfile.write(self.get_bootstrap_data(fn))
            bootfile.write('\n\n')

        bootfile.write("DEFAULT_SCRIPT=%r\n"%(os.path.basename(script),))
        bootfile.write('try:\n')
        bootfile.write('    _run()\n' % os.path.realpath(script))
        bootfile.write('except KeyboardInterrupt:\n')
        bootfile.write('    pass\n')
        bootfile.close()

        target.appdir = appdir
        return appdir

    def build_executable(self, target, arcname, pkgexts, copyexts, script, extra_scripts):
        # Build an executable for the target
        appdir, resdir, plist = self.create_bundle(target, script)
        self.appdir = appdir
        self.resdir = resdir
        self.plist = plist

        for fn in extra_scripts:
            if fn.endswith('.py'):
                fn = fn[:-3]
            elif fn.endswith('.pyw'):
                fn = fn[:-4]

            src_fn = script_executable(arch=self.arch)
            tgt_fn = os.path.join(self.appdir, 'Contents', 'MacOS', os.path.basename(fn))
            mergecopy(src_fn, tgt_fn)
            make_exec(tgt_fn)


        site_path = os.path.join(resdir, 'site.py')
        byte_compile([
            SourceModule('site', site_path),
            ],
            target_dir=resdir,
            optimize=self.optimize,
            force=self.force,
            verbose=self.verbose,
            dry_run=self.dry_run)
        if not self.dry_run:
            os.unlink(site_path)


        includedir = None
        configdir = None
        if sysconfig is not None:
            includedir = sysconfig.get_config_var('CONFINCLUDEPY')
            configdir = sysconfig.get_config_var('LIBPL')


        if includedir is None:
            includedir = 'python%d.%d'%(sys.version_info[:2])
        else:
            includedir = os.path.basename(includedir)

        if configdir is None:
            configdir = 'config'
        else:
            configdir = os.path.basename(configdir)

        self.compile_datamodels(resdir)
        self.compile_mappingmodels(resdir)

        bootfn = '__boot__'
        bootfile = open(os.path.join(resdir, bootfn + '.py'), 'w')
        for fn in target.prescripts:
            bootfile.write(self.get_bootstrap_data(fn))
            bootfile.write('\n\n')

        bootfile.write("DEFAULT_SCRIPT=%r\n"%(os.path.basename(script),))
        bootfile.write('try:\n')
        bootfile.write('    _run()\n' % os.path.realpath(script))
        bootfile.write('except KeyboardInterrupt:\n')
        bootfile.write('    pass\n')
        bootfile.close()

        target.appdir = appdir
        return appdir

    def build_executable(self, target, arcname, pkgexts, copyexts, script, extra_scripts):
        # Build an executable for the target
        appdir, resdir, plist = self.create_bundle(target, script)
        self.appdir = appdir
        self.resdir = resdir
        self.plist = plist

        for fn in extra_scripts:
            if fn.endswith('.py'):
                fn = fn[:-3]
            elif fn.endswith('.pyw'):
                fn = fn[:-4]

            src_fn = script_executable(arch=self.arch)
            tgt_fn = os.path.join(self.appdir, 'Contents', 'MacOS', os.path.basename(fn))
            mergecopy(src_fn, tgt_fn)
            make_exec(tgt_fn)


        site_path = os.path.join(resdir, 'site.py')
        byte_compile([
            SourceModule('site', site_path),
            ],
            target_dir=resdir,
            optimize=self.optimize,
            force=self.force,
            verbose=self.verbose,
            dry_run=self.dry_run)
        if not self.dry_run:
            os.unlink(site_path)


        includedir = None
        configdir = None
        if sysconfig is not None:
            includedir = sysconfig.get_config_var('CONFINCLUDEPY')
            configdir = sysconfig.get_config_var('LIBPL')


        if includedir is None:
            includedir = 'python%d.%d'%(sys.version_info[:2])
        else:
            includedir = os.path.basename(includedir)

        if configdir is None:
            configdir = 'config'
        else:
            configdir = os.path.basename(configdir)

        self.compile_datamodels(resdir)
        self.compile_mappingmodels(resdir)

        bootfn = '__boot__'
        bootfile = open(os.path.join(resdir, bootfn + '.py'), 'w')
        for fn in target.prescripts:
            bootfile.write(self.get_bootstrap_data(fn))
            bootfile.write('\n\n')

        bootfile.write("DEFAULT_SCRIPT=%r\n"%(os.path.basename(script),))

        script_map = {}
        for fn in extra_scripts:
            fn = os.path.basename(fn)
            if fn.endswith('.py'):
                script_map[fn[:-3]] = fn
            elif fn.endswith('.py'):
                script_map[fn[:-4]] = fn
            else:
                script_map[fn] = fn

        bootfile.write("SCRIPT_MAP=%r\n"%(script_map,))
        bootfile.write('_run()\n')
        bootfile.close()

        self.copy_file(script, resdir)
        for fn in extra_scripts:
            self.copy_file(fn, resdir)

        pydir = os.path.join(resdir, 'lib', 'python%s.%s'%(sys.version_info[:2]))
        if sys.version_info[0] == 2 or self.semi_standalone:
            arcdir = os.path.join(resdir, 'lib', 'python' + sys.version[:3])
        else:
            arcdir = os.path.join(resdir, 'lib')
        realhome = os.path.join(sys.prefix, 'lib', 'python' + sys.version[:3])
        self.mkpath(pydir)

        if self.optimize:
            self.symlink('../../site.pyo', os.path.join(pydir, 'site.pyo'))
        else:
            self.symlink('../../site.pyc', os.path.join(pydir, 'site.pyc'))
        cfgdir = os.path.join(pydir, configdir)
        realcfg = os.path.join(realhome, configdir)
        real_include = os.path.join(sys.prefix, 'include')
        if self.semi_standalone:
            self.symlink(realcfg, cfgdir)
            self.symlink(real_include, os.path.join(resdir, 'include'))
        else:
            self.mkpath(cfgdir)
            for fn in 'Makefile', 'Setup', 'Setup.local', 'Setup.config':
                rfn = os.path.join(realcfg, fn)
                if os.path.exists(rfn):
                    self.copy_file(rfn, os.path.join(cfgdir, fn))

            inc_dir = os.path.join(resdir, 'include', includedir)
            self.mkpath(inc_dir)
            self.copy_file(os.path.join(real_include, '%s/pyconfig.h'%(
                includedir)), os.path.join(inc_dir, 'pyconfig.h'))


        self.copy_file(arcname, arcdir)
        if sys.version_info[0] != 2:
            import zlib
            self.copy_file(zlib.__file__, os.path.dirname(arcdir))
        
        ext_dir = os.path.join(pydir, os.path.basename(self.ext_dir))
        self.copy_tree(self.ext_dir, ext_dir, preserve_symlinks=True)
        self.copy_tree(self.framework_dir,
            os.path.join(appdir, 'Contents', 'Frameworks'),
            preserve_symlinks=True)
        for pkg in self.packages:
            pkg = self.get_bootstrap(pkg)
            dst = os.path.join(pydir, os.path.basename(pkg))
            self.mkpath(dst)
            self.copy_tree(pkg, dst)
        for copyext in copyexts:
            fn = os.path.join(ext_dir,
                (copyext.identifier.replace('.', os.sep) +
                os.path.splitext(copyext.filename)[1])
            )
            self.mkpath(os.path.dirname(fn))
            copy_file(copyext.filename, fn, dry_run=self.dry_run)

        if 0 and sys.version_info[:2] >= (3, 2) and not self.alias:
            import encodings
            import encodings.cp437
            import encodings.utf_8
            import encodings.latin_1
            import codecs

            encodings_dir = os.path.join(pydir, 'encodings')
            self.mkpath(encodings_dir)

            byte_compile([
                    SourceModule('encodings.__init__', encodings.__file__),
                    SourceModule('encodings.cp437', encodings.cp437.__file__),
                    SourceModule('encodings.utf_8', encodings.utf_8.__file__),
                    SourceModule('encodings.latin_1', encodings.latin_1.__file__),
                    SourceModule('codecs', codecs.__file__),
                ],
                target_dir=pydir,
                optimize=self.optimize,
                force=self.force,
                verbose=self.verbose,
                dry_run=self.dry_run)

            if not self.dry_run:
                fp = open(os.path.join(encodings_dir, 'aliases.py'), 'w')
                fp.write('aliases = {}\n')
                fp.close()

        for src, dest in self.iter_data_files():
            dest = os.path.join(resdir, dest)
            if src == dest:
                continue
            makedirs(os.path.dirname(dest))
            copy_resource(src, dest, dry_run=self.dry_run)


        target.appdir = appdir
        return appdir

    def create_loader(self, item):
        # Hm, how to avoid needless recreation of this file?
        slashname = item.identifier.replace('.', os.sep)
        pathname = os.path.join(self.temp_dir, "%s.py" % slashname)
        if os.path.exists(pathname):
            if self.verbose:
                print("skipping python loader for extension %r"
                    % (item.identifier,))
        else:
            self.mkpath(os.path.dirname(pathname))
            # and what about dry_run?
            if self.verbose:
                print("creating python loader for extension %r"
                    % (item.identifier,))

            fname = slashname + os.path.splitext(item.filename)[1]
            source = make_loader(fname)
            if not self.dry_run:
                with open(pathname, "w") as fp:
                    fp.write(source)
            else:
                return
        return SourceModule(item.identifier, pathname)

    def make_lib_archive(self, zip_filename, base_dir, verbose=0,
                         dry_run=0):
        # Like distutils "make_archive", except we can specify the
        # compression to use - default is ZIP_STORED to keep the
        # runtime performance up.
        # Also, we don't append '.zip' to the filename.
        from distutils.dir_util import mkpath
        mkpath(os.path.dirname(zip_filename), dry_run=dry_run)

        if self.compressed:
            compression = zipfile.ZIP_DEFLATED
        else:
            compression = zipfile.ZIP_STORED
        if not dry_run:
            z = zipfile.ZipFile(zip_filename, "w",
                                compression=compression)
            save_cwd = os.getcwd()
            os.chdir(base_dir)
            for dirpath, dirnames, filenames in os.walk('.'):
                for fn in filenames:
                    path = os.path.normpath(os.path.join(dirpath, fn))
                    if os.path.isfile(path):
                        z.write(path, path)
            os.chdir(save_cwd)
            z.close()

        return zip_filename

    def copy_tree(self, infile, outfile,
                   preserve_mode=1, preserve_times=1, preserve_symlinks=0,
                   level=1, condition=None):
        """Copy an entire directory tree respecting verbose, dry-run,
        and force flags.

        This version doesn't bork on existing symlinks
        """
        return copy_tree(
            infile, outfile,
            preserve_mode,preserve_times,preserve_symlinks,
            not self.force,
            dry_run=self.dry_run,
            condition=condition)
