from pathlib import Path
from sqlite3 import connect
from sqlite3 import Connection

from .utils import file_md5


def insert_file(conn: Connection, avid_dir: Path, file_path: Path, md5: str | None = None):
    file_type = file_path.parts[0]
    file_ext = file_path.suffix.removeprefix(".")
    doc_collection, doc_id = None, None
    if file_type == "Documents":
        _, doc_collection_str, doc_id_str, *_ = file_path.parts
        doc_collection = int(doc_collection_str.removeprefix("docCollection"))
        doc_id = int(doc_id_str)
    elif file_type == "ContextDocumentation":
        _, doc_collection_str, doc_id_str, *_ = file_path.parts
        doc_collection = int(doc_collection_str.removeprefix("docCollection"))
        doc_id = int(doc_id_str)
    conn.execute(
        "insert or ignore into files"
        " (path, format, type, md5, size, docCollection, docId)"
        " values (?, ?, ?, ?, ?, ?, ?)",
        [
            str(file_path),
            file_ext,
            file_type,
            (md5 or file_md5(avid_dir / file_path)).upper(),
            avid_dir.joinpath(file_path).stat().st_size,
            doc_collection,
            doc_id,
        ],
    )


def create_database(path: Path) -> Connection:
    conn = connect(str(path))

    conn.execute(
        """create table if not exists files (
                path text not null,
                format text not null,
                type text not null,
                md5  text default null,
                size int,
                docCollection int,
                docId int,
                parentId text default null,
                mId int default null,
                originalName text default null,
                originalExtension text default null,
                gmlXsd text default null,
                primary key (path))
            """
    )
    conn.execute("create index if not exists idx_files_format on files (format)")
    conn.execute("create index if not exists idx_files_original_extension on files (originalExtension)")
    conn.execute("create index if not exists idx_files_md5 on files (md5)")
    conn.execute("create index if not exists idx_files_type on files (type)")

    conn.execute(
        """create view if not exists originalExtensionCount as
            select lower(originalExtension) as originalExtension, count(*) as count, count(distinct md5) as distinctCount, min(docId) as firstDocId
            from files
            where type = 'Documents'
            group by lower(originalExtension)
            order by count desc
          """
    )

    conn.execute(
        """create view if not exists md5Count as
            select md5, count(*) as count, min(docId) as firstDocId
            from files
            where type = 'Documents'
            group by md5
            order by count desc
          """
    )

    return conn


def update_md5(conn: Connection, path: Path):
    conn.execute(
        "update files set md5 = ?, size = ? where path = ?",
        [file_md5(path).upper(), str(path), path.stat().st_size],
    )
