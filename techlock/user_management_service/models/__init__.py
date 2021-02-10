from .department import (
    DEPARTMENT_CLAIM_SPEC,
    Department,
    DepartmentListQueryParameters,
    DepartmentListQueryParametersSchema,
    DepartmentPageableSchema,
    DepartmentSchema,
)
from .hydrator import HydratorPostSchema
from .office import (
    OFFICE_CLAIM_SPEC,
    Office,
    OfficeListQueryParameters,
    OfficeListQueryParametersSchema,
    OfficePageableSchema,
    OfficeSchema,
)
from .role import (
    ROLE_CLAIM_SPEC,
    Role,
    RoleListQueryParameters,
    RoleListQueryParametersSchema,
    RolePageableSchema,
    RoleSchema,
)
from .tenant import (
    TENANT_CLAIM_SPEC,
    Tenant,
    TenantListQueryParameters,
    TenantListQueryParametersSchema,
    TenantPageableSchema,
    TenantSchema,
)
from .ui_data import DashboardDataSchema
from .user import (
    USER_CLAIM_SPEC,
    PostUserChangePasswordSchema,
    PostUserSchema,
    UpdateUserSchema,
    User,
    UserListQueryParameters,
    UserListQueryParametersSchema,
    UserPageableSchema,
    UserSchema,
)

ALL_CLAIM_SPECS = [
    DEPARTMENT_CLAIM_SPEC,
    OFFICE_CLAIM_SPEC,
    ROLE_CLAIM_SPEC,
    TENANT_CLAIM_SPEC,
    USER_CLAIM_SPEC,
]
