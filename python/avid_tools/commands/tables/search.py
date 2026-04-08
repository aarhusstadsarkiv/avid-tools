import click

from pathlib import Path
from avid_tools.utils import AVID, find_avid_dir
from avid_tools import whitespacevalidate


@click.command("search", no_args_is_help=True, help="Perform full-text search in tables XML files")
@click.option("--text", required=True, type=str)
def cmd_search_tables(text: str):
    """
    Perform full-text search in table XML files
    """
    avid = AVID(find_avid_dir(Path.cwd()))

    whitespacevalidate.search_tables_xml(text, str(avid.indices.tableIndex))
