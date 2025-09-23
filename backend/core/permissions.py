from enum import Enum
from typing import List, Dict

class Permission(Enum):
    """Attributes for roles"""
    # User management attributes
    VIEW_USERS = ("view-users", "Permission to view user information")
    MANAGE_USERS = ("manage-users", "Permission to manage users")
    
    # Role management attributes
    VIEW_ROLES = ("view-roles", "Permission to view role information")
    MANAGE_ROLES = ("manage-roles", "Permission to manage roles and role attributes")
    
    def __init__(self, value: str, description: str):
        self._value_ = value
        self.description = description
    
    def __str__(self) -> str:
        """Return string value of Permission.VIEW_USERS"""
        return self.value

def get_attributes() -> List[Dict[str, str]]:
    """Get default role attributes configuration"""
    return [
        {
            "name": permission.value,
            "description": permission.description
        }
        for permission in Permission
    ]