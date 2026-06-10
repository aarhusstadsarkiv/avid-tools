import pytest
import logging

from avid_validator.command import cmd_validate_all
from click.testing import CliRunner
from pathlib import Path


def test_valid_db_is_validated(monkeypatch: pytest.MonkeyPatch, avid_dir: Path, caplog: pytest.LogCaptureFixture):
    monkeypatch.chdir(avid_dir)
    runner = CliRunner()

    with caplog.at_level(logging.INFO):
        runner.invoke(cmd_validate_all, [], catch_exceptions=False)

    assert "FAILED" not in caplog.text, "Some validation tests failed when it shouldnt have!"


def test_valid_db_fails_on_deliberate_index_error(monkeypatch: pytest.MonkeyPatch, avid_dir: Path, caplog: pytest.LogCaptureFixture):
    monkeypatch.chdir(avid_dir)
    runner = CliRunner()

    (avid_dir / "Indices" / "archiveIndex.xml").write_text("Yo")

    with caplog.at_level(logging.INFO):
        runner.invoke(cmd_validate_all, [], catch_exceptions=False)

    assert "FAILED" in caplog.text, "Validation didnt fail when it should have failed on archiveIndex!"
