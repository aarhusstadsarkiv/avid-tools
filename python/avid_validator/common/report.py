from typing import Generator, Optional, Callable, Union, Iterator
from dataclasses import dataclass

type OptReport = Optional[Report]
type GenReport = Generator[Optional[Report]]
Validator = Callable[..., Union[OptReport, Iterator[OptReport]]]


def ok() -> OptReport:
    return Report(success=True)


def fail(reason: str) -> OptReport:
    return Report(success=False, reason=reason)


@dataclass
class Report:
    """
    Report for a validator's results
    """

    success: bool
    reason: Optional[str] = None
