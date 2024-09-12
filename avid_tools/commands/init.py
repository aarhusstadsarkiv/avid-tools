from pathlib import Path

from click import BadParameter
from click import command
from click import Context
from click import pass_context

from avid_tools.database import create_database
from avid_tools.indices import save_doc_index
from avid_tools.indices import save_file_index
from avid_tools.utils import argument_avid_dir
from avid_tools.utils import AVID
from avid_tools.utils import ctx_params
from avid_tools.utils import validate_xml


@command("init", no_args_is_help=True)
@argument_avid_dir(False)
@pass_context
def cmd_init(ctx: Context, avid_dir: Path):
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    avid = AVID(avid_dir)

    if db_path.is_file():
        raise BadParameter(f"_metadata/avid.db already exists for {avid_dir.name}.", ctx, ctx_params(ctx)["avid_dir"])

    db_path.parent.mkdir(parents=True, exist_ok=True)

    for index_file in (
        avid.indices.archiveIndex,
        avid.indices.contextDocumentationIndex,
        avid.indices.docIndex,
        avid.indices.fileIndex,
        avid.indices.tableIndex,
    ):
        if not index_file.is_file():
            raise BadParameter(f"missing Indices/{index_file.name}", ctx, ctx_params(ctx)["avid_dir"])

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

    conn = create_database(db_path)
    save_file_index(conn, avid)
    save_doc_index(conn, avid)
