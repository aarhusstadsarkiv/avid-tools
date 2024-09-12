from json import dumps
from pathlib import Path
from re import compile as re_compile
from re import IGNORECASE
from re import Pattern
from typing import Callable
from xml.sax import ContentHandler
from xml.sax import parse as sax_parse
from xml.sax.xmlreader import AttributesImpl

from click import argument
from click import BadParameter
from click import command
from click import Context
from click import IntRange
from click import option
from click import pass_context

from avid_tools.utils import argument_avid_dir
from avid_tools.utils import AVID
from avid_tools.utils import ctx_params


class ContentHandlerTableSearch(ContentHandler):
    def __init__(self, regexp: Pattern[str], on_match: Callable[[int, list[str]], None], limit: int | None = None):
        super().__init__()
        self.regexp: Pattern[str] = regexp
        self.on_match: Callable[[int, list[str]], None] = on_match
        self.limit: int | None = limit
        self.is_row: bool = False
        self.is_column: bool = False
        self.row_number: int = 0
        self.row_columns: list[str] = []
        self.matches: int = 0

    def startElement(self, name: str, attrs: AttributesImpl):
        if name == "row":
            self.is_row: bool = True
            self.row_number += 1
        elif self.is_row and name[0] == "c":
            self.is_column = True
            self.row_columns.append("")

    def characters(self, content: str):
        if self.is_column:
            self.row_columns[-1] += content

    def endElement(self, name: str):
        if name == "row":
            if any(self.regexp.search(c) for c in self.row_columns):
                self.on_match(self.row_number, self.row_columns)
                self.matches += 1
                if self.limit and self.matches >= self.limit:
                    raise StopIteration
            self.is_row = False
            self.is_column = False
            self.row_columns: list[str] = []
        elif self.is_column and name[0] == "c":
            self.is_column = False


@command("search", no_args_is_help=True)
@argument_avid_dir(True)
@argument("patterns", metavar="PATTERN...", nargs=-1, required=True)
@option("--table", "-t", "table_ids", metavar="ID", type=IntRange(min=1), multiple=True)
@option("--limit", type=IntRange(1), default=None)
@option("--columns/--no-columns", "show_columns", is_flag=True, default=True)
@pass_context
def cmd_search(
    ctx: Context,
    avid_dir: Path,
    patterns: tuple[str, ...],
    table_ids: tuple[int, ...],
    limit: int | None,
    show_columns: bool,
):
    avid = AVID(avid_dir)
    tables = avid.tables

    if invalid_ids := [i for i in table_ids if i not in tables]:
        raise BadParameter(f"no tables with ID {', '.join(map(str, invalid_ids))}", ctx, ctx_params(ctx)["table_ids"])

    patterns = [p_.replace("%", ".*").replace("_", ".?") for p in patterns if (p_ := p.strip())]
    pattern = re_compile("(" + "|".join(patterns) + ")", IGNORECASE)

    table_ids = table_ids or sorted(tables.keys())

    if show_columns:

        def on_match_print(table: int, row_number: int, columns: list[str]):
            print(
                *(f"table{table_id}/{row_number}/c{n}: {col}" for n, col in enumerate(columns, 1)), sep="\n", end="\n\n"
            )
    else:

        def on_match_print(table: int, row_number: int, columns: list[str]):
            print(f"table{table_id}/{row_number}")

    for table_id in table_ids:
        file: Path = tables[table_id]
        on_match = lambda r, cs: on_match_print(table_id, r, cs)

        with file.open("r") as fh:
            handler = ContentHandlerTableSearch(pattern, on_match, limit)
            try:
                sax_parse(fh, handler)
            except StopIteration:
                pass
