from copy import deepcopy
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
from xmltodict import parse as parse_xml

from avid_tools.database import create_database
from avid_tools.database import insert_file
from avid_tools.database import update_md5
from avid_tools.indices import read_context_documentation
from avid_tools.indices import write_context_documentation
from avid_tools.utils import argument_avid_dir
from avid_tools.utils import AVID
from avid_tools.utils import ctx_params
from avid_tools.utils import remove_empty_dir
from avid_tools.utils import validate_xml


@group("context", no_args_is_help=True)
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
@grp_context.command("update", no_args_is_help=True)
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


@grp_context.command("move", no_args_is_help=True)
@argument_avid_dir(True)
@argument("FROM_DOC_ID", type=IntRange(1))
@argument("TO_DOC_ID", type=IntRange(1))
@pass_context
def cmd_context_move(ctx: Context, avid_dir: Path, from_doc_id: int, to_doc_id: int):
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    avid = AVID(avid_dir)

    context_docs: dict[int, dict] = read_context_documentation(avid)

    if from_doc_id not in context_docs:
        raise BadParameter(f"no context document with ID {from_doc_id}", ctx, ctx_params(ctx)["from_doc_id"])
    if to_doc_id not in context_docs:
        raise BadParameter(f"no context document with ID {to_doc_id}", ctx, ctx_params(ctx)["to_doc_id"])
    if from_doc_id == to_doc_id:
        return

    from_doc = deepcopy(context_docs[from_doc_id])
    to_doc = deepcopy(context_docs[to_doc_id])
    context_docs[from_doc_id] = to_doc
    context_docs[to_doc_id] = from_doc

    from_path_str, from_md5 = conn.execute(
        "select path, md5 from files where type = 'ContextDocumentation' and docId = ?", [from_doc_id]
    ).fetchone()
    to_path_str, to_md5 = conn.execute(
        "select path, md5 from files where type = 'ContextDocumentation' and docId = ?", [to_doc_id]
    ).fetchone()

    from_path = avid_dir.joinpath(from_path_str)
    to_path = avid_dir.joinpath(to_path_str)

    from_path_tmp = from_path.rename(to_path.with_name(f"tmp-{to_path.name}"))
    to_path.rename(from_path)
    from_path_tmp.rename(to_path)

    conn.execute(
        "update files set path = ?, md5 = ? where type = 'ContextDocumentation' and docId = ?",
        ["." + to_path_str, to_md5, from_doc_id],
    )
    conn.execute(
        "update files set path = ?, md5 = ? where type = 'ContextDocumentation' and docId = ?",
        [from_path_str, from_md5, to_doc_id],
    )
    conn.execute(
        "update files set path = ? where type = 'ContextDocumentation' and docId = ?",
        [to_path_str, from_doc_id],
    )

    write_context_documentation(avid, context_docs)
    update_md5(conn, avid.indices.contextDocumentationIndex)
    conn.commit()

    validate_xml(avid.indices.contextDocumentationIndex, avid.schemas.contextDocumentationIndex)


@grp_context.command("delete", no_args_is_help=True)
@argument_avid_dir(True)
@argument("DOC_ID", type=IntRange(1))
@pass_context
def cmd_context_delete(ctx: Context, avid_dir: Path, doc_id: int):
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    avid = AVID(avid_dir)

    context_docs: dict[int, dict] = read_context_documentation(avid)

    path_str: str = conn.execute(
        "select path from files where type = 'ContextDocumentation' and docId = ?",
        [doc_id],
    ).fetchone()[0]
    avid_dir.joinpath(path_str).unlink(missing_ok=True)
    conn.execute("delete from files where path = ?", [path_str])
    remove_empty_dir(avid_dir.joinpath("ContextDocumentation"), avid_dir.joinpath(path_str).parent)

    for old_doc_id in sorted([k for k in context_docs.keys() if k > doc_id]):
        new_doc_id = old_doc_id - 1
        path_str, doc_collection = conn.execute(
            "select path, docCollection from files where type = 'ContextDocumentation' and docId = ?",
            [old_doc_id],
        ).fetchone()
        path: Path = avid_dir.joinpath(path_str)
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
        remove_empty_dir(avid_dir.joinpath("ContextDocumentation"), path.parent)
        conn.commit()

    context_docs = {(i - 1) if i > doc_id else i: d for i, d in context_docs.items() if i != doc_id}
    write_context_documentation(avid, context_docs)
    update_md5(conn, avid.indices.contextDocumentationIndex)
    conn.commit()

    validate_xml(avid.indices.contextDocumentationIndex, avid.schemas.contextDocumentationIndex)
