import os
import re
from avid_validator.common.archive import ValidationContext, ValidationType, XMLIndices
from avid_validator.common.description import categorize, describe
from avid_validator.common.report import GenReport, Report, fail


@describe(
    """Mappen Tables skal indeholde én mappe for hver tabel i arkiveringsversionen."""
)
@categorize(ValidationType.TABLES)
def validate_4d1(ctx: ValidationContext, indices: XMLIndices) -> GenReport:
    table_idx = indices.tableIndex

    assert table_idx is not None, "No table index!"

    tables = table_idx["siardDiark"]["tables"]["table"]
    tabledir_files = os.listdir(ctx.tables)
    if len(tables) != len(tabledir_files):
        yield fail("Mismatch in number of tables in Tables and tableIndex.xml")


@describe("""Mappen for en tabel navngives »table[fortløbende nummer]«.""")
@categorize(ValidationType.TABLES)
def validate_4d2a(ctx: ValidationContext) -> GenReport:
    tables = os.listdir(ctx.tables)
    for table in tables:
        if not re.match(r"table\d+$", table):
            yield Report(
                success=False,
                reason=rf"Tables must be named 'table\d+$, which is not the case for {table}",
            )


@describe(
    """Den fortløbende nummerering begynder med 1. Foranstillede nuller må ikke anvendes."""
)
@categorize(ValidationType.TABLES)
def validate_4d2b(ctx: ValidationContext) -> GenReport:
    tables = [
        int(re.match(r"table(\d+)$", table).group(1))  # pyright: ignore
        for table in os.listdir(ctx.tables)
    ]  # pyright: ignore
    tables = sorted(tables)
    if tables[0] != 1:
        yield fail("First table index must start with 1!")


@describe(
    "Mappen for hver tabel skal indeholde en fil: table[fortløbende nummer]. xml, jf. dog 4. D. 5"
)
@categorize(ValidationType.TABLES)
def validate_4d3(ctx: ValidationContext) -> GenReport:
    tables = os.listdir(ctx.tables)

    for table in tables:
        table_content = os.listdir(ctx.tables / table)
        if f"{table}.xml" not in table_content:
            yield fail(f"{table}.xml is not in Tables dir!")

        table_content.remove(f"{table}.xml")
        table_content.remove(f"{table}.xsd")  # Not necessary!

        if not (len(table_content) == 0):
            yield fail(
                f"Cannot have more files than tablexxx.xml and tablexxx.xsd in {ctx.tables / table}"
            )


# 4d4 table[fortløbende nummber].xml er en XML instsans, der indeholder data for den pågældende tabel
# 4d5 Allerede med i 4d3
# 4d6 null felter
