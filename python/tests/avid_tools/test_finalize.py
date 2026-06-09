from avid_tools.utils import file_md5
import pytest
import sqlite3
import shutil

from click.testing import CliRunner
from pathlib import Path
from avid_tools.commands import finalize
from avid_tools.commands import init


@pytest.fixture
def avid_dir(tmpdir: Path):
    shutil.copytree("python/tests/databases/AVID.SA.18004.1", tmpdir / "AVID.SA.18004.1")
    return Path(tmpdir / "AVID.SA.18004.1")


@pytest.fixture
def avid_dir_with_db(tmpdir: Path, monkeypatch: pytest.MonkeyPatch):
    shutil.copytree("python/tests/databases/AVID.SA.18004.1", tmpdir / "AVID.SA.18004.1")
    tmp_avid_dir = Path(tmpdir / "AVID.SA.18004.1")

    monkeypatch.chdir(tmp_avid_dir)

    CliRunner().invoke(init.cmd_init, ["."])

    assert (tmp_avid_dir / "_metadata" / "avid_tools.db").exists()

    return tmp_avid_dir


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
    original_exists = Path.exists
    def fake_exists(self):
        if self.name == "avid_tools.db":
            return True
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)

    # Do not generate docIndex and fileIndex
    monkeypatch.setattr(finalize, "generate_doc_index", lambda _, __: None)
    monkeypatch.setattr(finalize, "generate_file_index", lambda _, __: None)

    runner = CliRunner()
    runner.invoke(finalize.cmd_finalize, ["--skip-validate", "--update-hashes", "documents"], catch_exceptions=False)

    hashes = basic_conn.execute("select md5 from files").fetchall()

    for hash, in hashes:
        assert len(hash) != 0


def test_finalize_raises_error_when_no_db_found(monkeypatch: pytest.MonkeyPatch, avid_dir: Path):
    monkeypatch.chdir(avid_dir)
    
    with pytest.raises(FileNotFoundError, match="avid_tools.db"):
        runner = CliRunner()
        runner.invoke(finalize.cmd_finalize, ["--skip-validate", "--update-hashes", "documents"], catch_exceptions=False)


def test_finalize_fixes_table_xml_md5(monkeypatch: pytest.MonkeyPatch, avid_dir_with_db: Path):
    monkeypatch.chdir(avid_dir_with_db)

    file = avid_dir_with_db / "Tables" / "table1" / "table1.xml"
    file.write_text("new table text")

    file_hash = file_md5(file)

    runner = CliRunner()
    runner.invoke(finalize.cmd_finalize, ["--skip-validate", "--update-hashes", "tables"], catch_exceptions=False)

    assert file_hash in (avid_dir_with_db / "Indices" / "fileIndex.xml").read_text(encoding="utf8")


def test_finalize_fixes_table_xsd_md5(monkeypatch: pytest.MonkeyPatch, avid_dir_with_db: Path):
    monkeypatch.chdir(avid_dir_with_db)

    file = avid_dir_with_db / "Tables" / "table1" / "table1.xsd"
    file.write_text("new table text")

    file_hash = file_md5(file)

    runner = CliRunner()
    runner.invoke(finalize.cmd_finalize, ["--skip-validate", "--update-hashes", "tables"], catch_exceptions=False)

    assert file_hash in (avid_dir_with_db / "Indices" / "fileIndex.xml").read_text(encoding="utf8")


def test_finalize_fixes_document_md5(monkeypatch: pytest.MonkeyPatch, avid_dir_with_db: Path):
    monkeypatch.chdir(avid_dir_with_db)

    file = avid_dir_with_db / "Documents" / "docCollection1" / "1" / "1.tif"
    file.write_text("new document text")

    file_hash = file_md5(file)

    runner = CliRunner()
    runner.invoke(finalize.cmd_finalize, ["--skip-validate", "--update-hashes", "documents"], catch_exceptions=False)

    assert file_hash in (avid_dir_with_db / "Indices" / "fileIndex.xml").read_text(encoding="utf8")


def test_finalize_fixes_context_document_md5(monkeypatch: pytest.MonkeyPatch, avid_dir_with_db: Path):
    monkeypatch.chdir(avid_dir_with_db)

    file = avid_dir_with_db / "ContextDocumentation" / "docCollection1" / "1" / "1.tif"
    file.write_text("new context document text")

    file_hash = file_md5(file)

    runner = CliRunner()
    runner.invoke(finalize.cmd_finalize, ["--skip-validate", "--update-hashes", "context"], catch_exceptions=False)

    assert file_hash in (avid_dir_with_db / "Indices" / "fileIndex.xml").read_text(encoding="utf8")


def test_finalize_fixes_archiveIndex_md5(monkeypatch: pytest.MonkeyPatch, avid_dir_with_db: Path):
    monkeypatch.chdir(avid_dir_with_db)

    file = avid_dir_with_db / "Indices" / "archiveIndex.xml"
    file.write_text("new index text")

    file_hash = file_md5(file)

    runner = CliRunner()
    runner.invoke(finalize.cmd_finalize, ["--skip-validate", "--update-hashes", "index"], catch_exceptions=False)

    assert file_hash in (avid_dir_with_db / "Indices" / "fileIndex.xml").read_text(encoding="utf8")


def test_finalize_fixes_tableIndex_md5(monkeypatch: pytest.MonkeyPatch, avid_dir_with_db: Path):
    monkeypatch.chdir(avid_dir_with_db)

    file = avid_dir_with_db / "Indices" / "tableIndex.xml"
    file.write_text("new index text")

    file_hash = file_md5(file)

    runner = CliRunner()
    runner.invoke(finalize.cmd_finalize, ["--skip-validate", "--update-hashes", "index"], catch_exceptions=False)

    assert file_hash in (avid_dir_with_db / "Indices" / "fileIndex.xml").read_text(encoding="utf8")


def test_finalize_fixes_contextDocumentationIndex_md5(monkeypatch: pytest.MonkeyPatch, avid_dir_with_db: Path):
    monkeypatch.chdir(avid_dir_with_db)

    file = avid_dir_with_db / "Indices" / "contextDocumentationIndex.xml"
    file.write_text("new index text")

    file_hash = file_md5(file)

    runner = CliRunner()
    runner.invoke(finalize.cmd_finalize, ["--skip-validate", "--update-hashes", "index"], catch_exceptions=False)

    assert file_hash in (avid_dir_with_db / "Indices" / "fileIndex.xml").read_text(encoding="utf8")


def test_document_added_also_adds_hash(monkeypatch: pytest.MonkeyPatch, avid_dir_with_db: Path):
    monkeypatch.chdir(avid_dir_with_db)

    file = avid_dir_with_db / "Documents" / "docCollection1" / "3141" / "1.tif"
    file.parent.mkdir(parents=True)
    file.write_text("new document text")

    file_hash = file_md5(file)

    runner = CliRunner()
    runner.invoke(finalize.cmd_finalize, ["--skip-validate", "--update-hashes", "documents"], catch_exceptions=False)

    assert file_hash in (avid_dir_with_db / "Indices" / "fileIndex.xml").read_text(encoding="utf8")
