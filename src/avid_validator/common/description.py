from collections.abc import Callable
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ParamSpec
from typing import TypeVar

from avid_validator.common.archive import ValidationType
from avid_validator.common.report import Validator

METHOD_DESCRIPTIONS: dict[str, str] = {}
METHOD_CATEGORIES: dict[ValidationType, set[str]] = {}
METHOD_VALIDATORS: set[ValidatorMeta] = set()


P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True)
class ValidatorMeta:
    name: str
    primary: Validator
    rust: Validator | None = None


def describe(description: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Describe a validator's purpose
    """

    def grab_description(func: Callable[P, R]) -> Callable[P, R]:
        METHOD_DESCRIPTIONS[func.__name__] = description
        return func

    return grab_description


def register(
    validation_types: Iterable[ValidationType] | ValidationType,
    rust: Validator | None = None
    ) -> Callable[[Validator], Validator]:
    """
    Categorize a validator function, and registers an equivalent but faster rust method.
    This is a required decorator for all validator functions!

    Args:
        validation_types
        rust (Callable): A faster equivalent Rust method
    """

    def add_categories(func: Validator) -> Validator:
        METHOD_VALIDATORS.add(ValidatorMeta(
            name=func.__name__,
            primary=func,
            rust=rust
        ))
        it_validation_types = (
            [validation_types]
            if isinstance(validation_types, ValidationType)
            else validation_types
        )
        for val_type in it_validation_types:
            METHOD_CATEGORIES.setdefault(val_type, set()).add(func.__name__)
        return func

    return add_categories
