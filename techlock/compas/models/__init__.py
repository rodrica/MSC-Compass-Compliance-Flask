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

from .audit import (
    AUDIT_CLAIM_SPEC,
    Audit,
    AuditListQueryParameters,
    AuditListQueryParametersSchema,
    AuditPageableSchema,
    AuditSchema,
)

from .audit_history import (
    AUDIT_HISTORY_CLAIM_SPEC,
    AuditHistory,
    AuditHistoryListQueryParameters,
    AuditHistoryListQueryParametersSchema,
    AuditHistoryPageableSchema,
    AuditHistorySchema,
)

from .audit_timeline import (
    AUDIT_TIMELINE_CLAIM_SPEC,
    AuditTimeline,
    AuditTimelineListQueryParameters,
    AuditTimelineListQueryParametersSchema,
    AuditTimelinePageableSchema,
    AuditTimelineSchema,
)

from .audit_response import (
    AUDIT_RESPONSE_CLAIM_SPEC,
    AuditResponse,
    AuditResponseListQueryParameters,
    AuditResponseListQueryParametersSchema,
    AuditResponsePageableSchema,
    AuditResponseSchema,
)

from .audit_response_history import (
    AUDIT_RESPONSE_HISTORY_CLAIM_SPEC,
    AuditResponseHistory,
    AuditResponseHistoryListQueryParameters,
    AuditResponseHistoryListQueryParametersSchema,
    AuditResponseHistoryPageableSchema,
    AuditResponseHistorySchema,
)

from .compliance import (
    COMPLIANCE_CLAIM_SPEC,
    Compliance,
    ComplianceListQueryParameters,
    ComplianceListQueryParametersSchema,
    CompliancePageableSchema,
    ComplianceSchema,
)

from .compliance_history import (
    COMPLIANCE_HISTORY_CLAIM_SPEC,
    ComplianceHistory,
    ComplianceHistoryListQueryParameters,
    ComplianceHistoryListQueryParametersSchema,
    ComplianceHistoryPageableSchema,
    ComplianceHistorySchema,
)

from .compliance_period import (
    COMPLIANCE_PERIOD_CLAIM_SPEC,
    CompliancePeriod,
    CompliancePeriodListQueryParameters,
    CompliancePeriodListQueryParametersSchema,
    CompliancePeriodPageableSchema,
    CompliancePeriodSchema,
)

from .compliance_timeline import (
    COMPLIANCE_TIMELINE_CLAIM_SPEC,
    ComplianceTimeline,
    ComplianceTimelineListQueryParameters,
    ComplianceTimelineListQueryParametersSchema,
    ComplianceTimelinePageableSchema,
    ComplianceTimelineSchema,
)

from .compliance_response import (
    COMPLIANCE_RESPONSE_CLAIM_SPEC,
    ComplianceResponse,
    ComplianceResponseListQueryParameters,
    ComplianceResponseListQueryParametersSchema,
    ComplianceResponsePageableSchema,
    ComplianceResponseSchema,
)

from .compliance_response_history import (
    COMPLIANCE_RESPONSE_HISTORY_CLAIM_SPEC,
    ComplianceResponseHistory,
    ComplianceResponseHistoryListQueryParameters,
    ComplianceResponseHistoryListQueryParametersSchema,
    ComplianceResponseHistoryPageableSchema,
    ComplianceResponseHistorySchema,
)

from .comment import (
    COMMENT_CLAIM_SPEC,
    Comment,
    CommentListQueryParameters,
    CommentListQueryParametersSchema,
    CommentPageableSchema,
    CommentSchema,
)

from .detail import (
    DETAIL_CLAIM_SPEC,
    Detail,
    DetailListQueryParameters,
    DetailListQueryParametersSchema,
    DetailPageableSchema,
    DetailSchema,
)

from .event import (
    EVENT_CLAIM_SPEC,
    Event,
    EventListQueryParameters,
    EventListQueryParametersSchema,
    EventPageableSchema,
    EventSchema,
)

from .journal import (
    JOURNAL_CLAIM_SPEC,
    Journal,
    JournalListQueryParameters,
    JournalListQueryParametersSchema,
    JournalPageableSchema,
    JournalSchema,
)

ALL_CLAIM_SPECS = [
    AUDIT_CLAIM_SPEC,
    AUDIT_HISTORY_CLAIM_SPEC,
    AUDIT_RESPONSE_CLAIM_SPEC,
    AUDIT_RESPONSE_HISTORY_CLAIM_SPEC,
    AUDIT_TIMELINE_CLAIM_SPEC,
    COMMENT_CLAIM_SPEC,
    COMPLIANCE_CLAIM_SPEC,
    COMPLIANCE_HISTORY_CLAIM_SPEC,
    COMPLIANCE_PERIOD_CLAIM_SPEC,
    COMPLIANCE_RESPONSE_CLAIM_SPEC,
    COMPLIANCE_RESPONSE_HISTORY_CLAIM_SPEC,
    COMPLIANCE_TASK_CLAIM_SPEC,
    COMPLIANCE_TIMELINE_CLAIM_SPEC,
    DETAIL_CLAIM_SPEC,
    EVENT_CLAIM_SPEC,
    JOURNAL_CLAIM_SPEC,
    REPORT_CLAIM_SPEC,
    REPORT_INSTRUCTION_CLAIM_SPEC,
    REPORT_NODE_CLAIM_SPEC,
    REPORT_VERSION_CLAIM_SPEC
]
