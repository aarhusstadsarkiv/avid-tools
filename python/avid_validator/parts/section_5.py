import logging
import os
import re
from pathlib import Path

from tqdm import tqdm

from avid_validator.common import utils  # pyright: ignore
from avid_validator.common.archive import ValidationContext
from avid_validator.common.archive import ValidationType
from avid_validator.common.archive import XMLIndices
from avid_validator.common.description import describe
from avid_validator.common.description import register
from avid_validator.common.report import fail
from avid_validator.common.report import GenReport
from avid_validator.common.types import get_allowed_table_types

logger = logging.getLogger(__name__)


@describe(
    """I overensstemmelse med den tabelstruktur, der i XML-instansen »tableIndex.xml« er defineret for hver tabel,
skal hver tabel findes i en XML-instans navngivet »table[fortløbende nummer]. xml«."""
)
@register(ValidationType.TABLES)
def validate_5a1a(ctx: ValidationContext, indeces: XMLIndices) -> GenReport:
    table_idx = indeces.tableIndex
    tables_dir_files = os.listdir(ctx.tables)

    if table_idx is None:
        yield fail("tableIndex.xml is None!")
        return

    for table in table_idx["siardDiark"]["tables"]["table"]:
        if table["folder"] not in tables_dir_files:
            yield fail("Table defined in tableIndex not present in Tables folder!")


@describe("""Den fortløbende nummerering begynder med 1. Foranstillede nuller må ikke anvendes.""")
@register(ValidationType.TABLES)
def validate_5a1b(indeces: XMLIndices) -> GenReport:
    table_idx = indeces.tableIndex

    if not table_idx is not None:
        yield fail("tableIndex.xml is None!")
        return

    table_ids = []
    for table in table_idx["siardDiark"]["tables"]["table"]:
        folder = int(
            re.match(r"table(\d+)$", table["folder"]).group(1)  # pyright: ignore
        )
        table_ids.append(folder)

    if not sorted(table_ids)[0] == 1:
        yield fail("First table id must be 1!")


def _rust_validate_5a2() -> GenReport:
    """
    This method is Rust alternative to the pure python method 'validate_5a2'
    """
    from avid_tools import feo2xmlprobe

    res = feo2xmlprobe.validate_tables_xsd()
    for item in res:
        yield fail(f"Failed {item}")


@describe("""Indholdet af de enkelte felter skal renses for eventuelle foran- og efterstillede blanktegn""")
@register(ValidationType.TABLES, rust=_rust_validate_5a2)
def validate_5a2(ctx: ValidationContext):
    tables = sorted(ctx.tables.rglob("table*.xml"))
    process = tqdm(tables)
    for table in process:
        process.set_description(f"Processing {table.name}")

        if not utils.validate_no_whitespaces(table):
            yield fail(f"Table {table} has whitespaces")


"""
5B Datatyper
"""


