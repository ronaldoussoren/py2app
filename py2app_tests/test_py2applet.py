import unittest
import subprocess
import os, shutil, sys
from py2app import script_py2applet
import py2app
if __name__ == "__main__":
    from tools import kill_child_processes
else:
    from .tools import kill_child_processes


class TestPy2Applet (unittest.TestCase):
    def setUp(self):
        self.testdir = 'test.dir'
        os.mkdir(self.testdir)

    def tearDown(self):
        shutil.rmtree(self.testdir)
        kill_child_processes()

    def run_py2applet(self, *args):
        env=os.environ.copy()
        env['TMPDIR'] = os.getcwd()
        pp = os.path.dirname(os.path.dirname(py2app.__file__))
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = pp + ':' + env['PYTHONPATH']
        else:
            env['PYTHONPATH'] = pp

        scriptfn = script_py2applet.__file__
        if scriptfn.endswith('.pyc'):
            scriptfn = scriptfn[:-1]

        p = subprocess.Popen([
            sys.executable, scriptfn ] + list(args),
            cwd = self.testdir,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            stdin = subprocess.PIPE,
            env=env)
        p.stdin.write('y\n'.encode('ascii'))
        data = p.communicate()[0]

        xit = p.wait()
        if xit != 0:
            sys.stdout.write(data.decode('latin1'))
            self.fail("Running py2applet %s failed"%(" ".join(args),))


    def test_generate_setup(self):
        self.run_py2applet('--make-setup', 'foo.py')

        setupfn = os.path.join(self.testdir, 'setup.py')
        self.assertTrue(os.path.exists(setupfn))
        fp = open(setupfn, 'r')
        contents = fp.read()
        fp.close()

        self.assertTrue("APP = ['foo.py']" in contents)


if __name__ == "__main__":
    unittest.main()
