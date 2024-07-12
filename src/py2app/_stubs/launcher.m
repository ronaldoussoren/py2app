/*
 * Stub executable for bundles.
 *
 * This stub supports macOS 10.9 or later, and Python 3.8 or later.
 *
 * Code in the stub can use all features of Objective-C except
 * for defining classes and protocols as those can be problematic
 * for the plugin bundle stub due to the possibility of having
 * multiple plugins loaded in the same process.
 *
 * XXX: What's needed to support venv from a bundled Python?
 *
 * XXX: This (like the stub in 0.x) does not support having more
 *      than one Python plugin in a process. Longer term this can
 *      be resolved by using subinterpreters.
 *
 * The build machinery uses a preprocessor define to control which
 * variant is build:
 * - No defines:   Main or secondary executable for an .app bundle
 * - `-DLAUNCH_PYTHON`: Equivalent to `python3` outside of a bundle
 * - `-DPLUGIN_BUNDLE`: Main binary for a plugin bundle
 *
 * Note that all types of binaries only work when located inside a
 * bundle, but can be used outside of the bundle by creating symbolic
 * links in a convenient place.
 */

#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include "Python.h"

#import <Cocoa/Cocoa.h>

#ifdef PLUGIN_BUNDLE
#include <mach-o/dyld.h>
static
const char *bundle_path(void) {
    int i;
    const struct mach_header *myHeader = _dyld_get_image_header_containing_address(&bundle_path);
    uint32_t count = _dyld_image_count();
    for (i = 0; i < count; i++) {
        if (_dyld_get_image_header(i) == myHeader) {
            return _dyld_get_image_name(i);
        }
    }
    abort();
    return NULL;
}

#endif /* PLUGIN_BUNDLE */

#if defined(ENABLE_MACHO_DEBUG) && !defined(PLUGIN_BUNDLE)
#include <mach-o/dyld.h>

static int debug_macho_usage = 0;

/* debug_dyld_usage - Report about shared libraries outside of the app
 *
 * The function logs information about all Mach-O images
 * loaded by the application that are not in the bundle and
 * are also not system libraries.
 *
 * This is primarily meant to be used while testing py2app itself.
 *
 * To enable either add 'debug_macho_usage' to the python configuration
 * in Info.plist, or set 'PY2APP_DEBUG_DYLIB' in the shell environment.
 *
 * Production builds of py2app do not have this feature available.
 */
static void debug_dyld_usage(void)
{
    if (!debug_macho_usage) return;

    uint32_t dylib_count = _dyld_image_count();
    char executable_path[1024];
    uint32_t bufsize = sizeof(executable_path);

    /* Find the bundle path */
    if (_NSGetExecutablePath(executable_path, &bufsize) != 0) {
        NSLog(@"Cannot validate dylib usage due to _NSGetExecutablePath failing");
        return;
    }

    char* end;
    for (int i = 0; i < 3; i++) {
        end = strrchr(executable_path, '/');
        if (!end) {
            NSLog(@"Cannot validate dylib usage unexpected executable path structure");
            return;
        }
        *end-- = 0;
    }
    *end++ = '/';
    *end = 0;
    bufsize = strlen(executable_path);

    for (uint32_t i = 0; i < dylib_count; i++)  {
        const char* image_name = _dyld_get_image_name(i);

        /* Check for system libraries */
        if (strncmp(image_name, "/System/", 8) == 0) {
            continue;
        }
        if (strncmp(image_name, "/usr/", 5) == 0 && strncmp(image_name, "/usr/local/", 11) != 0) {
            continue;
        }

        /* Check for files in the bundle */
        if (strncmp(image_name, executable_path, end-executable_path-1) == 0) {
            continue;
        }

        NSLog(@"Mach-O image outside of the bundle: %s", image_name);
    }
}
#endif /* ENABLE_MACHO_DEBUG */


static int finalize_python = 1;

/* setup_python - Initialize the python interpreter.
 *
 * Will call exit(3) when setting up the interpreter
 * fails for some reason.
 */
