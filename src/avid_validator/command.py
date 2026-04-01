import logging

import click

from avid_validator import config as av_config
from avid_validator import log  # pyright: ignore
from avid_validator import runner
from avid_validator.common.archive import ValidationType
from avid_validator.common import utils

from pathlib import Path
from tqdm import tqdm


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
@click.option(
    "--rust-optimize",
    type=bool,
    is_flag=True,
    default=False
)
def cmd_validate_all(check: list[str], verbose: bool, categories: list[str], except_vals: list[str], rust_optimize: bool):
    """
    Run archive validation tests
    """
    av_config.verbose = verbose

    valtype_categories = [ValidationType(cat.lower()) for cat in categories]

    logger.info("Running validator!")
    runner.run_validations(checks=check, category=valtype_categories, except_vals=except_vals, rust_optimize=rust_optimize)

@click.command("cvalidprog")
def cmd_test_tables(check: list[str], verbose: bool, categories: list[str], except_vals: list[str], rust_optimize: bool):
    """
    Test specific tables
    """
    tables = Path().cwd().rglob("Tables/table*/table*.xml")
    for table_xml_path in tqdm(tables):
        if table_xml_path.stem not in ["table268", "table559", "table269", "table267", "table270", "table559", "table558"]:
            continue
        table_xsd_path = table_xml_path.parent.joinpath(f"{table_xml_path.stem}.xsd")
        
        res, errs = utils.lxml_xml_validate(table_xml_path, table_xsd_path)
        if not res:
            print(errs)
            print(f"Error occurred in {table_xml_path}")
