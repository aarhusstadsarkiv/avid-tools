import logging
import os
import re
from pathlib import Path

from tqdm import tqdm
from xmlschema import XMLResource

from avid_validator.common import utils
from avid_validator.common.archive import ValidationContext
from avid_validator.common.archive import ValidationType
from avid_validator.common.archive import XMLIndices
from avid_validator.common.description import categorize
from avid_validator.common.description import describe
from avid_validator.common.report import fail
from avid_validator.common.report import GenReport

logger = logging.getLogger(__name__)


@describe(
    """I overensstemmelse med den tabelstruktur, der i XML-instansen »tableIndex.xml« er defineret for hver tabel,
skal hver tabel findes i en XML-instans navngivet »table[fortløbende nummer]. xml«."""
)
@categorize(ValidationType.TABLES)
def validate_5a1a(ctx: ValidationContext, indeces: XMLIndices) -> GenReport:
    table_idx = indeces.tableIndex
    tables_dir_files = os.listdir(ctx.tables)

    if table_idx is None:
        yield fail("tableIndex.xml is None!")
        return

    for table in table_idx["siardDiark"]["tables"]["table"]:
        if table["folder"] not in tables_dir_files:
            yield fail("Table defined in tableIndex not present in Tables folder!")


@describe(
    """Den fortløbende nummerering begynder med 1. Foranstillede nuller må ikke anvendes."""
)
@categorize(ValidationType.TABLES)
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


@describe(
    """Indholdet af de enkelte felter skal renses for eventuelle foran- og efterstillede blanktegn"""
)
@categorize(ValidationType.TABLES)
def validate_5a2(ctx: ValidationContext):
    tables = sorted(ctx.tables.rglob("table*.xml"))
    cell_tag_re = re.compile(r"\{.*\}c\d+$")
    process = tqdm(tables)
    for table in process:
        process.set_description(f"Processing {table.name}")
        res = XMLResource(table, lazy=True)
        for elem in res.iter():
            text = elem.text
            if text is None:
                continue
            if not cell_tag_re.match(elem.tag):
                continue
            if text != text.strip():
                yield fail(f"Whitespace detected in {table}")
                break


"""
5B Datatyper
"""

# ...

"""
5C Konvertering af tabelindhold til digitale dokumenter, lyd, video eller geodata
"""

# ...

"""
5D Tekstformat
"""


@describe(
    "Data i arkiveringsversionens indeksfiler og tabelindhold skal være indkodet som well-formed UTF-8, som angivet i ISO/IEC 10646:2003 Annex D og som beskrevet i The Unicode Standard 5.1, kapitel 3."
)
@categorize((ValidationType.INDICES, ValidationType.TABLES))
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
