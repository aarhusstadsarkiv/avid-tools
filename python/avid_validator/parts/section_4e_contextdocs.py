import os
import re
from avid_validator.common.archive import ValidationContext, ValidationType
from avid_validator.common.description import register, describe
from avid_validator.common.report import GenReport, fail, ok


@describe(
    """Mappen ContextDocumentation skal indeholde en eller flere dokumentsamlingsmapper med kontekstdokumentation, jf. 6. B."""
)
@register(ValidationType.CONTEXTDOCS)
def validate_4e1(ctx: ValidationContext) -> GenReport:
    # Skal indeholde en eller flere dokumentsamlingsmapper med kontektsdokumenter
    min_req_doc = ctx.context_docs / "docCollection1" / "1" / "1.tif"

    if not min_req_doc.is_file():
        yield fail("Must at least have one context documentation!")


@describe("""En dokumentsamlingsmappe med kontekstdokumentation må indeholde op til 10.000 dokumentmapper.""")
@register(ValidationType.CONTEXTDOCS)
def validate_4e2(ctx: ValidationContext) -> GenReport:
    docCollections = os.listdir(ctx.context_docs)
    for doccol in docCollections:
        if not (len(os.listdir(ctx.context_docs / doccol)) <= 10_000):
            yield fail("Must have no more than 10000 files per docCollection")


@register(ValidationType.CONTEXTDOCS)
def validate_4e3(ctx: ValidationContext) -> GenReport:
    tables = [
        int(re.match(r"docCollection(\d+)$", table).group(1))  # pyright: ignore
        for table in os.listdir(ctx.context_docs)
    ]  # pyright: ignore
    tables = sorted(tables)

    # uniquenes
    if len(tables) != len(set(tables)):
        yield fail("docCollection names must be unique!")

    # start with 1
    if tables[0] != 1:
        yield fail("First table index must start with 1!")


# 4e4 Unikt ID?
@describe(
    """Dokumentsamlingsmapperne navngives »docCollection[fortløbende nummer]«, begyndende med 1. Navnet skal være unikt inden for ContextDocumentation."""
)
@register(ValidationType.CONTEXTDOCS)
def validate_4e5(ctx: ValidationContext) -> GenReport:
    # Skal indeholde en eller flere dokumentsamlingsmapper med kontektsdokumenter
    docs = os.listdir(ctx.context_docs / "docCollection1" / "1")

    if len(docs) != 1:
        yield fail("Must only be one document per docId!")
    else:
        yield ok()


@describe(
    """Et dokuments fil (eller filer) navngives fortløbende med et nummer, begyndende med 1 samt formatets ekstension, jf. 4.G.8"""
)
@register(ValidationType.CONTEXTDOCS)
def validate_4e6(ctx: ValidationContext) -> GenReport:
    docs = (ctx.context_docs / "docCollection1").glob("*")
    files = [file.stem for file in docs]
    for file in files:
        # raise error if not int! Must be an int!
        try:
            int(file)
        except:
            yield fail(f"Failed to parse int from {file}")
