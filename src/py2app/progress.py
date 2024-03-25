"""
Basic progress reporting and logging

The interface is a work in progress, and might
be dropped later in favour of direct usage of
rich.progress
"""

import rich.progress


class Progress:
    def __init__(self, level: int = 2) -> None:
        # XXX: Reduce the default level after finding
        #      a nicer way to report progress on
        #      copying files.
        self._progress = rich.progress.Progress()
        self._progress.start()
        self._level = level

    def stop(self) -> None:
        self._progress.stop()

    def add_task(self, name: str, count: int) -> rich.progress.TaskID:
        return self._progress.add_task(name, total=count)

    def step_task(self, task_id: rich.progress.TaskID) -> None:
        self._progress.advance(task_id)

    def info(self, message: str) -> None:
        if self._level >= 1:
            self._progress.print(message)

    def trace(self, message: str) -> None:
        if self._level >= 2:
            self._progress.print(message)

    def warning(self, message: str) -> None:
        self._progress.print(f"[red]{message}[/red]")
