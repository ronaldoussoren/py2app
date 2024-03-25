import os
import signal
import subprocess


def kill_child_processes():
    parent_pid = os.getpid()
    sig = signal.SIGKILL
    ps_command = subprocess.Popen(
        "ps -o pid,ppid -ax", shell=True, stdout=subprocess.PIPE
    )
    ps_output = ps_command.stdout.read().decode("utf-8")
    ps_command.wait()
    ps_command.stdout.close()
    for line in ps_output.splitlines():
        pid, ppid = line.split()
        if ppid != parent_pid:
            continue
        try:
            os.kill(int(pid), sig)
        except OSError:
            pass

    ps_command = subprocess.Popen("ps -ax", shell=True, stdout=subprocess.PIPE)
    ps_output = ps_command.stdout.read()
    ps_command.wait()
    ps_command.stdout.close()
    ps_output = ps_output.decode("utf-8")

    my_dir = os.path.dirname(__file__) + "/"
    for line in ps_output.splitlines():
        if my_dir in line:
            pid, _ = line.split(None, 1)
            try:
                os.kill(int(pid), sig)
            except OSError:
                pass

    try:
        os.waitpid(0, 0)
    except OSError:
        pass
