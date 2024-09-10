from pathlib import Path
from sqlite3 import connect
from sqlite3 import Connection

from .utils import file_md5


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
            (md5 or file_md5(avid_dir / file_path)).upper(),
            doc_collection,
            doc_id,
            None,
        ],
    )


def create_database(path: Path) -> Connection:
    conn = connect(str(path))

    conn.execute(
        """create table if not exists files (
                path text not null,
                extension text not null,
                md5  text,
                type text not null,
                docCollection int,
                docId int,
                originalExtension text,
                primary key (path))
            """
    )
    conn.execute("create index if not exists files_extension on files (extension)")
    conn.execute("create index if not exists files_md5 on files (md5)")
    conn.execute("create index if not exists files_type on files (type)")

    return conn


def update_md5(conn: Connection, path: Path):
    conn.execute("update files set md5 = ? where path = ?", [file_md5(path).upper(), str(path)])
