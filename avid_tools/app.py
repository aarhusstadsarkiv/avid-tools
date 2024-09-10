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
from .database import insert_file
from .database import update_md5
from .indices import generate_doc_index
from .indices import generate_file_index
from .indices import read_context_documentation
from .indices import save_doc_index
from .indices import save_file_index
from .indices import write_context_documentation
from .utils import argument_avid_dir
from .utils import AVID
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


@app.group("context", no_args_is_help=True)
def grp_context(): ...


# noinspection HttpUrlsUsage,DuplicatedCode
@grp_context.command("add", no_args_is_help=True, short_help="Add a context document.")
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
@option("--position", metavar="INTEGER", type=IntRange(1), default=None, help="Position of the new context document.")
@pass_context
def cmd_context_add(ctx: Context, avid_dir: Path, file: Path, metadata: Path, position: int):
    """
    Add a context document to the archive in AVID_DIR.

    The context document FILE can be any file type as long as it is allowed (tiff, jp2, etc.).

    The METADATA file must be an XML document following the same schema as Indices/contextDocumentationIndex.xml, but
    with a single <document> tag. Any other tag is ignored.

    By default, the new context document is appended to the existing ones. If the --position option is used, the
    document will be added to that positon and the eixsting ones will be moved up.

    \b
    METADATA Example
    ----------------

    \b
    <?xml version="1.0" encoding="utf-8"?>
    <contextDocumentationIndex xsi:schemaLocation="http://www.sa.dk/xmlns/diark/1.0 ../Schemas/standard/contextDocumentationIndex.xsd"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.sa.dk/xmlns/diark/1.0">
        <document>...</document>
    </contextDocumentationIndex>
    """
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    avid = AVID(avid_dir)

    if validation_error := validate_xml(metadata, avid.schemas.contextDocumentationIndex):
        raise BadParameter(validation_error.message, ctx, ctx_params(ctx)["metadata"])

    try:
        new_context_doc = parse_xml(metadata.read_text())
        new_context_doc = new_context_doc["contextDocumentationIndex"]["document"]
        if isinstance(new_context_doc, list):
            new_context_doc = new_context_doc[0]
    except:
        raise BadParameter("Cannot parse metadata as XML", ctx, ctx_params(ctx)["metadata"])

    context_docs: dict[int, dict] = read_context_documentation(avid)
    new_context_doc_id: int = (len(context_docs) + 1) if not position else position
    new_context_doc_id = (len(context_docs) + 1) if new_context_doc_id > len(context_docs) else new_context_doc_id

    for doc_id in sorted([k for k in context_docs.keys() if k >= new_context_doc_id], reverse=True):
        path_str, doc_collection = conn.execute(
            "select path, docCollection from files where type = 'ContextDocumentation' and docId = ?",
            [doc_id],
        ).fetchone()
        path: Path = avid_dir.joinpath(path_str)
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
    insert_file(conn, avid_dir, new_context_doc_path.relative_to(avid_dir))

    context_docs = {(p + 1) if p >= new_context_doc_id else p: d for p, d in context_docs.items()}
    context_docs[new_context_doc_id] = new_context_doc

    write_context_documentation(avid, context_docs)

    update_md5(conn, avid.indices.contextDocumentationIndex)

    conn.commit()

    validate_xml(avid.indices.contextDocumentationIndex, avid.schemas.contextDocumentationIndex)


# noinspection HttpUrlsUsage,DuplicatedCode
@grp_context.command("update")
@argument_avid_dir(True)
@argument("DOC_ID", type=IntRange(1))
@option(
    "--file",
    type=ClickPath(exists=True, dir_okay=False, readable=True, resolve_path=True),
    default=None,
    callback=lambda _c, _p, v: Path(v),
)
@option(
    "--metadata",
    type=ClickPath(exists=True, dir_okay=False, readable=True, resolve_path=True),
    default=None,
    callback=lambda _c, _p, v: Path(v),
)
@pass_context
def cmd_context_update(ctx: Context, avid_dir: Path, doc_id: int, file: Path | None, metadata: Path | None):
    if not file and not metadata:
        return

    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    avid = AVID(avid_dir)

    if metadata:
        if validation_error := validate_xml(metadata, avid.schemas.contextDocumentationIndex):
            raise BadParameter(validation_error.message, ctx, ctx_params(ctx)["metadata"])

        try:
            new_context_doc = parse_xml(metadata.read_text())
            new_context_doc = new_context_doc["contextDocumentationIndex"]["document"]
            if isinstance(new_context_doc, list):
                new_context_doc = new_context_doc[0]
        except:
            raise BadParameter("Cannot parse metadata as XML", ctx, ctx_params(ctx)["metadata"])

        context_docs: dict[int, dict] = read_context_documentation(avid)
        context_docs[doc_id] = new_context_doc
        write_context_documentation(avid, context_docs)
        update_md5(conn, avid.indices.contextDocumentationIndex)

    if file:
        path_str: str = conn.execute(
            "select path from files where type = 'ContextDocumentation' and docId = ?",
            [doc_id],
        ).fetchone()[0]
        copy2(file, path := avid_dir.joinpath(path_str))
        update_md5(conn, path)


@app.command("finalize", no_args_is_help=True)
@argument_avid_dir(True)
def cmd_finalize(avid_dir: Path):
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    avid = AVID(avid_dir)
    generate_doc_index(conn, avid)
    generate_file_index(conn, avid)
