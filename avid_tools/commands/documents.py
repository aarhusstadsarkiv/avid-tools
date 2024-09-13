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
from avid_tools.utils import argument_avid_dir


@group("documents", no_args_is_help=True)
def grp_documents(): ...


@grp_documents.command("extensions", no_args_is_help=True)
@argument_avid_dir(True)
@option("--limit", type=IntRange(1), default=None)
@option("--reverse", is_flag=True, default=False)
@option("--csv-file", type=ClickPath(dir_okay=False, writable=True), callback=lambda _c, _p, v: Path(v) if v else None)
@pass_context
def cmd_documents_extensions(_ctx: Context, avid_dir: Path, limit: int | None, reverse: bool, csv_file: Path | None):
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    file: TextIO = csv_file.open("w", encoding="utf-8") if csv_file else stdout
    writer = csv_writer(file, delimiter="," if csv_file else "\t")

    writer.writerow(["ext", "count", "firstDocId"])

    for [ext, count, doc_id] in conn.execute(
        f"select * from originalExtensionCount order by count {'asc' if reverse else 'desc'} limit {limit or -1}"
    ):
        writer.writerow([ext, count, doc_id])

    file.close()


@grp_documents.command("checksums", no_args_is_help=True)
@argument_avid_dir(True)
@option("--limit", type=IntRange(1), default=None)
@option("--reverse", is_flag=True, default=False)
@option("--csv-file", type=ClickPath(dir_okay=False, writable=True), callback=lambda _c, _p, v: Path(v) if v else None)
@pass_context
def cmd_documents_extensions(_ctx: Context, avid_dir: Path, limit: int | None, reverse: bool, csv_file: Path | None):
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    file: TextIO = csv_file.open("w", encoding="utf-8") if csv_file else stdout
    writer = csv_writer(file, delimiter="," if csv_file else "\t")

    writer.writerow(["md5", "count", "firstDocId"])

    for [md5, count, doc_id] in conn.execute(
        f"select * from md5Count order by count {'asc' if reverse else 'desc'} limit {limit or -1}"
    ):
        writer.writerow([md5, count, doc_id])

    file.close()
