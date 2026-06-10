import importlib
import inspect
import logging
import pkgutil
import re
import traceback
import typing as t
from enum import Enum
from pathlib import Path

import avid_validator.config as av_config
from avid_validator import parts
from avid_validator.common.archive import Loadable
from avid_validator.common.archive import ValidationType
from avid_validator.common.description import METHOD_CATEGORIES
from avid_validator.common.description import METHOD_DESCRIPTIONS
from avid_validator.common.description import METHOD_VALIDATORS
from avid_validator.common.report import Report
from avid_validator.common.report import Validator

logger = logging.getLogger(__name__)


def import_all_submodules(package):
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"{package.__name__}.{module_name}")


class Part(Enum):
    SECTION_4A_GENERAL = "section_4a_general"
    SECTION_4B_PLACEMENT = "section_4b_placement"
    SECTION_4C_INDICES = "section_4c_indices"
    SECTION_4D_TABLES = "section_4d_tables"
    SECTION_4E_CONTEXTDOCS = "section_4e_contextdocs"
    SECTION_4F_SCHEMAS = "section_4f_schemas"
    SECTION_4G_DOCUMENTS = "section_4g_documents"
    SECTION_5 = "section_5"


def get_validators(rust_optimize: bool) -> dict[str, Validator]:
    """
    Get a list of validators
    """
    validators = {
        method.name: method.rust or method.primary if rust_optimize else method.primary for method in METHOD_VALIDATORS
    }

    return validators


def _build_kwargs(func: t.Callable) -> dict[str, t.Any]:
    """
    Build kwargs for validation function. These kwargs types must have an 'load' function to be a valid kwarg
    """
    type_hints: dict[str, t.Any] = t.get_type_hints(func)
    type_hints.pop("return", None)

    kwargs: dict[str, t.Any] = {}
    for argname, argtype in type_hints.items():
        load = getattr(argtype, "load", None)
        if not callable(load):
            raise TypeError(f"Parameter {argname!r} has non-loadable type {argtype!r}")

        loadable_type = t.cast(type[Loadable], argtype)
        kwargs[argname] = loadable_type.load()
    return kwargs


def _run_one_validator(name: str, func: Validator) -> list[Report]:
    """
    Run a single validator function
    """
    logger.info("%s", name)

    kwargs = _build_kwargs(func)
    reports: list[Report] = []

    try:
        if inspect.isgeneratorfunction(func):
            for item in func(**kwargs):
                if item is not None:
                    reports.append(item)
        else:
            result = func(**kwargs)
            if isinstance(result, Report):
                reports.append(result)
    except Exception as e:
        if av_config.verbose:
            logger.error(traceback.format_exc())
        reports.append(Report(success=False, reason=str(e)))

    return reports or [Report(success=True)]


def find_parent_matching(pattern: str, start: Path | None = None) -> Path | None:
    """
    Walk up from start (or cwd) and return the first parent directory whose name matches
    the regex pattern.
    """
    if start is None:
        start = Path.cwd()

    regex = re.compile(pattern)

    for parent in [start] + list(start.parents):
        if regex.search(parent.name):
            return parent

    return None


def run_validations(
    checks: t.Sequence[str] | None = None,
    category: t.Sequence[ValidationType] | None = None,
    except_vals: t.Sequence[str] | None = None,
    avid_dir: Path | None = None,
    rust_optimize: bool = False,
) -> None:
    """
    Run validators defined in parts/(part_name) prefixed by "validate_".

    If 'checks' is defined, it only checks validators with names included in 'checks'
    """
    # Make sure all the parts have been imported so the decorated have run
    import_all_submodules(parts)

    if category is None:
        category = []
    if except_vals is None:
        except_vals = []
    if avid_dir is None:
        if starting_dir := find_parent_matching(r"(?i)AVID\..*"):
            av_config.avid_dir = starting_dir
        else:
            raise Exception("No avid directory could be found!")

    all_validators = get_validators(rust_optimize=rust_optimize)

    # Filter by check name(s)
    selected = all_validators if not checks else {name: fn for name, fn in all_validators.items() if name in checks}

    # Filter off except_vals validators
    selected = (
        selected if not except_vals else {name: fn for name, fn in all_validators.items() if name not in except_vals}
    )

    # If categories are defined, filter also by category
    if len(category) != 0:
        selected = {
            name: fn for name, fn in selected.items() if all([name in METHOD_CATEGORIES[cat] for cat in category])
        }

    # Run (selected) validators
    for name, func in selected.items():
        has_described = False
        for report in _run_one_validator(name, func):
            if not report.reason:
                continue

            # Failed if has reason
            descr = METHOD_DESCRIPTIONS.get(name)
            if descr and not has_described:
                logger.info("%s DESCR: %s", name, descr)
                has_described = True

            logger.info("%s FAILED: %s", name, report.reason.replace(r"\n", "\n"))
