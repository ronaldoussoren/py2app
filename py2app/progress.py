import rich.progress


class Progress:
    def __init__(self, level=2):
        # XXX: Reduce the default level after finding
        #      a nicer way to report progress on
        #      copying files.
        self._progress = rich.progress.Progress()
        self._progress.start()
        self._level = level

    def stop(self):
        self._progress.stop()

    def add_task(self, name, count):
        return self._progress.add_task(name, total=count)

    def step_task(self, task_id):
        self._progress.advance(task_id)

    def info(self, message):
        if self._level >= 1:
            self._progress.print(message)

    def trace(self, message):
        if self._level >= 2:
            self._progress.print(message)

    def warning(self, message):
        self._progress.print(f"[red]{message}[/red]")
