from avid_validator.common.archive import ValidationContext, ValidationType
from avid_validator.common.description import categorize, describe
from avid_validator.common.report import GenReport
from avid_validator.common.rules import require_dirs, require_name_startswith

ALL_CATEGORIES = (
    ValidationType.CONTEXTDOCS,
    ValidationType.DOCS,
    ValidationType.INDICES,
    ValidationType.SCHEMAS,
    ValidationType.TABLES,
)


@describe("Mapperne skal navngives som angivet i figur 4.1.")
@categorize(ALL_CATEGORIES)
def validate_4b3(ctx: ValidationContext) -> GenReport:
    yield require_dirs(
        ctx, "Indices", "Tables", "ContextDocumentation", "Schemas", "Documents"
    )


@describe(
    "Et arkiveringsversionsID består af præfikset AVID, en kode på 2-4 bogstaver (som angiver det modtagende arkiv), samt et arkiveringsversionsløbenummer. Elementerne adskilles med punktum."
)
@categorize(ALL_CATEGORIES)
def validate_4b4a(ctx: ValidationContext) -> GenReport:
    yield require_name_startswith(ctx.root, "AVID.", "Does not start with 'AVID.'!")