static void setup_python(NSBundle* mainBundle, int argc, char* const* argv, char* const* envp)
{
#ifndef LAUNCH_PYTHON
static char path_buffer[MAXPATHLEN*2];
#endif
    PyPreConfig preconfig;
    PyConfig config;
    PyStatus status;
    NSArray* path_suffixes = nil;

    PyPreConfig_InitIsolatedConfig(&preconfig);
    preconfig.utf8_mode = 1;

#ifdef LAUNCH_PYTHON
    preconfig.parse_argv = 1;
#endif

    /*
     * 2. Customize interpreter pre-configuration using the `PyConfig`
     *    key in the `Info.plist` file.
     */
    NSDictionary* pyconfig = [mainBundle objectForInfoDictionaryKey:@"PyConfig"];
    if (pyconfig != nil && [[pyconfig class] isSubclassOfClass:[NSDictionary class]]) {
        NSNumber* value;

        /*  - malloc debug (bool), default False */
        value = pyconfig[@"malloc_debug"];
        if (value != nil && [[value class] isSubclassOfClass:[NSNumber class]]) {
            if ([value boolValue]) {
                preconfig.allocator = PYMEM_ALLOCATOR_DEBUG;
            } else {
                preconfig.allocator = PYMEM_ALLOCATOR_DEFAULT;
            }
        }

        /*  - dev_mode (bool), default False  */
        value = pyconfig[@"dev_mode"];
        if (value && [[value class] isSubclassOfClass:[NSNumber class]]) {
            config.dev_mode = [value boolValue];
        }
    }

    status = Py_PreInitializeFromBytesArgs(&preconfig, argc, (char**)argv);
    if (PyStatus_Exception(status)) goto configerror;


    PyConfig_InitIsolatedConfig(&config);
#ifdef LAUNCH_PYTHON
    config.parse_argv = 1;
#endif

    /* 1. Basic configuration */

    /*    - Don't attempt to write PYC files */
    config.write_bytecode = 0;

    /*    - Install Python's signal handlers (defaults to off in isolated mode) */
    config.install_signal_handlers = 1;

    /*
     * 2. Customize interpreter configuration using the `PyConfig`
     *    key in the `Info.plist` file.
     */
    if (pyconfig != nil && [[pyconfig class] isSubclassOfClass:[NSDictionary class]]) {
        NSNumber* value;

        /*  - optimization_level (int), default 0 */
        value = pyconfig[@"optimization_level"];
        if (value && [[value class] isSubclassOfClass:[NSNumber class]]) {
            config.optimization_level = [value intValue];
        }

        /*  - verbose (int), default 0 */
        value = pyconfig[@"verbose"];
        if (value && [[value class] isSubclassOfClass:[NSNumber class]]) {
            config.verbose = [value intValue];
        }

        /*  - faulthandler (bool), default False */
        value = pyconfig[@"faulthandler"];
        if (value && [[value class] isSubclassOfClass:[NSNumber class]]) {
            config.faulthandler = [value intValue];
        }

        /* - finalize (bool), default True */
        value = pyconfig[@"finalize"];
        if (value && [[value class] isSubclassOfClass:[NSNumber class]]) {
            finalize_python = [value intValue];
        }

        path_suffixes = pyconfig[@"sys.path"];
        if (path_suffixes != nil && ![[path_suffixes class] isSubclassOfClass:[NSArray class]]) {
            path_suffixes = nil;
        }
    }

    /* 3. Perform Path Configuration
     *
     *    See `doc/bundle-structure.rst` for the py2app bundle structure.
     *    That structure is different from the regular `sys.prefix` structure
     *    and therefore the calculates the full path configuration.
     */
    NSURL* resourceURL = mainBundle.resourceURL;
    if (resourceURL == nil) {
        NSLog(@"Cannot determine bundle resources URL");
        goto cocoaerror;
    }

    status = PyConfig_SetBytesString(&config, &config.home,
        [[NSURL URLWithString:@"Contents/Resources" relativeToURL:resourceURL] fileSystemRepresentation]);
    if (PyStatus_Exception(status)) goto configerror;

    status = PyConfig_SetString(&config, &config.platlibdir, L"lib");
    if (PyStatus_Exception(status)) goto configerror;


    status = PyConfig_SetBytesString(&config, &config.program_name, argv[0]);
    if (PyStatus_Exception(status)) goto configerror;

    config.pythonpath_env = NULL;

    status = PyConfig_SetString(&config, &config.base_prefix, config.home);
    if (PyStatus_Exception(status)) goto configerror;

    status = PyConfig_SetBytesString(&config, &config.base_exec_prefix,
        [[NSURL URLWithString:@"bin" relativeToURL:resourceURL] fileSystemRepresentation]);
    if (PyStatus_Exception(status)) goto configerror;

    status = PyConfig_SetBytesString(&config, &config.base_executable,
            [mainBundle pathForAuxiliaryExecutable:@"python3"].UTF8String);
    if (PyStatus_Exception(status)) goto configerror;

    status = PyConfig_SetString(&config, &config.exec_prefix, config.base_exec_prefix);
    if (PyStatus_Exception(status)) goto configerror;

    status = PyConfig_SetString(&config, &config.executable, config.base_executable);
    if (PyStatus_Exception(status)) goto configerror;

    status = PyConfig_SetString(&config, &config.prefix, config.base_prefix);
    if (PyStatus_Exception(status)) goto configerror;

    config.module_search_paths_set = 1;

    /*
     * For alias builds: ...
     * For standalone builds: ...
     * For semi-standalone builds: ...
     */
    config.module_search_paths.items = NULL;
    config.module_search_paths.length = 0;

    if (path_suffixes == nil) {
        path_suffixes = [NSArray arrayWithObjects:
            @"python-libraries.zip",
            @"python-libraries",
            @"lib-dynload",
            NULL
        ];
    }

    for (NSString* suffix in path_suffixes) {
        wchar_t* wstr;
        wstr = Py_DecodeLocale(
                [[NSURL URLWithString:suffix relativeToURL:resourceURL] fileSystemRepresentation],
                NULL);
        if (wstr == NULL) {
            goto cocoaerror;
        }
        status = PyWideStringList_Append(&config.module_search_paths, wstr);
        if (PyStatus_Exception(status)) goto configerror;
    }


    /* 4. Set up sys.argv */
    status = PyConfig_SetBytesArgv(&config, argc, argv);
    if (PyStatus_Exception(status)) goto configerror;

#ifdef LAUNCH_PYTHON
    /* 5. Finish configuration */
    status = PyConfig_Read(&config);
    if (PyStatus_Exception(status)) goto configerror;
#endif


    /* 6. Initialize the Python interpreter: */
    status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    if (PyStatus_Exception(status)) goto configerror;


    /* 7. Inject `sys.py2app_bundle_resources` */
    const char* resourcePath = mainBundle.resourcePath.UTF8String;
    PyObject* value = PyUnicode_DecodeUTF8(resourcePath, strlen(resourcePath), NULL);
    if (!value) {
        status = PyStatus_Error("cannot convert bundle resource path to python");
        goto pyerror;
    }

    if (PySys_SetObject("py2app_bundle_resources", value) == -1) {
        status = PyStatus_Error("cannot set sys.py2app_bundle_resources");
        Py_DECREF(value);
        goto pyerror;
    }
    Py_DECREF(value);

#if !defined(LAUNCH_PYTHON) && !defined(PLUGIN_BUNDLE)
    /* 8. Inject `sys.py2app_argv0` */
    uint32_t path_buffer_size = sizeof(path_buffer);
    if (_NSGetExecutablePath(path_buffer, &path_buffer_size) == -1) {
        status = PyStatus_Error("cannot fetch executable path");
        goto pyerror;
    }

    char* resolved = realpath(path_buffer, NULL);
    if (resolved == NULL) {
        status = PyStatus_Error("cannot fetch executable path");
        goto pyerror;
    }

    value = PyUnicode_DecodeUTF8(resolved, strlen(resolved), NULL);
    free(resolved);
    if (!value) {
        status = PyStatus_Error("cannot convert executable path to python");
        goto pyerror;
    }
    if (PySys_SetObject("py2app_argv0", value) == -1) {
        status = PyStatus_Error("cannot set sys.py2app_argv0");
        Py_DECREF(value);
        goto pyerror;
    }
    Py_DECREF(value);
#endif

#ifdef PLUGIN_BUNDLE
    value = PyLong_FromVoidPtr(mainBundle);
    if (PySys_SetObject("py2app_bundle_address", value) == -1) {
        status = PyStatus_Error("cannot set sys.py2app_bundle_address");
        Py_DECREF(value);
        goto pyerror;
    }
    Py_DECREF(value);
#endif

#ifdef ENABLE_MACHO_DEBUG
    /* 8. Check if dylib loading should be verified */
    if (pyconfig != nil && [[pyconfig class] isSubclassOfClass:[NSDictionary class]]) {
        NSNumber* value;

        /*  - debug_macho_usage (bool), default False */
        value = pyconfig[@"debug_macho_usage"];
        if (value && [[value class] isSubclassOfClass:[NSNumber class]]) {
            debug_macho_usage = [value intValue];
        }
    }

    if (getenv("PY2APP_DEBUG_MACHO") != 0) {
        debug_macho_usage = 1;
    }
#endif /* ENABLE_MACHO_DEBUG */
    return;

pyerror:
    PyErr_Print();
    Py_Finalize();

configerror:
    /*
     * Something went wrong, report the error (if needed)
     * and exit the process.
     */
    if (PyStatus_IsExit(status)) {
        exit(status.exitcode);
    }
    Py_ExitStatusException(status);

cocoaerror:
    exit(42);
}


