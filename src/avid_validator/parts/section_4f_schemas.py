import hashlib
import os
from pathlib import Path
import tempfile
import zipfile

import requests
from avid_validator.common.archive import ValidationContext, ValidationType
from avid_validator.common.description import register, describe
from avid_validator.common.report import GenReport, fail


@describe(
    """Mappen Schemas skal være opdelt i undermapperne standard og localShared."""
)
@register(ValidationType.SCHEMAS)
def validate_4f1(ctx: ValidationContext) -> GenReport:
    if not (ctx.schemas / "standard").is_dir():
        yield fail("Indices/standard is not a directory!")
    if not (ctx.schemas / "localShared").is_dir():
        yield fail("Indices/localShared is not a directory!")


@describe(
    """Mappen standard skal indeholde skemaer for arkiveringsversionens indeksfiler,
jf. bilag 8, samt W3C standard XML-skema, jf. http://www.w3. org/2001/XMLSchema.xsd."""
)
@register(ValidationType.SCHEMAS)
def validate_4f2(ctx: ValidationContext) -> GenReport:
    # Indeholde indeksfiler
    req_filer = ["archiveIndex", "tableIndex", "docIndex", "fileIndex"]
    index_files = [file.stem for file in (ctx.schemas / "standard").glob("*")]

    if len(index_files) == 0:
        yield fail("No index files found!")

    for req_file in req_filer:
        if req_file not in index_files:
            yield fail(f"Index file, {req_file}, missing!")


@describe(
    """For skemaerne fileIndex.xsd, archiveIndex.xsd, contextDocumentationIndex.xsd, tableIndex.xsd,
docIndex.xsd, researchIndex.xsd samt W3Cs standard XML-skema gælder, at der altid skal anvendes de skemaer,
som Rigsarkivet stiller til rådighed. Skemaerne og deres navngivning må ikke ændres i arkiveringsversionen."""
)
@register(ValidationType.SCHEMAS)
def validate_4f3(ctx: ValidationContext) -> GenReport:
    schemas_url = "https://www.rigsarkivet.dk/wp-content/uploads/2022/02/Schemas.zip"

    with tempfile.TemporaryDirectory() as tmpdir:
        schemas_zip_path = os.path.join(tmpdir, "schemas.zip")
        extract_path = tmpdir
        with open(schemas_zip_path, "wb") as schemas_f:
            response = requests.get(schemas_url)
            schemas_f.write(response.content)

        schemas_zip = zipfile.ZipFile(schemas_zip_path)
        schemas_zip.extractall(extract_path)

        rigsarkiv_schemas_path = Path(extract_path + "/Schemas/standard")

        for archive_schema in ctx.schemas.joinpath("standard").glob("*.xsd"):
            archive_schema_hash = hashlib.md5(archive_schema.read_bytes()).hexdigest()
            downloaded_schema_hash = hashlib.md5(
                rigsarkiv_schemas_path.joinpath(archive_schema.name).read_bytes()
            ).hexdigest()

            if not archive_schema_hash == downloaded_schema_hash:
                yield fail(f"{archive_schema} does not match Rigsarkivets schemas!")
