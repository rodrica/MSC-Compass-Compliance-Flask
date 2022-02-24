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

from .report_instruction import (
    REPORT_INSTRUCTION_CLAIM_SPEC,
    ReportInstruction,
    ReportInstructionListQueryParameters,
    ReportInstructionListQueryParametersSchema,
    ReportInstructionPageableSchema,
    ReportInstructionSchema,
)

from .compliance_task import (
    COMPLIANCE_TASK_CLAIM_SPEC,
    ComplianceTask,
    ComplianceTaskListQueryParameters,
    ComplianceTaskListQueryParametersSchema,
    ComplianceTaskPageableSchema,
    ComplianceTaskSchema,
)

ALL_CLAIM_SPECS = [
    COMPLIANCE_TASK_CLAIM_SPEC,
    REPORT_CLAIM_SPEC,
    REPORT_INSTRUCTION_CLAIM_SPEC,
    REPORT_NODE_CLAIM_SPEC,
    REPORT_VERSION_CLAIM_SPEC
]
