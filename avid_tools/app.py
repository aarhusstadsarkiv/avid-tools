from pathlib import Path

from click import BadParameter
from click import Context
from click import group
from click import pass_context
from click import version_option

from .__version__ import __version__
from .context.context import grp_context
from .database import create_database
from .indices import generate_doc_index
from .indices import generate_file_index
from .indices import save_doc_index
from .indices import save_file_index
from .utils import argument_avid_dir
from .utils import AVID
from .utils import ctx_params


@group("avid-tools", no_args_is_help=True)
@version_option(__version__)
def app(): ...


@app.command("init", no_args_is_help=True)
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


@app.command("finalize", no_args_is_help=True)
@argument_avid_dir(True)
def cmd_finalize(avid_dir: Path):
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    avid = AVID(avid_dir)
    generate_doc_index(conn, avid)
    generate_file_index(conn, avid)


app.add_command(grp_context, grp_context.name)
app.add_command(grp_context, grp_context.name)
