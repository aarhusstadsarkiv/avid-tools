import logging
from pathlib import Path
from re import compile as re_compile
from re import Pattern
from typing import TextIO
from xml.sax import ContentHandler
from xml.sax import parse as sax_parse
from xml.sax.saxutils import escape
from xml.sax.saxutils import quoteattr
from xml.sax.xmlreader import AttributesImpl

from avid_tools.utils import AVID
from avid_tools.utils import ctx_params
from avid_tools.utils import print_line
from avid_tools.versioncontrol import AVIDEditFile, AVIDVersionControl
from click import BadParameter
from click import command
from click import Context
from click import IntRange
from click import option
from click import pass_context

from ...database import create_database
from ...database import update_md5
from ...utils import find_avid_dir
from ...utils import option_help
from .utils import Column
from .utils import read_table_schema

_whitespace: str = "".join(map(chr, range(33)))
_col_name: Pattern = re_compile(r"^c\d+$")
_escape_entities: dict[str, str] = {'"': "&quot;"}


logger = logging.getLogger(__name__)


class ContentHandlerTrim(ContentHandler):
    def __init__(self, file_handle: TextIO, columns: dict[str, Column]):
        super().__init__()
        self.handle: TextIO = file_handle
        self.columns: dict[str, Column] = columns
        self.current_tag: str | None = None
        self.current_tag_is_col: bool = False
        self.current_content: str = ""

    def startDocument(self):
        self.handle.write('<?xml version="1.0" encoding="UTF-8" ?>\n')

    def startElement(self, name: str, attrs: AttributesImpl):
        self.current_tag_is_col = self.current_tag in ("row", None) and _col_name.match(name) is not None
        self.current_tag = name
        if not self.current_tag_is_col:
            attrs_string: str = " ".join(f"{n}={quoteattr(v)}" for n, v in attrs.items())
            self.handle.write(f"<{name} {attrs_string}".strip() + ">")

    def characters(self, content: str):
        if self.current_tag:
            self.current_content += content

    def endElement(self, name: str):
        if self.current_tag_is_col and self.current_tag not in self.columns:
            pass
        elif self.current_tag_is_col:
            self.current_content = self.current_content.strip(_whitespace)
            if self.current_content:
                self.handle.write(f"<{name}>{escape(self.current_content, _escape_entities)}</{name}>")
            elif self.columns[self.current_tag].nullable:
                self.handle.write(f'<{name} xsi:nil="true"/>')
            else:
                self.handle.write(f"<{name}/>")
        else:
            self.handle.write(f"{escape(self.current_content, _escape_entities).strip(_whitespace)}</{name}>")

        self.current_tag = None
        self.current_tag_is_col = False
        self.current_content = ""


@command("trim", no_args_is_help=True, add_help_option=False, short_help="Trim tabelværdier.")
@option("--table", "-t", "table_ids", metavar="ID", type=IntRange(1), multiple=True, help="Vælg tabeller.")
@option_help()
@pass_context
def cmd_trim(ctx: Context, table_ids: tuple[int, ...]):
    """
    Trim tabelværdier og sæt NULL værdier.

    Tomme kollonner med nillable=true i tabelskema sættes til NULL med xsi:nil="true".

    Som default trimmes alle tabeller. Det kan overrides med --table.
    """
    avid_path = find_avid_dir(Path.cwd())
    avid: AVID = AVID(avid_path)
    db_path: Path = avid.dir.joinpath("_metadata", "avid_tools.db")
    conn = create_database(db_path)
    tables = avid.tables
    schemas = avid.schemas.tables
    table_ids = table_ids or tuple(tables.keys())
    avidvc = AVIDVersionControl(avid_path)

    if invalid_ids := [i for i in table_ids if i not in tables]:
        raise BadParameter(f"no tables with ID {', '.join(map(str, invalid_ids))}", ctx, ctx_params(ctx)["table_ids"])

    for table_id in table_ids:
        columns: list[Column] = read_table_schema(schemas[table_id])
        file: Path = tables[table_id]
        out_file: Path = file.with_name("." + file.name)

        with AVIDEditFile(avidvc, file):
            try:
                _, clear_line = print_line(f"{file.name}/cleaning... ", end="", flush=True)

                with file.open("r", encoding="utf-8") as fi, out_file.open("w", encoding="utf-8") as fo:
                    sax_parse(fi, ContentHandlerTrim(fo, {c.name: c for c in columns}))

                clear_line()

                _, clear_line = print_line(f"{file.name}/updating hash... ", end="", flush=True)

                out_file.replace(file)

                update_md5(conn, file)
                conn.commit()

                clear_line()
            finally:
                out_file.unlink(missing_ok=True)
