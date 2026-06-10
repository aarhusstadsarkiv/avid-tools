import pytest
import logging
import shutil

from avid_validator.command import cmd_validate_all
from click.testing import CliRunner
from pathlib import Path


def check_validation(error_message: str, caplog: pytest.LogCaptureFixture, succeed: bool):
    runner = CliRunner()

    with caplog.at_level(logging.INFO):
        runner.invoke(cmd_validate_all, [], catch_exceptions=False)

    if succeed:
        assert "FAILED" not in caplog.text, error_message
    else:
        assert "FAILED" in caplog.text, error_message


def get_run_caplog_text(caplog: pytest.LogCaptureFixture) -> str:
    runner = CliRunner()

    with caplog.at_level(logging.DEBUG):
        runner.invoke(cmd_validate_all, [], catch_exceptions=False)

    return caplog.text

def check_validation_fail(error_message: str, caplog: pytest.LogCaptureFixture):
    check_validation(error_message, caplog, succeed=False)


def check_validation_succeed(error_message: str, caplog: pytest.LogCaptureFixture):
    check_validation(error_message, caplog, succeed=True)


def test_valid_db_is_validated(monkeypatch: pytest.MonkeyPatch, avid_dir: Path, caplog: pytest.LogCaptureFixture):
    monkeypatch.chdir(avid_dir)
    
    check_validation_succeed("Validation failed when it should not have!", caplog)


def test_valid_db_fails_on_deliberate_index_error(
    monkeypatch: pytest.MonkeyPatch, avid_dir: Path, caplog: pytest.LogCaptureFixture
):
    monkeypatch.chdir(avid_dir)

    (avid_dir / "Indices" / "archiveIndex.xml").write_text("Yo")

    check_validation_fail("Validation didnt fail when it should have failed on archiveIndex!", caplog)


def test_docCollection_not_start_with_1(monkeypatch: pytest.MonkeyPatch, avid_dir: Path, caplog: pytest.LogCaptureFixture):
    monkeypatch.chdir(avid_dir)

    doc_collection_path = avid_dir.joinpath("Documents", "docCollection1")
    shutil.rmtree(doc_collection_path)

    check_validation_fail("Should have failed validation when docCollection does not start with 1!", caplog)


def test_no_doccollection_when_archive_index_states_it_has(monkeypatch: pytest.MonkeyPatch, avid_dir: Path, caplog: pytest.LogCaptureFixture):
    monkeypatch.chdir(avid_dir)

    documents_path = avid_dir.joinpath("Documents")
    shutil.rmtree(documents_path)

    check_validation_fail("Should have failed validation when docCollection does not start with 1!", caplog)


def test_fail_on_no_index_files(monkeypatch: pytest.MonkeyPatch, avid_dir: Path, caplog: pytest.LogCaptureFixture):
    monkeypatch.chdir(avid_dir)

    documents_path = avid_dir.joinpath("Indices")
    shutil.rmtree(documents_path)

    check_validation_fail("Did not fail when no indeces exist!", caplog)


def test_fail_on_bad_xsd_type(monkeypatch: pytest.MonkeyPatch, avid_dir: Path, caplog: pytest.LogCaptureFixture):
    monkeypatch.chdir(avid_dir)

    xsd_content_format = """<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns="http://www.sa.dk/xmlns/siard/1.0/schema0/table1.xsd" attributeFormDefault="unqualified" elementFormDefault="qualified" targetNamespace="http://www.sa.dk/xmlns/siard/1.0/schema0/table1.xsd" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="table">
    <xs:complexType>
      <xs:sequence>
        <xs:element minOccurs="0" maxOccurs="unbounded" name="row" type="rowType" />
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="rowType">
    <xs:sequence>
      <xs:element minOccurs="1" name="c1" type="xs:{}" />
      <xs:element minOccurs="1" name="c2" type="xs:string" />
    </xs:sequence>
  </xs:complexType>
</xs:schema>"""

    print(xsd_content_format.format("some weird format"))
    table1_xsd = avid_dir.joinpath("Tables", "table1", "table1.xsd")
    assert table1_xsd.exists()

    table1_xsd.write_text(xsd_content_format.format("some_weird_number"), encoding="utf8")
    assert "validate_5b1 FAILED" not in get_run_caplog_text(caplog), "validate 5b1 should not have failed in test 1"

    table1_xsd.write_text(xsd_content_format.format("integer"), encoding="utf8")
    assert "validate_5b1 FAILED" not in get_run_caplog_text(caplog), "validate 5b1 should have failed in test 2"
