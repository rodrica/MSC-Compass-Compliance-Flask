from .hydrator import (
    HydratorPostSchema,
)

from .department import (
    Department,
    DepartmentSchema,
    DepartmentPageableSchema,
    DepartmentListQueryParameters,
    DepartmentListQueryParametersSchema,
    DEPARTMENT_CLAIM_SPEC,
)
from .office import (
    Office,
    OfficeSchema,
    OfficePageableSchema,
    OfficeListQueryParameters,
    OfficeListQueryParametersSchema,
    OFFICE_CLAIM_SPEC,
)
from .role import (
    Role,
    RoleSchema,
    RolePageableSchema,
    RoleListQueryParameters,
    RoleListQueryParametersSchema,
    ROLE_CLAIM_SPEC,
)
from .tenant import (
    Tenant,
    TenantSchema,
    TenantPageableSchema,
    TenantListQueryParameters,
    TenantListQueryParametersSchema,
    TENANT_CLAIM_SPEC,
)
from .user import (
    User,
    UserSchema,
    UserPageableSchema,
    UserListQueryParameters,
    UserListQueryParametersSchema,
    PostUserSchema,
    PostUserChangePasswordSchema,
    UpdateUserSchema,
    USER_CLAIM_SPEC,
)

from .ui_data import (
    DashboardDataSchema,
)

ALL_CLAIM_SPECS = [
    DEPARTMENT_CLAIM_SPEC,
    OFFICE_CLAIM_SPEC,
    ROLE_CLAIM_SPEC,
    TENANT_CLAIM_SPEC,
    USER_CLAIM_SPEC,
]