@describe(
    """De standardiserede datatyper, som skal anvendes for tabelindhold, er angivet i figur 5.1.
    De er et uddrag af datatyper fra standarden SQL:1999 repræsenteret som
    datatyper i W3C XML Schema Language 1.0"""
)
@register(ValidationType)
def validate_5b1(ctx: ValidationContext, indices: XMLIndices) -> GenReport:
    """
    The XSD schemas for each table, should be able to validate the given types.

    Then the large part of this code is validating that the cell types specified in tableIndex.xml,
    match with the given table schema file.
    """
    if indices.tableIndex is None:
        yield fail("tableIndex has not been parsed, maybe it doesnt exist!")
        return

    allowed_table_types = get_allowed_table_types()
    tables = indices.tableIndex["siardDiark"]["tables"]["table"]
    for table in tables:
        columns = table["columns"]["column"]
        table_folder = table["folder"]
        table_name = table["name"]

        for column in columns:
            try:
                ctype = column["type"]
                column_id = column["columnID"]
                att = allowed_table_types.match(ctype)

                if att is None:
                    yield fail(
                        f"Table '{table_name}' in folder '{table_folder}' has column '{column['name']}' whose type '{ctype}' could not be parsed! (Maybe it's not valid!)"
                    )
                    continue

                # Parse XSD and make sure it is a valid conversion from tableIndex type!
                xsd_path = ctx.tables / table["folder"] / (table_folder + ".xsd")
                xsd_dict = utils.prepare_xml(xsd_path)
                if xsd_dict is None:
                    yield fail(f"Could not parse XSD file, {xsd_path}")
                    continue

                elements = xsd_dict["xs:schema"]["xs:complexType"]["xs:sequence"]["xs:element"]
                element = [element for element in elements if element["@name"] == column_id][0]
                element_type = element["@type"].split(":")[1].lower()

                if not att.allowed(element_type):
                    yield fail(
                        f"Column '{column_id}' in XSD schema for table '{table_name}' in folder '{table_folder}' has non-allowed type '{element_type}'. Type rule: '{att}'"
                    )
            except Exception:
                yield fail(f"An error occurred when parsing column, '{column}', for table, {table}!")


"""
5C Konvertering af tabelindhold til digitale dokumenter, lyd, video eller geodata
"""


@describe(
    """Tabelindhold skal overholde de angivne datatyper, jf. 5. B. Det følger heraf, at dataindhold i tabelform fra et it-system,
som skal overføres til en arkiveringsversion og som ikke umiddelbart kan overholde dette krav, skal have sit dataindhold konverteret således"""
)
@register(ValidationType.TABLES)
def validate_5c1(ctx: ValidationContext) -> GenReport:
    tables = list(ctx.tables.rglob("table*.xml"))
    for table_xml_path in tqdm(tables):
        table_xsd_path = table_xml_path.parent.joinpath(f"{table_xml_path.stem}.xsd")

        res, errs = utils.lxml_xml_validate(table_xml_path, table_xsd_path)
        if not res:
            print(errs)
            yield fail(f"Error occurred in {table_xml_path}")


"""
5D Tekstformat
"""


@describe(
    """Data i arkiveringsversionens indeksfiler og tabelindhold skal være indkodet som well-formed UTF-8,
    som angivet i ISO/IEC 10646:2003 Annex D og som beskrevet i The Unicode Standard 5.1, kapitel 3."""
)
@register((ValidationType.INDICES, ValidationType.TABLES))
def validate_5d1a() -> GenReport:
    files = utils.all_files()
    if not files:
        yield fail("List of files could not be generated!")
        return

    for file in files:
        if "Indices" not in file or "Tables" in file:
            continue

        well_formed_report = utils.is_well_formed_utf8(Path(file))
        if not well_formed_report.success:
            yield well_formed_report


def validate_5d_textformat() -> GenReport:
    yield fail(
        "No validations implemented for text formats except for UTF-8 compliance and check for disallowed chars!"
    )


# validate_5d1d is a subset of 5d1a


# ...

"""
5E Digitale dokumenter
"""


@register((ValidationType.DOCS, ValidationType.CONTEXTDOCS))
def validate_5e() -> GenReport:
    from avid_validator.common import tiff

    tiff_files = Path(".").resolve().rglob("*.tif")
    files = list(tiff_files)
    logger.info("Run tif check!")
    for file in tqdm(files):
        yield from tiff.check_tiff_bek128_bitdepths(file)


def validate_5e_digital_documents() -> GenReport:
    yield fail("No validations implemented for digital documents except for tif files!")


"""
5F Lyd of video
"""


def validate_5f_video_audio() -> GenReport:
    yield fail("No validations implemented for video and audio!")


"""
5G Geodata
"""


def validate_5g_geodate() -> GenReport:
    yield fail("No validations implemented for geodata!")


"""
5H Komprimering
"""

# ...

"""
5I Optimering
"""

# ...

"""
5J Ingen forringelse
"""
