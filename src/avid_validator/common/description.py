from typing import Callable, Iterable, ParamSpec, TypeVar

from avid_validator.common.archive import ValidationType

METHOD_DESCRIPTIONS: dict[str, str] = {}
METHOD_CATEGORIES: dict[ValidationType, set[str]] = {}


P = ParamSpec("P")
R = TypeVar("R")


def describe(description: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Describe a validator's purpose
    """

    def grab_description(func: Callable[P, R]) -> Callable[P, R]:
        METHOD_DESCRIPTIONS[func.__name__] = description
        return func

    return grab_description


def categorize(
    validation_types: Iterable[ValidationType] | ValidationType,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Categorize a validator function
    """

    def add_categories(func: Callable[P, R]) -> Callable[P, R]:
        it_validation_types = (
            [validation_types]
            if isinstance(validation_types, ValidationType)
            else validation_types
        )
        for val_type in it_validation_types:
            METHOD_CATEGORIES.setdefault(val_type, set()).add(func.__name__)
        return func

    return add_categories
