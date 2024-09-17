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

from avid_tools.utils import AVID
from avid_tools.utils import ctx_params
from avid_tools.utils import find_avid_dir


class ContentHandlerTableSearch(ContentHandler):
    def __init__(
        self,
        regexp: Pattern[str],
        on_match: Callable[[int, dict[int, str]], None],
        limit: int | None = None,
        column_ids: list[int] | None = None,
    ):
        super().__init__()
        self.regexp: Pattern[str] = regexp
        self.on_match: Callable[[int, dict[int, str]], None] = on_match
        self.limit: int | None = limit
        self.column_ids: list[int] | None = column_ids
        self.is_row: bool = False
        self.row_number: int = 0
        self.column_id: int | None = None
        self.row_columns: dict[int, str] = {}
        self.matches: int = 0

    def startElement(self, name: str, attrs: AttributesImpl):
        if name == "row":
            self.is_row = True
            self.row_number += 1
        elif self.is_row and name[0] == "c":
            column_id: int = int(name[1:])
            if not self.column_ids or column_id in self.column_ids:
                self.column_id = column_id
                self.row_columns[column_id] = ""

    def characters(self, content: str):
        if self.column_id is not None:
            self.row_columns[self.column_id] += content

    def endElement(self, name: str):
        if name == "row":
            if any(self.regexp.search(c) for c in self.row_columns.values()):
                self.on_match(self.row_number, self.row_columns)
                self.matches += 1
                if self.limit and self.matches >= self.limit:
                    raise StopIteration
            self.is_row = False
            self.row_columns = {}
        elif self.column_id is not None and name[0] == "c":
            self.column_id = None


@command("search", no_args_is_help=True, short_help="Søg i tabellerne.")
@argument("patterns", metavar="PATTERN...", nargs=-1, required=True)
@option("--table", "-t", "table_ids", metavar="ID", type=IntRange(min=1), multiple=True, help="Vælg søgetabeller.")
@option(
    "--column",
    "-c",
    "columns",
    metavar="TABLE_ID COLUMN_ID",
    type=(IntRange(1), IntRange(1)),
    multiple=True,
    help="Vælg søgekolonner i tabeller.",
)
@option("--limit", metavar="INTEGER", type=IntRange(1), default=None, help="Begræns hvor mange resultater vises.")
@option(
    "--show-columns/--show-rows",
    "show_columns",
    is_flag=True,
    default=True,
    help="Vis alle kolonner i matchende rækker eller kun rækkenumre.",
)
@pass_context
def cmd_search(
    ctx: Context,
    patterns: tuple[str, ...],
    table_ids: tuple[int, ...],
    columns: tuple[tuple[int, int], ...],
    limit: int | None,
    show_columns: bool,
):
    """
    Søg PATTERN i tabel rækker i Tables.

    PATTERN skal være i SQL LIKE format (% til nul eller flere bogstaver og _ til nul eller et bogstav). Flere
    PATTERN kan bruges og matches med "eller" logik (dvs. PATTERN et, eller PATTERN to, eller PATTERN tre, osv.).

    Som default søges PATTERN'er i alle tabeller og kolonner.
    --table kan bruges for at begrænse søgning til bestemte tabeller.
    --column kan bruges for at begrænse søgning til bestemte kolloner i bestemte tabeller.
    Begge --table og --column kan bruges.
    """
    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    tables = avid.tables

    if invalid_ids := [i for i in table_ids if i not in tables]:
        raise BadParameter(f"no tables with ID {', '.join(map(str, invalid_ids))}", ctx, ctx_params(ctx)["table_ids"])
    if invalid_ids := [i for i, _ in columns if i not in tables]:
        raise BadParameter(f"no tables with ID {', '.join(map(str, invalid_ids))}", ctx, ctx_params(ctx)["columns"])

    patterns = [p_.replace("%", ".*").replace("_", ".?") for p in patterns if (p_ := p.strip())]
    pattern = re_compile("(" + "|".join(patterns) + ")", IGNORECASE)

    targets: dict[int, list[int] | None] = {}

    for table_id in table_ids:
        targets[table_id] = None
    for [table_id, column_id] in columns:
        targets[table_id] = targets.get(table_id) or []
        targets[table_id].append(column_id)

    targets = targets or {i: None for i in sorted(tables.keys())}

    if show_columns:

        def on_match_print(_table: int, _row_number: int, _columns: dict[int, str]):
            print(
                *(f"table{_table}/row{_row_number}/c{n}: {col}" for n, col in _columns.items()),
                sep="\n",
                end="\n\n",
            )
    else:

        def on_match_print(_table: int, _row_number: int, _columns: dict[int, str]):
            print(f"table{_table}/row{_row_number}")

    for table_id, column_ids in targets.items():
        file: Path = tables[table_id]
        on_match = lambda r, cs: on_match_print(table_id, r, cs)

        with file.open("r") as fh:
            handler = ContentHandlerTableSearch(pattern, on_match, limit, column_ids)
            try:
                sax_parse(fh, handler)
            except StopIteration:
                pass
