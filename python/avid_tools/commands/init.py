from pathlib import Path

from click import argument
from click import BadParameter
from click import command
from click import Context
from click import pass_context
from click import Path as ClickPath
from click import option

from avid_tools.database import create_database
from avid_tools.indices import save_doc_index
from avid_tools.indices import save_file_index
from avid_tools.utils import AVID, validate_archive_xmls
from avid_tools.utils import ctx_params
from avid_tools.utils import option_help


@command("init", add_help_option=False)
@argument(
    "AVID_DIR",
    type=ClickPath(exists=True, file_okay=False, writable=True, readable=True, resolve_path=True),
    required=True,
    callback=lambda _c, _p, v: Path(v),
)
@option("--skip-validate", is_flag=True, default=False)
@option_help()
@pass_context
def cmd_init(ctx: Context, avid_dir: Path, skip_validate: bool):
    """
    Initializer en ny AVID mappe med værktøjets database.

    AVID_DIR argument skal være stien til hoved mappen af en arkiversingsversion (hvor Indices, Tables, osv. ligger).
    Hvis programmet kører i hoved mappen, kan man brug "." som sti.
    """
    avid: AVID = AVID(avid_dir)
    db_path: Path = avid.dir.joinpath("_metadata", "avid_tools.db")

    missing_indices: list[Path] = []

    for index_file in (
        avid.indices.archiveIndex,
        avid.indices.contextDocumentationIndex,
        avid.indices.docIndex,
        avid.indices.fileIndex,
        avid.indices.tableIndex,
    ):
        if not index_file.is_file():
            missing_indices.append(index_file)

    if missing_indices:
        raise BadParameter(
            f"missing {', '.join(str(i.relative_to(avid_dir)) for i in missing_indices)}.",
            ctx,
            ctx_params(ctx)["avid_dir"],
        )

    if not skip_validate:
        validate_archive_xmls(avid, ctx)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = create_database(db_path)
    save_file_index(conn, avid)
    save_doc_index(conn, avid)
