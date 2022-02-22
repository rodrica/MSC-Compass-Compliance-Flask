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

from .report_node import (
    REPORT_NODE_CLAIM_SPEC,
    ReportNode,
    ReportNodeListQueryParameters,
    ReportNodeListQueryParametersSchema,
    ReportNodePageableSchema,
    ReportNodeSchema,
)

ALL_CLAIM_SPECS = [
    REPORT_CLAIM_SPEC,
    REPORT_NODE_CLAIM_SPEC,
    REPORT_VERSION_CLAIM_SPEC
]
