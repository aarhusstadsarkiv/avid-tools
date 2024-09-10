from hashlib import md5
from pathlib import Path
from sqlite3 import connect
from sqlite3 import Connection

from acacore.utils.functions import file_checksum

from avid_tools.utils import file_md5


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
    conn.execute("update files set md5 = ? where path = ?", [file_md5(path), str(path)])
