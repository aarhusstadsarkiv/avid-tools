from pathlib import Path

from click import BadParameter
from click import Choice
from click import command
from click import Context
from click import option
from click import pass_context

from avid_tools.database import create_database
from avid_tools.database import update_md5
from avid_tools.indices import generate_doc_index
from avid_tools.indices import generate_file_index
from avid_tools.utils import AVID
from avid_tools.utils import ctx_params
from avid_tools.utils import find_avid_dir
from avid_tools.utils import option_help
from avid_tools.utils import validate_xml


@command("finalize", no_args_is_help=True, add_help_option=False)
@option(
    "--update-hashes",
    type=Choice(["all", "index", "context", "tables", "documents", "none"]),
    default=(
        "index",
        "context",
    ),
    multiple=True,
    show_default=True,
    help="Vælg hvilke hashes skal opdateres.",
)
@option_help()
@pass_context
def cmd_finalize(ctx: Context, update_hashes: tuple[str, ...]):
    """
    Opdater md5 hashes og generer nye Indices/fileIndex.xml og Indices/docIndex.xml filer.

    archiveIndex.xml, contextDocumentationIndex.xml, tableIndex.xml bliver valideret.

    Som default, kun md5 hashes af index filer og kontekstdokumentation bliver opdateret. Men det kan ændres med
    --update-hashes option:

    \b
    * all: opdater hashes af alle filer
    * index: opdater hashes af indices
    * context: opdater hashes af kontekstdokumentation filerne
    * tables: opdater hashes af tabellerne
    * documents: opdater hashes af dokumenterne
    * none: ingen hash bliver opdateret
    """
    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    db_path: Path = avid.dir.joinpath("_metadata", "avid_tools.db")
    conn = create_database(db_path)
    update_hashes = ("index", "context", "tables", "documents") if "all" in update_hashes else update_hashes

    for index_file, schema in (
        (avid.indices.archiveIndex, avid.schemas.archiveIndex),
        (avid.indices.contextDocumentationIndex, avid.schemas.contextDocumentationIndex),
        (avid.indices.tableIndex, avid.schemas.tableIndex),
    ):
        if validation_error := validate_xml(index_file, schema):
            raise BadParameter(
                f"error in Indices/{index_file.name}, {validation_error.msg}",
                ctx,
                ctx_params(ctx)["avid_dir"],
            )

    if "index" in update_hashes:
        update_md5(conn, avid.indices.archiveIndex)
        update_md5(conn, avid.indices.contextDocumentationIndex)
        update_md5(conn, avid.indices.tableIndex)

    if "context" in update_hashes:
        for [context_doc_path] in conn.execute("select path from files where type = 'ContextDocumentation'"):
            update_md5(conn, avid.dir.joinpath(context_doc_path))

    if "tables" in update_hashes:
        for table_path in avid.tables.values():
            update_md5(conn, table_path)

    if "documents" in update_hashes:
        for [document_path] in conn.execute("select path from files where type = 'Documents'"):
            update_md5(conn, avid.dir.joinpath(document_path))

    generate_doc_index(conn, avid)
    update_md5(conn, avid.indices.docIndex)
    generate_file_index(conn, avid)
