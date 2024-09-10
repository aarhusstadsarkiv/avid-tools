from pathlib import Path
from sqlite3 import Connection
from typing import Any

from xmltodict import parse as parse_xml
from xmltodict import unparse as unparse_xml

from .database import insert_file
from .utils import path_suffixes


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
            "update files set format = ?, parentId = ?, mId = ?, gmlXsd = ?, originalName = ?, originalExtension = ? where type = 'Documents' and docId = ?",
            [
                tag["aFt"],
                tag.get("pID"),
                tag.get("mID"),
                tag["oFn"],
                tag.get("gmlXsd"),
                path_suffixes(Path(tag["oFn"])).removeprefix("."),
                int(tag["dID"]),
            ],
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
