from pathlib import Path
from shutil import copy2

from click import argument
from click import BadParameter
from click import Context
from click import group
from click import IntRange
from click import option
from click import pass_context
from click import Path as ClickPath
from click import version_option
from xmltodict import parse as parse_xml

from .__version__ import __version__
from .database import create_database
from .indices import insert_file
from .indices import read_context_documentation
from .indices import save_doc_index
from .indices import save_file_index
from .indices import write_context_documentation
from .utils import argument_avid_dir
from .utils import ctx_params
from .utils import validate_xml


@group("avid-tools", no_args_is_help=True)
@version_option(__version__)
def app(): ...


@app.command("init", no_args_is_help=True)
@argument_avid_dir(False)
@pass_context
def cmd_init(ctx: Context, avid_dir: Path):
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
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
    save_file_index(avid_dir, conn)
    save_doc_index(avid_dir, conn)


@app.group("context", no_args_is_help=True)
def grp_context(): ...


@grp_context.command("add", no_args_is_help=True)
@argument_avid_dir(True)
@argument(
    "file",
    type=ClickPath(exists=True, dir_okay=False, readable=True, resolve_path=True),
    callback=lambda _c, _p, v: Path(v),
)
@argument(
    "metadata",
    type=ClickPath(exists=True, dir_okay=False, readable=True, resolve_path=True),
    callback=lambda _c, _p, v: Path(v),
)
@option("--position", type=IntRange(1), default=None)
@pass_context
def cmd_context_add(ctx: Context, avid_dir: Path, file: Path, metadata: Path, position: int):
    if validation_error := validate_xml(
        metadata,
        avid_dir.joinpath("Schemas", "standard", "contextDocumentationIndex.xsd"),
    ):
        raise BadParameter(validation_error.message, ctx, ctx_params(ctx)["metadata"])

    try:
        new_context_doc = parse_xml(metadata.read_text())
    except:
        raise BadParameter("Cannot parse metadata as XML", ctx, ctx_params(ctx)["metadata"])

    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)

    context_docs: dict[int, dict] = read_context_documentation(avid_dir)
    new_context_doc_id: int = (len(context_docs) + 1) if not position else position

    for doc_id in sorted([k for k in context_docs.keys() if k >= new_context_doc_id], reverse=True):
        path_str, doc_collection = conn.execute(
            "select path, docCollection from files where type = 'ContextDocumentation' and docId = ?",
            [doc_id],
        ).fetchone()
        path: Path = Path(path_str)
        new_doc_id: int = doc_id + 1
        new_path: Path = avid_dir.joinpath(
            "ContextDocumentation",
            f"docCollection{doc_collection}",
            str(new_doc_id),
            path.name,
        )
        new_path.parent.mkdir(parents=True, exist_ok=True)
        path.rename(new_path)
        conn.execute(
            "update files set path = ?, docId = ? where path = ?",
            [str(new_path.relative_to(avid_dir)), new_doc_id, path_str],
        )
        conn.commit()

    new_context_doc_path = avid_dir.joinpath(
        "ContextDocumentation",
        f"docCollection1",
        str(new_context_doc_id),
        f"1{file.suffix}",
    )
    new_context_doc_path.parent.mkdir(parents=True, exist_ok=True)
    copy2(file, new_context_doc_path)
    insert_file(conn, avid_dir, new_context_doc_path)

    context_docs = {(p + 1) if p >= new_context_doc_id else p: d for p, d in context_docs.items()}
    context_docs[new_context_doc_id] = new_context_doc

    write_context_documentation(avid_dir, context_docs)

    conn.commit()
