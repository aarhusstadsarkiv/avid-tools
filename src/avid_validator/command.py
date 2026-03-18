import logging
from pathlib import Path

import click

from avid_validator import config as av_config
from avid_validator import log  # pyright: ignore
from avid_validator import runner
from avid_validator.common.archive import ValidationType

log.configure_logging()
logger = logging.getLogger(__name__)


@click.command("run")
@click.option(
    "--check",
    type=str,
    default=[],
    multiple=True,
    help="Check specific validation function(s)",
)
@click.option(
    "--verbose",
    is_flag=True,
    type=bool,
    default=False,
    help="Set logging level to DEBUG",
)
@click.option(
    "--category",
    "categories",
    type=click.Choice([v.value for v in ValidationType], case_sensitive=False),
    default=[],
    multiple=True,
    help="Run all validators of type",
)
@click.option(
    "--except",
    "except_vals",
    type=str,
    default=[],
    multiple=True,
    help="Validators to not check",
)
def cmd_validate_all(check: list[str], verbose: bool, categories: list[str], except_vals: list[str]):
    """
    Run archive validation tests
    """
    av_config.verbose = verbose

    valtype_categories = [ValidationType(cat.lower()) for cat in categories]

    logger.info("Running validator!")
    runner.run_validations(checks=check, category=valtype_categories, except_vals=except_vals)
