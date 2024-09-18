from csv import writer as csv_writer
from pathlib import Path
from sys import stdout
from typing import TextIO

from click import Context
from click import group
from click import IntRange
from click import option
from click import pass_context
from click import Path as ClickPath

from avid_tools.database import create_database
from avid_tools.utils import AVID
from avid_tools.utils import find_avid_dir
from avid_tools.utils import option_help


@group("documents", no_args_is_help=True, add_help_option=False)
@option_help()
def grp_documents():
    """Vis oversigter af dokumenterne i arkiveringsverionen."""


# noinspection DuplicatedCode
@grp_documents.command(
    "extensions",
    no_args_is_help=True,
    add_help_option=False,
    short_help="Vis antallet af filtypenavner.",
)
@option("--limit", type=IntRange(1), default=None, help="Begræns hvor mange resultater vises.")
@option("--reverse", is_flag=True, default=False, help="Vis i stigende rækkefølge.")
@option(
    "--csv-file",
    type=ClickPath(dir_okay=False, writable=True),
    callback=lambda _c, _p, v: Path(v) if v else None,
    help="Gem output til en CSV fil.",
)
@option_help()
@pass_context
def cmd_documents_extensions(_ctx: Context, limit: int | None, reverse: bool, csv_file: Path | None):
    """
    Vis antallet af filtypenavner.

    \b
    Der vises fire kolloner:
    * ext: filetypen
    * count: antallet af filer med filetypen
    * unique: antallet af unikke md5 hashes med filetypen
    * firstDocId: først docId med filetypen

    Brug --limit option for at begrænse hvor mange filtyper vises. Filetypenavner vises i faldende rækkefølge som
    default, for at vise dem i stigende rækkefølge brug --reverse option.

    Resultaterne kan gemmes til en CSV fil ved at brug --csv-file option. --limit og --reverse kan bruges med CSV fil
    også.
    """
    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    db_path: Path = avid.dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    file: TextIO = csv_file.open("w", encoding="utf-8") if csv_file else stdout
    writer = csv_writer(file, delimiter="," if csv_file else "\t")

    writer.writerow(["ext", "count", "unique", "firstDocId"])

    for row in conn.execute(
        f"select originalExtension, count, distinctCount, firstDocId from originalExtensionCount order by count {'asc' if reverse else 'desc'} limit {limit or -1}"
    ):
        writer.writerow(row)

    file.close()


# noinspection DuplicatedCode
@grp_documents.command(
    "checksums",
    no_args_is_help=True,
    add_help_option=False,
    short_help="Vis antallet af md5 hashes.",
)
@option("--limit", type=IntRange(1), default=None, help="Begræns hvor mange resultater vises.")
@option("--reverse", is_flag=True, default=False, help="Vis i stigende rækkefølge.")
@option(
    "--csv-file",
    type=ClickPath(dir_okay=False, writable=True),
    callback=lambda _c, _p, v: Path(v) if v else None,
    help="Gem output til en CSV fil.",
)
@option_help()
@pass_context
def cmd_documents_checksums(_ctx: Context, limit: int | None, reverse: bool, csv_file: Path | None):
    """
    Vis antallet af md5 hashes.

    \b
    Der vises fire kolloner:
    * md5: hash
    * count: antallet af filer med hash
    * firstDocId: først docId med hash

    Brug --limit option for at begrænse hvor mange hasher vises. Hasher vises i faldende rækkefølge som default, for at
    vise dem i stigende rækkefølge, brug --reverse option.

    Resultaterne kan gemmes til en CSV fil ved at brug --csv-file option. --limit og --reverse kan bruges med CSV fil
    også.
    """
    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    db_path: Path = avid.dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    file: TextIO = csv_file.open("w", encoding="utf-8") if csv_file else stdout
    writer = csv_writer(file, delimiter="," if csv_file else "\t")

    writer.writerow(["md5", "count", "firstDocId"])

    for [md5, count, doc_id] in conn.execute(
        f"select * from md5Count order by count {'asc' if reverse else 'desc'} limit {limit or -1}"
    ):
        writer.writerow([md5, count, doc_id])

    file.close()
