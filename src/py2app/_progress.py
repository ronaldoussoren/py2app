import typing

import rich.progress

T = typing.TypeVar("T")


class Progress:
    def __init__(self, level: int = 1) -> None:
        self._progress = rich.progress.Progress(
            *rich.progress.Progress.get_default_columns()[:-1],
            rich.progress.TimeElapsedColumn(),
            rich.progress.TextColumn("{task.fields[current]}"),
            transient=True,
        )
        self._progress.start()
        self._level = level
        self.have_error = False

    def stop(self) -> None:
        self._progress.stop()

    def add_task(self, name: str, count: int | None) -> rich.progress.TaskID:
        return self._progress.add_task(name, total=count, current="", start=True)

    def step_task(self, task_id: rich.progress.TaskID) -> None:
        self._progress.advance(task_id)

    def iter_task(
        self, items: typing.Sequence[T], label: str, current: typing.Callable[[T], str]
    ) -> typing.Iterator[T]:
        task_id = self.add_task(label, count=len(items))

        for value in items:
            self.update(task_id, current=current(value))
            yield value
            self.step_task(task_id)

        self.update(task_id, current="")

    def update(self, task_id: rich.progress.TaskID, **kwds: typing.Any) -> None:
        self._progress.update(task_id, **kwds)

    def task_done(self, task_id: rich.progress.TaskID) -> None:
        task = self._progress.tasks[task_id]
        if task.total is None:
            self._progress.update(task_id, total=task.completed, current="")

    def print(  # noqa: A003
        self, message: str, *, highlight: typing.Optional[bool] = None
    ) -> None:
        if highlight is not None:
            self._progress.print(message, highlight=highlight)
        else:
            self._progress.print(message)

    def info(self, message: str, *, highlight: typing.Optional[bool] = None) -> None:
        if self._level >= 1:
            self.print(message, highlight=highlight)

    def trace(self, message: str) -> None:
        if self._level >= 2:
            self._progress.print(message)

    def warning(self, message: str) -> None:
        # XXX: Color doesn't work?
        if message:
            self._progress.print(f":orange_circle: {message}")

    def error(self, message: str) -> None:
        if message:
            self._progress.print(f":red_circle: {message}")
        self.have_error = True
