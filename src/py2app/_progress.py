import typing

import rich.progress

T = typing.TypeVar("T")


class Progress:
    def __init__(self, level: int = 1) -> None:
        self._progress = rich.progress.Progress(
            *rich.progress.Progress.get_default_columns()[:-1],
            rich.progress.TimeElapsedColumn(),
            rich.progress.TextColumn("{task.fields[current]}"),
        )
        self._progress.start()
        self._level = level

    def stop(self) -> None:
        self._progress.stop()

    def add_task(self, name: str, count: int) -> rich.progress.TaskID:
        return self._progress.add_task(name, total=count, current="", start=True)

    def step_task(self, task_id: rich.progress.TaskID) -> None:
        self._progress.advance(task_id)

    def iter_task(
        self, items: typing.List[T], label: str, current=typing.Callable[[T], str]
    ) -> typing.Iterator[T]:
        task_id = self.add_task(label, count=len(items))

        for value in items:
            self.update(task_id, current=current(value))
            yield value
            self.step_task(task_id)

        self.update(task_id, current="")

    def update(self, task_id: rich.progress.TaskID, **kwds):
        self._progress.update(task_id, **kwds)

    def info(self, message: str) -> None:
        if self._level >= 1:
            self._progress.print(message)

    def trace(self, message: str) -> None:
        if self._level >= 2:
            self._progress.print(message)

    def warning(self, message: str) -> None:
        self._progress.print(f"[red]{message}[/red]")
