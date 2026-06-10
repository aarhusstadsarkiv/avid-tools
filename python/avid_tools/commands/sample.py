from math import ceil
from pathlib import Path
from shutil import copy2
from sqlite3 import Connection
from sys import stderr

from click import argument
from click import group
from click import IntRange
from click import option
from click import Path as ClickPath

from avid_tools.database import create_database
from avid_tools.utils import AVID
from avid_tools.utils import find_avid_dir
from avid_tools.utils import option_help


def sample(
    avid: AVID,
    conn: Connection,
    bin_col: str,
    sample_size: int,
    extensions: tuple[str, ...],
    output_dir: Path,
    where: list[str],
    aggregate: list[str] | None = None,
):
    extensions = tuple(filter(bool, (e.strip() for e in extensions)))

    if not extensions or "all" in extensions:
        extensions = (
            *(e for e in extensions if e not in ("all", "all-valid", "all-invalid")),
            *(
                f[0]
                for f in conn.execute(
                    "select distinct originalExtension from files"
                    " where type = 'Documents' and originalExtension is not null and docId is not null"
                )
            ),
        )
    elif "all-valid" in extensions:
        extensions = (
            *(e for e in extensions if e not in ("all", "all-valid", "all-invalid")),
            *(
                f[0]
                for f in conn.execute(
                    "select distinct originalExtension from files"
                    " where type = 'Documents' and originalExtension is not null and originalExtension != '' and docId is not null"
                )
            ),
        )
    elif "all-invalid" in extensions:
        extensions = (
            *(e for e in extensions if e not in ("all", "all-valid", "all-invalid")),
            "",
        )
    extensions = tuple(sorted({e.lower() for e in extensions}))
    sample_lower_limit, sample_higher_limit = ceil(sample_size / 2), sample_size // 2
    sorting_index: int = 1
    if bin_col == "docId":
        sorting_index = 3

    for extension in extensions:
        where_stmt: str = " and ".join([*where, "lower(originalExtension) = ?"])
        aggregate_stmt: str = (" having " + " and ".join(aggregate)) if aggregate is not None else ""
        files: list[tuple[str, int, str, int]] = [
            *conn.execute(
                "select min(path), min(size), min(originalName), min(docId) from files"
                f" where {where_stmt} group by md5 {aggregate_stmt} order by min({bin_col}) limit {sample_lower_limit}",
                [extension],
            ),
            *conn.execute(
                "select min(path), min(size), min(originalName), min(docId) from files"
                f" where {where_stmt} group by md5 {aggregate_stmt} order by min({bin_col}) desc limit {sample_higher_limit}",
                [extension],
            ),
        ]
        files = sorted(set(files), key=lambda f: f[sorting_index])

        print(extension or "<tom>")

        if not files:
            print("+--- ingen filer fundet")

        for n, [path_str, size, original_name, doc_id] in enumerate(files, 1):
            prefix: str = ""
            if bin_col == "size":
                prefix = f"{size}-"
            file_path: Path = avid.dir.joinpath(path_str)
            copy_path: Path = output_dir.joinpath(
                extension or "_invalid",
                f"{prefix}{doc_id}-{original_name}{file_path.suffix}",
            )
            print(f"{'+' if n == len(files) else '|'}---", copy_path.name)
            copy_path.parent.mkdir(parents=True, exist_ok=True)
            copy2(file_path, copy_path)

        print()


@group("sample", no_args_is_help=True, add_help_option=False)
@option_help()
def grp_sample():
    """Tag en prøve af dokumenter."""


