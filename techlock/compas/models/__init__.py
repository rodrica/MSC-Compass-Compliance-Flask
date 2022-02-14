from .hydrator import HydratorPostSchema
from .role import (
    ROLE_CLAIM_SPEC,
    Role,
    RoleListQueryParameters,
    RoleListQueryParametersSchema,
    RolePageableSchema,
    RoleSchema,
)
from .ui_data import DashboardDataSchema
from .user import (
    USER_CLAIM_SPEC,
    PostUserChangePasswordSchema,
    UpdateUserSchema,
    User,
    UserListQueryParameters,
    UserListQueryParametersSchema,
    UserPageableSchema,
    UserSchema,
)

ALL_CLAIM_SPECS = [
    ROLE_CLAIM_SPEC,
    USER_CLAIM_SPEC,
]
