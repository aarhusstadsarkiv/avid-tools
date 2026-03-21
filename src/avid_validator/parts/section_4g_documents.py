import os
import re

from tqdm import tqdm
from avid_validator.common.archive import ValidationContext, ValidationType, XMLIndices
from avid_validator.common.description import register, describe
from avid_validator.common.report import GenReport, fail


@describe(
    """Mappen Documents skal indeholde én eller flere dokumentsamlingsmapper, dog maksimalt 10.000."""
)
@register(ValidationType.DOCS)
def validate_4g1(ctx: ValidationContext) -> GenReport:
    doc_count = len(os.listdir(ctx.documents))

    if doc_count == 0:
        yield fail("Must be at least one document!")

    if doc_count > 10_000:
        yield fail("The documents folder not contain more 10000 document collection folders!")


@describe("""Dokumentsamlingsmapperne navngives »docCollection[fortløbende nummer]«,
begyndende med 1. Navnet skal være unikt inden for Documents.""")
@register(ValidationType.DOCS)
def validate_4g2(ctx: ValidationContext) -> GenReport:
    tables = [
        int(re.match(r"docCollection(\d+)$", table).group(1))  # pyright: ignore
        for table in os.listdir(ctx.documents)
    ]
    tables = sorted(tables)

    # uniquenes
    if not len(tables) == len(set(tables)):
        yield fail("docCollection names must be unique!")

    # start with 1
    if not tables[0] == 1:
        yield fail("First table index must start with 1!")


@describe("""En dokumentsamlingsmappe må indeholde op til 10.000 dokumentmapper.""")
@register(ValidationType.DOCS)
def validate_4g3(ctx: ValidationContext) -> GenReport:
    docCollections = os.listdir(ctx.documents)
    for doccol in docCollections:
        if not (len(os.listdir(ctx.documents / doccol)) <= 10_000):
            yield fail("Must have no more than 10000 files per docCollection")


# 4g4 Tildeles et ID på op til 12 cifre
# 4g5 Dokumentmappe skal indeholde et dokument som består af en eller flere filer af samme format, og navngives med dokumentets ID.
# 4g6 Et dokuments fil (eller filer) navngives fortløbende med et nummer, begyndende med 1 samt formatets ekstension. Foranstillede nuller må ikke anvendes.
# 4g7 For GML-filer lagres det relevante skema i samme mappe som GML-filen, og navngives med fortløbende nummer efterfulgt af . xsd, jf. dog 4. G. 7.a. Foranstillede nuller må ikke anvendes.
# 4g7a GML-skemaer kan alternativt lagres i den skema-mappe, som navngives localShared, jf. 4. F. GML-skemaer i mappen localShared navngives »localSchema[fortløbende nummer]«, begyndende med 1.


@describe("""Anvendelse af ekstensions""")
def validate_4g8(ctx: ValidationContext) -> GenReport:
    allowed_extensions = {".tif", ".mp3", ".mpg", ".jp2", ".gml", ".wav"}
    files = ctx.documents.rglob("*.*")

    for file in tqdm(files):
        if file.suffix not in allowed_extensions:
            yield fail(f"File {file} does not have an allowed extension!")

