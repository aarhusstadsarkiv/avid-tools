import logging
from pathlib import Path

import click
import xmltodict
from avid_tools.utils import AVID
from avid_tools.utils import find_avid_dir
from avid_tools.versioncontrol import AVIDEditFile
from avid_tools.versioncontrol import AVIDVersionControl

logger = logging.getLogger(__name__)



def _add_missing_pkeys(table_index: Path):
    """
    Add missing primary key if it is missing for a table
    """
    avidvc = AVIDVersionControl()
    with AVIDEditFile(avidvc, table_index):
        with open(table_index, "rb") as f:
            table_index_dict = xmltodict.parse(f)

        tables = table_index_dict["siardDiark"]["tables"]["table"]

        has_modified = False
        for table in tables:
            # Use the first column in table as primary key
            pk_column = table["columns"]["column"][0]["name"]

            if table.get("primaryKey") is None:
                has_modified = True
                table["primaryKey"] = {"name": f"AV_{table['name']}", "column": pk_column}

        if has_modified:
            with open(table_index, "w", encoding="utf-8") as f:
                f.write(xmltodict.unparse(table_index_dict, pretty=True, indent=4))

@click.group("keys")
def grp_keys():
    """
    Work with primary and foreign keys of tables
    """


@grp_keys.command("add-primary")
def cmd_add_primary_keys():
    """
    Add primary keys to all tables in tableIndex that lack it.

    The first column listed in the table is then specified to be the primary key for that table.
    """
    avid = AVID(find_avid_dir(Path.cwd()))

    table_index = avid.indices.tableIndex

    _add_missing_pkeys(table_index)
