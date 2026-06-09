import pytest
from pathlib import Path
import shutil
from click.testing import CliRunner
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


