from dataclasses import dataclass


@dataclass
class AuthInfo:
    user_id: str
    tenant_id: str