/* clear_bundle_address: py2app can set `PYOBJC_BUNDLE_ADDRESS`
 * in the * environment, clear this variable. And likewise
 * for the value followed by the pid
 */
static void clear_bundle_address(void)
{
    char buf[128];

    if (getenv("PYOBJC_BUNDLE_ADDRESS") != NULL) {
        unsetenv("PYOBJC_BUNDLE_ADDRESS");
    }
    snprintf(buf, sizeof(buf)-1, "PYOBJC_BUNDLE_ADDRESS%ld", (long)getpid());
    if (getenv(buf) != NULL) {
        unsetenv(buf);
    }
}


#ifndef PLUGIN_BUNDLE
#define ERR 1
int
main(int argc, char * const *argv, char * const *envp)
#else
#define ERR
static void __attribute__ ((constructor)) _py2app_bundle_load(void);

static void _py2app_bundle_load(void)
#endif
{
    NSString* prebootPy;
    FILE* prebootFile;
#ifndef LAUNCH_PYTHON
    NSString* bootPy;
    FILE* bootFile;
#endif
    int rval;

    @autoreleasepool {
        /*
         * The main bundle is determined in a circumspect way to
         * support symlinks to the bundle executable.
         *
         * When such symlinks exist the [NSBundle mainBundle] method
         * does not return an object that refers to the bundle
         * the linked to executable is in.
         */
#ifdef PLUGIN_BUNDLE
        char** envp = _NSGetEnviron();
        char** argv = { bundle_path(), NULL };
        int argc = 1;

        if (argv[0] == NULL) {
            NSLog("Cannot determine path to bundle");
            return;
        }

        char* resolved = realpath(argv[0], NULL);
#else /* !PLUGIN_BUNDLE */

static  char path_buffer[MAXPATHLEN*2];
        uint32_t bufsize = sizeof(path_buffer);

        if (_NSGetExecutablePath(path_buffer, &bufsize) != 0) {
            NSLog(@"Cannot determine path");
            return ERR;
        }

        char* resolved = realpath(path_buffer, NULL);
#endif
        if (resolved == NULL) {
            NSLog(@"Cannot determine path");
            return ERR;
        }

        /* Resolved structure should be "path/to/bundle.app/Contents/MacOS/exe"
         * Drop the last 3 segments.
         */

        for (int i = 0; i < 3 ;i++) {
            char *c = strrchr(resolved, '/');
            if (c == NULL) {
                NSLog(@"Cannot determine path");
                return ERR;
            }
            *c = '\0';
        }

        NSBundle* mainBundle = [NSBundle bundleWithPath:[NSString stringWithUTF8String:resolved]];
        if (!mainBundle) {
            NSLog(@"Not in a bundle, exiting");
            return ERR;
        }

        if (Py_IsInitialized()) {
            /* See comment at the start of this file */
            NSLog(@"The Python interpreter is already initialized, bailing out");
            return ERR;
        }

        clear_bundle_address();
        setup_python(mainBundle, argc, argv, envp);
        free(resolved);

        prebootPy = [[[mainBundle resourcePath] stringByAppendingPathComponent:@"__preboot__.py"] retain];
#ifndef LAUNCH_PYTHON
        bootPy = [[[mainBundle resourcePath] stringByAppendingPathComponent:@"__boot__.py"] retain];
#endif
    }


    prebootFile = fopen([prebootPy UTF8String], "r");
    if (prebootFile == NULL) {
        NSLog(@"Cannot open %@, errno=%d", prebootPy, errno);
        return ERR;
    }

#ifndef LAUNCH_PYTHON
    bootFile = fopen([bootPy UTF8String], "r");
    if (bootFile == NULL) {
        NSLog(@"Cannot open %@, errno=%d", bootPy, errno);
        fclose(prebootFile);
        return ERR;
    }
#endif

    rval = PyRun_SimpleFile(prebootFile, [prebootPy UTF8String]);
    if (rval == 0) {
#ifndef LAUNCH_PYTHON
        rval = PyRun_SimpleFile(bootFile, [bootPy UTF8String]);
#elif defined(LAUNCH_PYTHON)
        rval = Py_RunMain();
#endif
    }

    fclose(prebootFile);
    [prebootPy release];

#ifndef LAUNCH_PYTHON
    fclose(bootFile);
    [bootPy release];
#endif

#ifdef PLUGIN_BUNDLE
    /* Whatever happened, we cannot finalize the Python interpreter */

    PyErr_Clear();
    PyGILState_Release(gilState);
    if (gilState == PyGILState_LOCKED) {
        PyEval_SaveThread();
    }

#else /* !PLUGIN_BUNDLE */

#ifdef ENABLE_MACHO_DEBUG
    debug_dyld_usage();
#endif /* ENABLE_MACHO_DEBUG */


    if (finalize_python) {
        Py_Finalize();
    }
#ifndef LAUNCH_PYTHON
    return rval == 0?0:2;
#else
    return rval;
#endif

#endif /* !PLUGIN_BUNDLE */
}
