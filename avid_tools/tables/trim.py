from pathlib import Path
from re import compile as re_compile
from re import Pattern
from typing import Optional
from typing import TextIO
from xml.sax import ContentHandler
from xml.sax import parse as sax_parse
from xml.sax.saxutils import escape
from xml.sax.saxutils import quoteattr
from xml.sax.xmlreader import AttributesImpl

from click import BadParameter
from click import command
from click import Context
from click import IntRange
from click import option
from click import pass_context

from avid_tools.utils import argument_avid_dir
from avid_tools.utils import AVID
from avid_tools.utils import ctx_params
from avid_tools.utils import print_line

from .utils import Column
from .utils import read_table_schema

_whitespace: str = "".join(map(chr, range(0, 33)))
_col_name: Pattern = re_compile(r"^c\d+$")
_escape_entities: dict[str, str] = {'"': "&quot;"}


class ContentHandlerTrim(ContentHandler):
    def __init__(self, file_handle: TextIO, columns: dict[str, Column]):
        super().__init__()
        self.handle: TextIO = file_handle
        self.columns: dict[str, Column] = columns
        self.current_tag: Optional[str] = None
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


@command("trim", no_args_is_help=True)
@argument_avid_dir(True)
@option("--table", "-t", "table_ids", metavar="ID", type=IntRange(1), multiple=True)
@pass_context
def cmd_trim(ctx: Context, avid_dir: Path, table_ids: tuple[int, ...]):
    avid = AVID(avid_dir)
    tables = avid.tables
    schemas = avid.schemas.tables
    table_ids = table_ids or tuple(tables.keys())

    if invalid_ids := [i for i in table_ids if i not in tables]:
        raise BadParameter(f"no tables with ID {', '.join(map(str, invalid_ids))}", ctx, ctx_params(ctx)["table_ids"])

    for table_id in table_ids:
        columns: list[Column] = read_table_schema(schemas[table_id])
        file: Path = tables[table_id]
        out_file: Path = file.with_name("." + file.name)

        try:
            _, clear_line = print_line(f"{file.name}/cleaning... ", end="", flush=True)

            with file.open("r", encoding="utf-8") as fi:
                with out_file.open("w", encoding="utf-8") as fo:
                    sax_parse(fi, ContentHandlerTrim(fo, {c.name: c for c in columns}))

            new_size, old_size = out_file.stat().st_size, file.stat().st_size

            clear_line()

            if new_size != old_size:
                out_file.replace(file)
                print(f"{file.name}/saved {new_size}B")
                print(f"{file.name}/removed {old_size - new_size}B")
            else:
                print(f"{file.name}/no changes")
        finally:
            out_file.unlink(missing_ok=True)
