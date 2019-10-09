from .hydrator import (
    HydratorPostSchema,
)

from .department import (
    Department,
    DepartmentSchema,
    DepartmentPageableSchema,
    DEPARTMENT_CLAIM_SPEC,
)
from .office import (
    Office,
    OfficeSchema,
    OfficePageableSchema,
    OFFICE_CLAIM_SPEC,
)
from .role import (
    Role,
    RoleSchema,
    RolePageableSchema,
    ROLE_CLAIM_SPEC,
)
from .tenant import (
    Tenant,
    TenantSchema,
    TenantPageableSchema,
    TENANT_CLAIM_SPEC,
)
from .user import (
    User,
    UserSchema,
    UserPageableSchema,
    PostUserSchema,
    USER_CLAIM_SPEC,
)

ALL_CLAIM_SPECS = [
    DEPARTMENT_CLAIM_SPEC,
    OFFICE_CLAIM_SPEC,
    ROLE_CLAIM_SPEC,
    TENANT_CLAIM_SPEC,
    USER_CLAIM_SPEC,
]