@grp_sample.command("size", no_args_is_help=True, add_help_option=False)
@argument("extensions", metavar="EXTENSIONS...", nargs=-1, required=True)
@option(
    "--sample-size",
    metavar="INTEGER",
    type=IntRange(min=1),
    default=5,
    show_default=True,
    help="Antallet af filer i prøven.",
)
@option("--min-size", metavar="INTEGER", type=IntRange(min=1), default=None, help="Min filstørrelse i prøven.")
@option("--max-size", metavar="INTEGER", type=IntRange(min=1), default=None, help="Max filstørrelse i prøven.")
@option(
    "--output-dir",
    type=ClickPath(file_okay=False, writable=True, resolve_path=True),
    default=None,
    callback=lambda _c, _p, v: Path(v) if v else None,
    help="Mappen hvor prøven skal ligge.",
)
@option_help()
def cmd_sample_size(
    extensions: tuple[str, ...],
    sample_size: int,
    min_size: int | None,
    max_size: int | None,
    output_dir: Path | None,
):
    """
    Tag en prøve af dokumenterne baseret på det originale filtypenavn og størrelsen.

    Der tages en prøve af hver filtype, sorteret efter størrelsen. En halvdel af prøven indeholder filer med de laveste
    størrelser, og den anden del indeholder filer med de højeste.

    Prøven begrænses til de originale filtyper i EXTENSION argumenter. For at tage en prøve af alle filtyper brug
    "all" som argument. For at tage en prøve af valide filtyper alene brug "all-valid" som argument. For at tage en
    prøve af ikke valide filtyper brug "all-invalid" som argument.

    Som default bruges mappen _metadata/sample_size for at gemme prøven. Det kan overrides med --output-dir option.
    """
    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    db_path: Path = avid.dir.joinpath("_metadata", "avid_tools.db")
    conn = create_database(db_path)

    if not output_dir:
        print(
            "No output directory specified, using",
            (output_dir := avid.dir.joinpath("_metadata", "sample_size")).relative_to(avid.dir.parent),
            file=stderr,
            end="\n\n",
        )

    where: list[str] = ["type = 'Documents'", "docId is not null"]
    aggregate: list[str] = []

    if min_size:
        aggregate.append(f"min(size) >= {min_size}")
    if max_size:
        aggregate.append(f"min(size) <= {max_size}")

    sample(avid, conn, "size", sample_size, extensions, output_dir, where, aggregate)


@grp_sample.command("docid", no_args_is_help=True, add_help_option=False)
@argument("extensions", metavar="EXTENSIONS...", nargs=-1, required=True)
@option(
    "--sample-size",
    metavar="INTEGER",
    type=IntRange(min=1),
    default=5,
    show_default=True,
    help="Antallet af filer i prøven.",
)
@option("--min-docid", metavar="INTEGER", type=IntRange(min=1), default=None, help="Min docId i prøven.")
@option("--max-docid", metavar="INTEGER", type=IntRange(min=1), default=None, help="Max docId i prøven.")
@option(
    "--output-dir",
    type=ClickPath(file_okay=False, writable=True, resolve_path=True),
    default=None,
    callback=lambda _c, _p, v: Path(v) if v else None,
)
@option_help()
def cmd_sample_docid(
    extensions: tuple[str, ...],
    sample_size: int,
    min_docid: int | None,
    max_docid: int | None,
    output_dir: Path | None,
):
    """
    Tag en prøve af dokumenterne baseret på det originale filtypenavn og docId'en.

    Der tages en prøve af hver filtype, sorteret efter docID. En halvdel af prøven indeholder filer med de laveste
    docId'er, og den anden del indeholder filer med de højeste.

    Prøven begrænses til de originale filtyper i EXTENSION argumenter. For at tage en prøve af alle filtyper brug
    "all" som argument. For at tage en prøve af valide filtyper alene brug "all-valid" som argument. For at tage en
    prøve af ikke valide filtyper brug "all-invalid" som argument.

    Som default bruges mappen _metadata/sample_docid for at gemme prøven. Det kan overrides med --output-dir option.
    """
    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    db_path: Path = avid.dir.joinpath("_metadata", "avid_tools.db")
    conn = create_database(db_path)

    if not output_dir:
        print(
            "No output directory specified, using",
            (output_dir := avid.dir.joinpath("_metadata", "sample_docid")).relative_to(avid.dir.parent),
            file=stderr,
            end="\n\n",
        )

    where: list[str] = ["type = 'Documents'", "docId is not null"]

    if min_docid:
        where.append(f"min(docId) >= {min_docid}")
    if max_docid:
        where.append(f"min(docId) <= {min_docid}")

    sample(avid, conn, "docId", sample_size, extensions, output_dir, where)
