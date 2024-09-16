from copy import deepcopy
from pathlib import Path
from shutil import copy2
from sqlite3 import Connection

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
from avid_tools.utils import AVID
from avid_tools.utils import ctx_params
from avid_tools.utils import find_avid_dir
from avid_tools.utils import remove_empty_dir
from avid_tools.utils import validate_xml


def move_context_docs(
    conn: Connection,
    avid: AVID,
    context_docs: dict[int, dict],
    interval: tuple[int, int],
    diff: int,
) -> dict[int, dict]:
    if diff == 0 or interval[1] - interval[0] < 0:
        return context_docs

    doc_ids: list[int] = sorted(
        (i for i in context_docs if interval[0] <= i <= interval[1]),
        reverse=diff > 0,
    )

    for doc_id in doc_ids:
        new_doc_id: int = doc_id + diff
        path_str, doc_collection = conn.execute(
            "select path, docCollection from files where type = 'ContextDocumentation' and docId = ?",
            [doc_id],
        ).fetchone()
        path: Path = avid.dir.joinpath(path_str)
        new_path: Path = avid.dir.joinpath(
            "ContextDocumentation",
            f"docCollection{doc_collection}",
            str(new_doc_id),
            path.name,
        )
        new_path.parent.mkdir(parents=True, exist_ok=True)
        path.rename(new_path)
        remove_empty_dir(avid.dir / "ContextDocumentation", path.parent)
        conn.execute(
            "update files set path = ?, docId = ? where type = 'ContextDocumentation' and docId = ?",
            [str(new_path.relative_to(avid.dir)), new_doc_id, doc_id],
        )
        conn.commit()

    return {(i + diff) if i in doc_ids else i: d for i, d in context_docs.items()}


@group("context", no_args_is_help=True)
def grp_context(): ...


# noinspection HttpUrlsUsage,DuplicatedCode
@grp_context.command("add", no_args_is_help=True, short_help="Add a context document.")
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
def cmd_context_add(ctx: Context, file: Path, metadata: Path, position: int):
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
    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    db_path: Path = avid.dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)

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

    context_docs = move_context_docs(conn, avid, context_docs, (new_context_doc_id, len(context_docs)), +1)

    context_docs[new_context_doc_id] = new_context_doc

    new_context_doc_path = avid.dir.joinpath(
        "ContextDocumentation",
        f"docCollection1",
        str(new_context_doc_id),
        f"1{file.suffix}",
    )
    new_context_doc_path.parent.mkdir(parents=True, exist_ok=True)
    copy2(file, new_context_doc_path)
    insert_file(conn, avid.dir, new_context_doc_path.relative_to(avid.dir))

    write_context_documentation(avid, context_docs)

    update_md5(conn, avid.indices.contextDocumentationIndex)

    conn.commit()

    validate_xml(avid.indices.contextDocumentationIndex, avid.schemas.contextDocumentationIndex)


# noinspection HttpUrlsUsage,DuplicatedCode
@grp_context.command("update", no_args_is_help=True)
@argument("DOC_ID", type=IntRange(1))
@option(
    "--file",
    type=ClickPath(exists=True, dir_okay=False, readable=True, resolve_path=True),
    default=None,
    callback=lambda _c, _p, v: Path(v) if v else None,
)
@option(
    "--metadata",
    type=ClickPath(exists=True, dir_okay=False, readable=True, resolve_path=True),
    default=None,
    callback=lambda _c, _p, v: Path(v) if v else None,
)
@pass_context
def cmd_context_update(ctx: Context, doc_id: int, file: Path | None, metadata: Path | None):
    if not file and not metadata:
        return

    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    db_path: Path = avid.dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)

    context_docs: dict[int, dict] = read_context_documentation(avid)

    if doc_id not in context_docs:
        raise BadParameter(f"no context document with ID {doc_id}", ctx, ctx_params(ctx)["doc_id"])

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

        context_docs[doc_id] = new_context_doc
        write_context_documentation(avid, context_docs)
        update_md5(conn, avid.indices.contextDocumentationIndex)
        validate_xml(avid.indices.contextDocumentationIndex, avid.schemas.contextDocumentationIndex)

    if file:
        path_str: str = conn.execute(
            "select path from files where type = 'ContextDocumentation' and docId = ?",
            [doc_id],
        ).fetchone()[0]
        copy2(file, path := avid.dir.joinpath(path_str).with_suffix(file.suffix))
        conn.execute(
            "update files set path = ? where type = 'ContextDocumentation' and docId = ?",
            [str(path.relative_to(avid.dir)), doc_id],
        )
        update_md5(conn, path)

    conn.commit()


