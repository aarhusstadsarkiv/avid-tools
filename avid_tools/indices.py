from pathlib import Path
from sqlite3 import Connection
from sqlite3 import Row
from typing import Any
from xml.sax.saxutils import escape

from xmltodict import parse as parse_xml
from xmltodict import unparse as unparse_xml

from .database import insert_file
from .utils import path_suffix


def save_file_index(avid_dir: Path, conn: Connection):
    def callback(_, tag: dict[str, str]):
        file_path = Path(tag["foN"].replace("\\", "/"), tag["fiN"])
        file_path = file_path.relative_to(avid_dir.name)
        insert_file(conn, avid_dir, file_path, tag["md5"])
        return True

    with avid_dir.joinpath("Indices", "fileIndex.xml").open("rb", encoding="utf-8") as fh:
        parse_xml(fh, item_depth=2, item_callback=callback)

    conn.commit()


# noinspection HttpUrlsUsage
def generate_file_index(conn: Connection, avid_dir: Path):
    with avid_dir.joinpath("Indices", "fileIndex.xml").open("w") as fh:
        fh.write('<?xml version="1.0" encoding="utf-8"?>\n')
        fh.write(
            '<fileIndex xsi:schemaLocation="http://www.sa.dk/xmlns/diark/1.0 ../Schemas/standard/fileIndex.xsd" xmlns="http://www.sa.dk/xmlns/diark/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        )
        cur = conn.execute("select path, md5 from files order by path")
        for path_str, md5 in cur:
            path = Path(path_str)
            fh.write("<f>")
            fh.write("<foN>{}\\{}</foN>".format(avid_dir.name, escape("\\".join(map(str, path.parent.parts)))))
            fh.write(f"<fiN>{escape(path.name)}</fiN>")
            fh.write(f"<md5>{md5.upper()}</md5>")
            fh.write("</f>")
        fh.write("</fileIndex>")


def save_doc_index(avid_dir: Path, conn: Connection):
    def callback(_, tag: dict[str, str]):
        conn.execute(
            "update files set format = ?, parentId = ?, mId = ?, gmlXsd = ?, originalName = ?, originalExtension = ? where type = 'Documents' and docId = ?",
            [
                tag["aFt"],
                tag.get("pID"),
                tag.get("mID"),
                tag.get("gmlXsd"),
                tag["oFn"],
                path_suffix(Path(tag["oFn"])).removeprefix("."),
                int(tag["dID"]),
            ],
        )
        return True

    with avid_dir.joinpath("Indices", "docIndex.xml").open("rb", encoding="utf-8") as fh:
        parse_xml(fh, item_depth=2, item_callback=callback)

    conn.commit()


# noinspection HttpUrlsUsage
def generate_doc_index(conn: Connection, avid_dir: Path):
    with avid_dir.joinpath("Indices", "docIndex.xml").open("w") as fh:
        fh.write('<?xml version="1.0" encoding="utf-8"?>\n')
        fh.write(
            '<docIndex xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.sa.dk/xmlns/diark/1.0" xsi:schemaLocation="http://www.sa.dk/xmlns/diark/1.0 file:///C:/Documents%20and%20Settings/rateb/Skrivebord/GML%20aflevering/AVID.SA.18001.1/Schemas/standard/docIndex.xsd">'
        )
        cur = conn.execute(
            "select docId, mId, parentId, docCollection, gmlXsd, originalName, format from files where type = 'Documents' order by docId"
        )
        cur.row_factory = Row
        document: Row
        for document in cur:
            fh.write("<doc>")
            fh.write(f"<dID>{document['docId']}</dID>")
            if document["parentId"] is not None:
                fh.write(f"<pID>{document['parentId']}</pID>")
            fh.write(f"<mID>{document['mId']}</mID>")
            fh.write(f"<dCf>docCollection{document['docCollection']}</dCf>")
            fh.write(f"<oFn>{escape(document['originalName'])}</oFn>")
            fh.write(f"<aFt>{escape(document['format'])}</aFt>")
            if document["gmlXsd"] is not None:
                fh.write(f"<gmlXsd>{escape(document['gmlXsd'])}</gmlXsd>")
            fh.write("</doc>")
        fh.write("</docIndex>")


def read_context_documentation(avid_dir: Path) -> dict[int, dict[str, Any]]:
    context_docs: dict[int, dict[str, Any]] = {}

    def callback(_, tag: dict[str, Any]):
        context_docs[int(tag["documentID"])] = {k: v for k, v in tag.items() if k != "documentID"}
        return True

    with avid_dir.joinpath("Indices", "contextDocumentationIndex.xml").open("rb", encoding="utf-8") as fh:
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
    avid_dir.joinpath("Indices", "contextDocumentationIndex.xml").write_text(unparse_xml(xml, encoding="utf-8"))
