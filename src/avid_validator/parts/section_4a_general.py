from avid_validator.common.archive import ValidationContext
from avid_validator.common.report import GenReport
from avid_validator.common.rules import require_name_startswith


def validate_4ba(ctx: ValidationContext) -> GenReport:
    yield require_name_startswith(ctx.root, "AVID.", "Does not start with 'AVID.'!")