# noinspection DuplicatedCode
@grp_context.command("move", no_args_is_help=True, context_settings={"ignore_unknown_options": True})
@argument("FROM_DOC_ID", type=IntRange(1))
@argument("TO_DOC_ID", type=IntRange(-1))
@pass_context
def cmd_context_move(ctx: Context, from_doc_id: int, to_doc_id: int):
    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    db_path: Path = avid.dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)

    context_docs: dict[int, dict] = read_context_documentation(avid)

    if from_doc_id not in context_docs:
        raise BadParameter(f"no context document with ID {from_doc_id}", ctx, ctx_params(ctx)["from_doc_id"])
    if to_doc_id > 0 and to_doc_id not in context_docs:
        raise BadParameter(f"no context document with ID {to_doc_id}", ctx, ctx_params(ctx)["to_doc_id"])
    if from_doc_id == to_doc_id:
        return

    from_doc = deepcopy(context_docs[from_doc_id])

    if to_doc_id <= 0:
        del context_docs[from_doc_id]
        from_path_str, *from_doc_data = conn.execute(
            "select path, format, type, md5, docCollection, parentId, mId, originalName, originalExtension, gmlXsd"
            " from files where type = 'ContextDocumentation' and docId = ?",
            [from_doc_id],
        ).fetchone()
        conn.execute("delete from files where type = 'ContextDocumentation' and docId = ?", [from_doc_id])
        conn.commit()
        from_path: Path = avid.dir.joinpath(from_path_str)
        from_path_tmp: Path = from_path.replace(avid.dir.joinpath(from_path.name).with_name("." + from_path.name))
        remove_empty_dir(avid.dir / "ContextDocumentation", from_path.parent)

        if to_doc_id == 0:
            to_doc_id = 1
            context_docs = move_context_docs(conn, avid, context_docs, (to_doc_id, from_doc_id), +1)
        else:
            to_doc_id = len(context_docs) + 1
            context_docs = move_context_docs(conn, avid, context_docs, (from_doc_id, to_doc_id), -1)

        context_docs[to_doc_id] = from_doc

        new_path: Path = avid.dir.joinpath(
            "ContextDocumentation",
            f"docCollection{from_doc_data[3]}",
            str(to_doc_id),
            from_path.name,
        )
        new_path.parent.mkdir(parents=True, exist_ok=True)
        from_path_tmp.rename(new_path)
        conn.execute(
            "insert into files"
            " (path, docId, format, type, md5, docCollection, parentId, mId, originalName, originalExtension, gmlXsd)"
            " values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [str(new_path.relative_to(avid.dir)), to_doc_id, *from_doc_data],
        )
    else:
        to_doc = deepcopy(context_docs[to_doc_id])
        context_docs[from_doc_id] = to_doc
        context_docs[to_doc_id] = from_doc

        from_path_str, from_md5 = conn.execute(
            "select path, md5 from files where type = 'ContextDocumentation' and docId = ?", [from_doc_id]
        ).fetchone()
        to_path_str, to_md5 = conn.execute(
            "select path, md5 from files where type = 'ContextDocumentation' and docId = ?", [to_doc_id]
        ).fetchone()

        from_path = avid.dir.joinpath(from_path_str)
        to_path = avid.dir.joinpath(to_path_str)

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


# noinspection DuplicatedCode
@grp_context.command("delete", no_args_is_help=True)
@argument("DOC_ID", type=IntRange(1))
@pass_context
def cmd_context_delete(ctx: Context, doc_id: int):
    avid: AVID = AVID(find_avid_dir(Path.cwd()))
    db_path: Path = avid.dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)

    context_docs: dict[int, dict] = read_context_documentation(avid)

    if doc_id not in context_docs:
        raise BadParameter(f"no context document with ID {doc_id}", ctx, ctx_params(ctx)["doc_id"])

    path_str: str = conn.execute(
        "select path from files where type = 'ContextDocumentation' and docId = ?",
        [doc_id],
    ).fetchone()[0]
    avid.dir.joinpath(path_str).unlink(missing_ok=True)
    conn.execute("delete from files where path = ?", [path_str])
    remove_empty_dir(avid.dir.joinpath("ContextDocumentation"), avid.dir.joinpath(path_str).parent)

    del context_docs[doc_id]

    context_docs = move_context_docs(conn, avid, context_docs, (doc_id, len(context_docs)), -1)

    write_context_documentation(avid, context_docs)
    update_md5(conn, avid.indices.contextDocumentationIndex)
    conn.commit()

    validate_xml(avid.indices.contextDocumentationIndex, avid.schemas.contextDocumentationIndex)
