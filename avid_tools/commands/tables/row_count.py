from pathlib import Path
from xml.sax import ContentHandler
from xml.sax import parse as sax_parse
from xml.sax.xmlreader import AttributesImpl

from click import BadParameter
from click import command
from click import Context
from click import IntRange
from click import option
from click import pass_context

from avid_tools.database import create_database
from avid_tools.database import update_md5
from avid_tools.indices import read_table_index
from avid_tools.indices import write_table_index
from avid_tools.utils import AVID
from avid_tools.utils import ctx_params
from avid_tools.utils import find_avid_dir
from avid_tools.utils import validate_xml


class ContentHandlerRowCount(ContentHandler):
    def __init__(self):
        super().__init__()
        self.rows = 0

    def startElement(self, name: str, attrs: AttributesImpl):
        if name == "row":
            self.rows += 1


@command("update-row-count", no_args_is_help=True)
@option("--table", "-t", "table_ids", metavar="ID", type=IntRange(min=1), multiple=True)
@pass_context
def cmd_update_row_count(ctx: Context, table_ids: tuple[int, ...]):
    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    db_path: Path = avid.dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    tables = avid.tables

    if invalid_ids := [i for i in table_ids if i not in tables]:
        raise BadParameter(f"no tables with ID {', '.join(map(str, invalid_ids))}", ctx, ctx_params(ctx)["table_ids"])

    table_index: dict = read_table_index(avid)
    table_index_tables: dict[int, dict] = {
        int(t["folder"].removeprefix("table")): t for t in table_index["tables"]["table"]
    }
    table_ids = table_ids or tuple(sorted(table_index_tables.keys()))

    for table_id in table_ids:
        file: Path = tables[table_id]

        with file.open("r") as fh:
            handler = ContentHandlerRowCount()
            sax_parse(fh, handler)

        table_index_tables[table_id]["rows"] = str(handler.rows)

    table_index["tables"]["table"] = [table_index_tables[i] for i in sorted(table_index_tables.keys())]

    write_table_index(avid, table_index)
    validate_xml(avid.indices.tableIndex, avid.schemas.tableIndex)
    update_md5(conn, avid.indices.tableIndex)
    conn.commit()
