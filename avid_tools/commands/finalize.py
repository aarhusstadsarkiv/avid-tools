import logging

from pathlib import Path

from click import Choice
from click import command
from click import Context
from click import option
from click import pass_context
from tqdm import tqdm

from avid_tools.database import create_database
from avid_tools.database import update_md5
from avid_tools.indices import generate_doc_index
from avid_tools.indices import generate_file_index
from avid_tools.utils import AVID
from avid_tools.utils import find_avid_dir
from avid_tools.utils import option_help
from avid_tools.utils import validate_archive_xmls


logger = logging.getLogger(__file__)


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
@option("--skip-validate", is_flag=True, default=False)
@option_help()
@pass_context
def cmd_finalize(ctx: Context, update_hashes: tuple[str, ...], skip_validate: bool):
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

    logger.info("Perform XML validation" if not skip_validate else "Skip XML validation")
    if not skip_validate:
        validate_archive_xmls(avid, ctx)

    logger.info(f"Update hashes for '{', '.join(update_hashes)}'")

    with conn:
        if "index" in update_hashes:
            update_md5(conn, avid.indices.archiveIndex)
            update_md5(conn, avid.indices.contextDocumentationIndex)
            update_md5(conn, avid.indices.tableIndex)

        if "context" in update_hashes:
            for [context_doc_path] in tqdm(conn.execute("select path from files where type = 'ContextDocumentation'")):
                update_md5(conn, avid.dir.joinpath(context_doc_path))

        if "tables" in update_hashes:
            for table_path in tqdm(avid.tables.values()):
                update_md5(conn, table_path)
        
        if "documents" in update_hashes:
            for [document_path] in tqdm(conn.execute("select path from files where type = 'Documents'"), unit="doc"):
                update_md5(conn, document_path, avid.dir)

    with conn:
        generate_doc_index(conn, avid)
        update_md5(conn, avid.indices.docIndex.relative_to(avid.dir), avid.dir)
        generate_file_index(conn, avid)

    logger.info("Done!")
