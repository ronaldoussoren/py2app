#include "Python.h"
#include "libfoo.h"


static PyMethodDef mod_methods[] = {
	{ 0, 0, 0, 0}
};

#if PY_VERSION_HEX >= 0x03000000

static struct PyModuleDef mod_module = {
	PyModuleDef_HEAD_INIT,
	"foo",
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

PyObject* PyInit_foo(void);

PyObject*
PyInit_foo(void)

#else

#define INITERROR() return
#define INITDONE() return

void initfoo(void);

void
initfoo(void)
#endif
{
	PyObject* m;

#if PY_VERSION_HEX >= 0x03000000
	m = PyModule_Create(&mod_module);
#else
	m = Py_InitModule4("foo", mod_methods,
		NULL, NULL, PYTHON_API_VERSION);
#endif
	if (!m) {
		INITERROR();
	}

	if (PyModule_AddIntConstant(m, "sq_1", square(1))) {
		INITERROR();
	}

	if (PyModule_AddIntConstant(m, "sq_2", square(2))) {
		INITERROR();
	}

	INITDONE();
}
