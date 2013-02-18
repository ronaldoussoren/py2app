#include "Python.h"
#include "sharedlib.h"

#define _STR(x) #x
#define STR(x) _STR(x)

static PyObject*
mod_function(PyObject* mod __attribute__((__unused__)), PyObject* arg)
{
	int value = PyLong_AsLong(arg);
	if (PyErr_Occurred()) {
		return NULL;
	}
	value = FUNC_NAME(value);
	return PyLong_FromLong(value);
}

static PyMethodDef mod_methods[] = {
	{
		STR(NAME),
		(PyCFunction)mod_function,
		METH_O,
		0
	},
	{ 0, 0, 0, 0 }
};

#if PY_VERSION_HEX >= 0x03000000

static struct PyModuleDef mod_module = {
	PyModuleDef_HEAD_INIT,
	STR(NAME),
	NULL,
	0,
	mod_methods,
	NULL,
	NULL,
	NULL,
	NULL
};

#define INITERROR() return NULL
#define INITDONE() return m

PyObject* INITFUNC(void);

PyObject*
INITFUNC(void)

#else

#define INITERROR() return
#define INITDONE() return


void INITFUNC(void);

void
INITFUNC(void)
#endif

{
	PyObject* m;


#if PY_VERSION_HEX >= 0x03000000
	m = PyModule_Create(&mod_module);
#else
	m = Py_InitModule4(STR(NAME), mod_methods,
		NULL, NULL, PYTHON_API_VERSION);
#endif
	if (!m) {
		INITERROR();
	}

	INITDONE();
}
