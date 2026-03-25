import xmltodict
import codecs
import xmlschema
import logging
from lxml import etree

from pathlib import Path
from typing import Any, Optional
from avid_validator import config as av_config
from avid_validator.common.report import Report

logger = logging.getLogger(__name__)


def prepare_xml(path: Path | str) -> Optional[dict[Any, Any]]:
    """
    Parse an XML file to a dict object
    """
    if isinstance(path, str):
        path = Path(path)

    try:
        if path.exists():
            return xmltodict.parse(path.read_text()) if path.exists() else None
    except:
        return None


def filenames(path: Path) -> list[str]:
    return [file.name for file in path.glob("*")]


def lazy_xml_validate(xml_path: Path, xsd_path: Path):
    """
    Validate an XML files lazily against an XML schema
    """
    xml_res = xmlschema.XMLResource(xml_path, lazy=True)
    schema = xmlschema.XMLSchema(xsd_path)
    schema.validate(xml_res)


def lxml_xml_validate(xml_path: Path, xsd_path: Path):
    schema = etree.XMLSchema(file=xsd_path)

    errors = []
    try:
        context = etree.iterparse(xml_path, events=("end",), schema=schema)
        for _, elem in context:
            elem.clear()

        return True, []
    except etree.XMLSyntaxError as e:
        errors.append(str(e))
        errors.extend(str(entry) for entry in e.error_log)
        return False, errors


def all_files() -> Optional[list[str]]:
    """
    Returns a list of filepaths defined in fileIndex.xml
    """
    file_index = prepare_xml(av_config.avid_dir / "Indices" / "fileIndex.xml")

    if file_index is None:
        return

    file_paths = []
    for item in file_index["fileIndex"]["f"]:
        file_path: str = item["foN"]
        file_path = (
            file_path.replace("\\", "/").replace(f"{av_config.avid_dir.name}/", "")
            + f"/{item["fiN"]}"
        )
        file_paths.append(file_path)

    return file_paths


def is_well_formed_utf8(file_path: Path, chunk_size: int = 1024 * 1024) -> Report:
    """
    Checks if file is well formed AND does not contain forbidden chars
    """
    FORBIDDEN = set(range(0x00, 0x20)) - {0x09, 0x0A, 0x0D}

    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    byte_pos = 0

    decode_fail = Report(
        success=False, reason=f"{file_path} is not a utf-8 well formed file"
    )
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            try:
                text = decoder.decode(chunk, final=False)
            except UnicodeDecodeError as e:
                return decode_fail

            for i, ch in enumerate(text):
                code = ord(ch)
                if code in FORBIDDEN:
                    return Report(
                        success=False,
                        reason=f"Forbidden character found in {file_path}",
                    )

            byte_pos += len(chunk)

        try:
            decoder.decode(b"", final=True)
        except UnicodeDecodeError as e:
            return decode_fail

    return Report(True)
