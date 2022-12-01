import typing


class RecipeInfo(typing.TypedDict, total=False):
    expected_missing_imports: typing.Set[str]
    packages: typing.Sequence[str]
    flatpackages: typing.Sequence[typing.Union[str, typing.Tuple[str, str]]]
    loader_files: typing.Sequence[
        typing.Union[str, typing.Tuple[str, typing.Sequence[str]]]
    ]
    prescripts: typing.Sequence[typing.Union[str, typing.IO[str]]]
    includes: typing.Sequence[str]
    resources: typing.Sequence[
        typing.Union[
            str, typing.Tuple[str, typing.Sequence[typing.Union[str, typing.IO[str]]]]
        ]
    ]
    frameworks: typing.Sequence[str]
    use_old_sdk: bool
