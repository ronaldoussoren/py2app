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
 * XXX: This needs a second variant that emulates
 * a python3 executable inside the bundle (for use
 * as sys.executable)
 *
 * XXX: What's needed to support venv from a bundled Python?
 *
 * XXX: T.B.D. how to implement semi-standalone bundles
 *      (which use an installed python and look for that
 *       at run time). Current opinion: drop that feature.
 *
 *       Possibly another axis of variants (see list below for
 *       primary axis) that performs manual runtime linking
 *       of libpython.
 *
 * XXX: The code should be split into several files (probably
 *      as a header-only library) to allow for code reuse in
 *      a number of variants and in the bundle stub)
 *
 *      In the end we need:
 *      - plugin bundle stub
 *      - plugin bundle stub using subinterpreters
 *      - app bundle stub
 *      - python3 command-line tool
 *      - stub for "extra" scripts
 *
 *      the preprocessor can help here, but is not ideal.
 *
 * XXX: The current code just prints to stderr on problems,
 *      but should pop up a GUI instead (see previous implementation)
 *
 *      Should it? Maybe only in semi-standalone mode when it cannot
 *      find Python; in all other cases launch problems are either
 *      bugs in py2app or a user script that doesn't work right)
 *
 */
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include "Python.h"

#import <Cocoa/Cocoa.h>

/* setup_python - Initialize the python interpreter.
 *
 * Will call exit(3) when setting up the interpreter
 * fails for some reason.
 */
static void setup_python(NSBundle* mainBundle, int argc, char* const* argv, char* const* envp)
{
    PyPreConfig preconfig;
    PyConfig config;
    PyStatus status;

    PyPreConfig_InitIsolatedConfig(&preconfig);
    preconfig.utf8_mode = 1;

    /*
     * 2. Customize interpreter pre-configuration using the `PyConfig`
     *    key in the `Info.plist` file.
     */
    NSDictionary* pyconfig = [mainBundle objectForInfoDictionaryKey:@"PyConfig"];
    if (pyconfig != nil && [[pyconfig class] isSubclassOfClass:[NSDictionary class]]) {
        NSNumber* value;

        /*  - malloc debug (bool), default False */
        value = pyconfig[@"malloc_debug"];
        if (value != nil && [[pyconfig class] isSubclassOfClass:[NSNumber class]]) {
            if ([value boolValue]) {
                preconfig.allocator = PYMEM_ALLOCATOR_DEBUG;
            } else {
                preconfig.allocator = PYMEM_ALLOCATOR_DEFAULT;
            }
        }

        /*  - dev_mode (bool), default False  */
        value = pyconfig[@"dev_mode"];
        if (value && [[pyconfig class] isSubclassOfClass:[NSNumber class]]) {
            config.dev_mode = [value boolValue];
        }
    }

    status = Py_PreInitialize(&preconfig);
    if (PyStatus_Exception(status)) goto configerror;


    PyConfig_InitIsolatedConfig(&config);

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
        if (value && [[pyconfig class] isSubclassOfClass:[NSNumber class]]) {
            config.optimization_level = [value intValue];
        }

        /*  - verbose (int), default 0 */
        value = pyconfig[@"verbose"];
        if (value && [[pyconfig class] isSubclassOfClass:[NSNumber class]]) {
            config.verbose = [value intValue];
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

    static NSArray* path_suffixes = @[
        @"python-libraries.zip",
        @"python-libraries",
        @"lib-dynload",
    ];

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


    /* 5. Initialize the Python interpreter: */
    status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    if (PyStatus_Exception(status)) goto configerror;


    /* 6. Inject `sys.bundle_resources` */
    const char* resourcePath = mainBundle.resourcePath.UTF8String;
    PyObject* value = PyUnicode_DecodeUTF8(resourcePath, strlen(resourcePath), NULL);
    if (!value) {
        status = PyStatus_Error("cannot convert bundle resource path to python");
        goto pyerror;
    }

    if (PySys_SetObject("py2app_bundle_resources", value) == -1) {
        status = PyStatus_Error("cannot set sys.bundle_resources");
        goto pyerror;
    }
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


int
main(int argc, char * const *argv, char * const *envp)
{
    NSString* mainPy;
    FILE* mainFile;

    @autoreleasepool {
        NSBundle* mainBundle = [NSBundle mainBundle];

        if (!mainBundle) {
            NSLog(@"Not in an application bundle, exiting");
            return 1;
        }

        clear_bundle_address();
        setup_python(mainBundle, argc, argv, envp);

        mainPy = [[[mainBundle resourcePath] stringByAppendingPathComponent:@"__boot__.py"] retain];
    }


    mainFile = fopen([mainPy UTF8String], "r");
    if (mainFile == NULL) {
        NSLog(@"Cannot open %@, errno=%d", mainPy, errno);
        return 1;
    }

    int rval = PyRun_SimpleFile(mainFile, [mainPy UTF8String]);
    fclose(mainFile);
    [mainPy release];

    /* XXX: Finalizing the interpreter can be problematic, maybe
     *      turn this into a config option?
     */
    Py_Finalize();
    return rval == 0?0:2;
}
