from pathlib import Path
from sqlite3 import Connection
from typing import Any

from xmltodict import parse as parse_xml
from xmltodict import unparse as unparse_xml

from .utils import file_md5
from .utils import path_suffixes


def insert_file(conn: Connection, avid_dir: Path, file_path: Path, md5: str | None = None):
    file_type = file_path.parts[0]
    file_ext = file_path.suffix.removeprefix(".")
    doc_collection, doc_id = None, None
    if file_type == "Documents":
        path_str: str = str(file_path).removeprefix("Documents/docCollection")
        doc_collection_str, doc_id_str, *_ = path_str.split("/")
        doc_collection = int(doc_collection_str)
        doc_id = int(doc_id_str)
    elif file_type == "ContextDocumentation":
        path_str: str = str(file_path).removeprefix("ContextDocumentation/docCollection")
        doc_collection_str, doc_id_str, *_ = path_str.split("/")
        doc_collection = int(doc_collection_str)
        doc_id = int(doc_id_str)
    conn.execute(
        "insert or ignore into files"
        " (path, extension, type, md5, docCollection, docId, originalExtension)"
        " values (?, ?, ?, ?, ?, ?, ?)",
        [
            str(file_path),
            file_ext,
            file_type,
            md5 or file_md5(avid_dir / file_path),
            doc_collection,
            doc_id,
            None,
        ],
    )


def save_file_index(avid_dir: Path, conn: Connection):
    def callback(_, tag: dict[str, str]):
        file_path = Path(tag["foN"].replace("\\", "/"), tag["fiN"])
        file_path = file_path.relative_to(avid_dir.name)
        insert_file(conn, avid_dir, file_path, tag["md5"])
        return True

    with avid_dir.joinpath("Indices", "fileIndex.xml").open("rb") as fh:
        parse_xml(fh, item_depth=2, item_callback=callback)

    conn.commit()


def save_doc_index(avid_dir: Path, conn: Connection):
    def callback(_, tag: dict[str, str]):
        conn.execute(
            "update files set originalExtension = ? where docId = ?",
            [path_suffixes(Path(tag["oFn"])).removeprefix("."), int(tag["dID"])],
        )
        return True

    with avid_dir.joinpath("Indices", "docIndex.xml").open("rb") as fh:
        parse_xml(fh, item_depth=2, item_callback=callback)

    conn.commit()


def read_context_documentation(avid_dir: Path) -> dict[int, dict[str, Any]]:
    context_docs: dict[int, dict[str, Any]] = {}

    def callback(_, tag: dict[str, Any]):
        context_docs[int(tag["documentID"])] = {k: v for k, v in tag.items() if k != "documentID"}
        return True

    with avid_dir.joinpath("Indices", "contextDocumentationIndex.xml").open("rb") as fh:
        parse_xml(fh, item_depth=2, item_callback=callback)

    return context_docs


# noinspection HttpUrlsUsage
def write_context_documentation(avid_dir: Path, context_docs: dict[int, dict[str, Any]]):
    xml: dict[str, Any] = {
        "contextDocumentationIndex": {
            "@xsi:schemaLocation": "http://www.sa.dk/xmlns/diark/1.0 ../Schemas/standard/contextDocumentationIndex.xsd",
            "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "@xmlns": "http://www.sa.dk/xmlns/diark/1.0",
            "document": [
                {"documentID": doc_id} | {k: v for k, v in doc.items() if k != "documentID"}
                for doc_id, doc in context_docs.items()
            ],
        }
    }
    avid_dir.joinpath("Indices", "contextDocumentationIndex.xml").write_text(unparse_xml(xml))
