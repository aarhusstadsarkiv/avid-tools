import pytest

from avid_validator.command import cmd_validate_all
from click.testing import CliRunner
from pathlib import Path


def test_valid_db_is_validated(monkeypatch: pytest.MonkeyPatch, avid_dir: Path):
    monkeypatch.chdir(avid_dir)
    runner = CliRunner()
    run_res = runner.invoke(cmd_validate_all, [], catch_exceptions=False)

    assert "FAILED" not in run_res.output, "Some validation tests failed when it shouldnt have!"
