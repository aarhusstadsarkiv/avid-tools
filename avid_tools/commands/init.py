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


@command("init", no_args_is_help=True)
@argument_avid_dir(False)
@pass_context
def cmd_init(ctx: Context, avid_dir: Path):
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")

    if db_path.is_file():
        raise BadParameter(f"_metadata/avid.db already exists for {avid_dir.name}.", ctx, ctx_params(ctx)["avid_dir"])

    db_path.parent.mkdir(parents=True, exist_ok=True)

    for index_file in (
        "archiveIndex.xml",
        "contextDocumentationIndex.xml",
        "docIndex.xml",
        "fileIndex.xml",
        "tableIndex.xml",
    ):
        if not avid_dir.joinpath("Indices", index_file).is_file():
            raise BadParameter(f"Missing Indices/{index_file}", ctx, ctx_params(ctx)["avid_dir"])

    conn = create_database(db_path)
    avid = AVID(avid_dir)
    save_file_index(conn, avid)
    save_doc_index(conn, avid)
