from pathlib import Path
from shutil import copy2

from click import argument
from click import BadParameter
from click import Choice
from click import Context
from click import group
from click import option
from click import pass_context
from click import Path as ClickPath
from xmltodict import parse as parse_xml

from avid_tools.database import create_database
from avid_tools.database import update_md5
from avid_tools.utils import AVID
from avid_tools.utils import ctx_params
from avid_tools.utils import find_avid_dir
from avid_tools.utils import option_help
from avid_tools.utils import validate_xml


@group("index", no_args_is_help=True, add_help_option=False)
@option_help()
def grp_index():
    """Vis og opdater indeks filer i Indices."""


@grp_index.command("view", no_args_is_help=True, add_help_option=False)
@argument(
    "index",
    type=Choice(["archiveIndex", "contextDocumentationIndex", "tableIndex"], case_sensitive=False),
    nargs=-1,
    required=True,
)
@option_help()
def cmd_index_view(index: tuple[str, ...]):
    """Vis en eller flere indeks filer."""

    def printer(obj: dict | list, indent: int = 0):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    print("    " * indent, f"{k}:", sep="")
                    printer(v, indent + 1)
                else:
                    print("    " * indent, f"{k}: {v}", sep="")
        elif isinstance(obj, list):
            for n, v in enumerate(obj, 1):
                if isinstance(v, (dict, list)):
                    print("    " * indent, f"{n}:", sep="")
                    printer(v, indent + 1)
                else:
                    print("    " * indent, f"{n}: {v}", sep="")

    avid: AVID = AVID(find_avid_dir(Path.cwd()))

    for index_type in index:
        if index_type == "archiveIndex":
            xml = parse_xml(avid.indices.archiveIndex.read_text(encoding="utf-8"), encoding="utf-8")
        elif index_type == "contextDocumentationIndex":
            xml = parse_xml(avid.indices.contextDocumentationIndex.read_text(encoding="utf-8"), encoding="utf-8")
        elif index_type == "tableIndex":
            xml = parse_xml(avid.indices.tableIndex.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            continue
        printer(xml)


@grp_index.command("update", no_args_is_help=True, add_help_option=False)
@argument(
    "index_file",
    type=ClickPath(exists=True, dir_okay=False, readable=True),
    nargs=1,
    required=True,
    callback=lambda _c, _p, v: Path(v),
)
@option(
    "--type",
    "index_type",
    type=Choice(["archiveIndex", "contextDocumentationIndex", "tableIndex"], case_sensitive=False),
    default=None,
    required=False,
    help="Indeks type.",
)
@option_help()
@pass_context
def cmd_index_update(ctx: Context, index_file: Path, index_type: str | None):
    """
    Opdater en indeks file.

    Indekstype genkendes automatisk fra navnet af INDEX_FILE, men det kan overrides med --type option.
    """
    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    db_path: Path = avid.dir.joinpath("_metadata", "avid_tools.db")
    conn = create_database(db_path)

    if index_file.name in ["archiveIndex.xml", "contextDocumentationIndex.xml", "tableIndex.xml"] and not index_type:
        index_type = index_file.with_suffix("").name
    elif not index_type:
        raise BadParameter(
            f"cannot recognize index type from file {index_type}",
            ctx,
            ctx_params(ctx)["index"],
            "Must be one of archiveIndex.xml, contextDocumentationIndex.xml, tableIndex.xml",
        )

    if index_type == "archiveIndex":
        schema, target = avid.schemas.archiveIndex, avid.indices.archiveIndex
    elif index_type == "contextDocumentationIndex":
        schema, target = avid.schemas.contextDocumentationIndex, avid.indices.contextDocumentationIndex
    elif index_type == "tableIndex":
        schema, target = avid.schemas.archiveIndex, avid.indices.archiveIndex
    else:
        raise BadParameter(f"unknown index type {index_type}", ctx, ctx_params(ctx)["index_type"])

    if validation_error := validate_xml(index_file, schema):
        raise BadParameter(validation_error.msg, ctx, ctx_params(ctx)["index"])

    if index_file != target:
        copy2(index_file, target)

    update_md5(conn, target)
    conn.commit()
