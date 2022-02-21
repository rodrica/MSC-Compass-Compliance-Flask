from .report import (
    REPORT_CLAIM_SPEC,
    Report,
    ReportListQueryParameters,
    ReportListQueryParametersSchema,
    ReportPageableSchema,
    ReportSchema,
)
from .report_version import (
    REPORT_VERSION_CLAIM_SPEC,
    ReportVersion,
    ReportVersionListQueryParameters,
    ReportVersionListQueryParametersSchema,
    ReportVersionPageableSchema,
    ReportVersionSchema,
)

ALL_CLAIM_SPECS = [
    REPORT_CLAIM_SPEC,
    REPORT_VERSION_CLAIM_SPEC
]
