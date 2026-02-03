from pathlib import Path

from click import argument
from click import BadParameter
from click import command
from click import Context
from click import pass_context
from click import Path as ClickPath

from avid_tools.database import create_database
from avid_tools.indices import save_doc_index
from avid_tools.indices import save_file_index
from avid_tools.utils import AVID
from avid_tools.utils import ctx_params
from avid_tools.utils import option_help
from avid_tools.utils import validate_xml


@command("init", no_args_is_help=True, add_help_option=False)
@argument(
    "AVID_DIR",
    type=ClickPath(exists=True, file_okay=False, writable=True, readable=True, resolve_path=True),
    required=True,
    callback=lambda _c, _p, v: Path(v),
)
@option_help()
@pass_context
def cmd_init(ctx: Context, avid_dir: Path):
    """
    Initializer en ny AVID mappe med værktøjets database.

    AVID_DIR argument skal være stien til hoved mappen af en arkiversingsversion (hvor Indices, Tables, osv. ligger).
    Hvis programmet kører i hoved mappen, kan man brug "." som sti.
    """
    avid: AVID = AVID(avid_dir)
    db_path: Path = avid.dir.joinpath("_metadata", "avid_tools.db")

    if db_path.is_file():
        raise BadParameter(f"_metadata/avid_tools.db already exists for {avid_dir.name}.", ctx, ctx_params(ctx)["avid_dir"])

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

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = create_database(db_path)
    save_file_index(conn, avid)
    save_doc_index(conn, avid)
