import pytest
import sqlite3
from click.testing import CliRunner
from pathlib import Path
from avid_tools.commands import finalize


@pytest.fixture
def basic_conn():
    conn = sqlite3.connect(":memory:")

    conn.execute(
        """create table if not exists files (
                path text not null,
                format text,
                type text,
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

    conn.execute("insert into files(path, md5, size, type) values(?, ?, ?, ?)", ("Documents/1/1.tif", "", "", "Documents"))
    conn.execute("insert into files(path, md5, size) values(?, ?, ?)", ("Indices/docIndex.xml", "", ""))

    try:
        yield conn
    finally:
        conn.close()


class FakeIndices:
    docIndex: Path
    def __init__(self, dir) -> None:
        self.docIndex = dir / Path("Indices/docIndex.xml")


class FakeAVID:
    dir: Path
    indices: FakeIndices
    def __init__(self, *args, **kwargs) -> None:
        print("Setting up FakeAVID")
        self.dir = Path("python/tests/databases/test_avid1")
        self.indices = FakeIndices(self.dir)


def test_finalize(basic_conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch):
    """
    Test that the md5 values are updated!
    """
    # Create FakeAVID to be compatible with in-memory basic_conn database
    monkeypatch.setattr(finalize, "AVID", FakeAVID)
    monkeypatch.setattr(finalize, "create_database", lambda _: basic_conn)
    monkeypatch.setattr(finalize, "find_avid_dir", lambda _: None)

    # Do not generate docIndex and fileIndex
    monkeypatch.setattr(finalize, "generate_doc_index", lambda _, __: None)
    monkeypatch.setattr(finalize, "generate_file_index", lambda _, __: None)

    runner = CliRunner()
    runner.invoke(finalize.cmd_finalize, ["--skip-validate", "--update-hashes", "documents"], catch_exceptions=False)

    hashes = basic_conn.execute("select md5 from files").fetchall()

    for hash, in hashes:
        assert len(hash) != 0
