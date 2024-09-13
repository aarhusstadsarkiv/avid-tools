from pathlib import Path

from click import BadParameter
from click import command
from click import Context
from click import pass_context

from avid_tools.database import create_database
from avid_tools.database import update_md5
from avid_tools.indices import generate_doc_index
from avid_tools.indices import generate_file_index
from avid_tools.utils import argument_avid_dir
from avid_tools.utils import AVID
from avid_tools.utils import ctx_params
from avid_tools.utils import validate_xml


@command("finalize", no_args_is_help=True)
@argument_avid_dir(True)
@pass_context
def cmd_finalize(ctx: Context, avid_dir: Path):
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    avid = AVID(avid_dir)

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
        update_md5(conn, index_file)

    for context_doc_path in conn.execute("select path from files where type = 'ContextDocumentation'"):
        update_md5(conn, avid.dir.joinpath(context_doc_path))

    for table_path in avid.tables.values():
        update_md5(conn, table_path)

    generate_doc_index(conn, avid)
    update_md5(conn, avid.indices.docIndex)
    generate_file_index(conn, avid)
