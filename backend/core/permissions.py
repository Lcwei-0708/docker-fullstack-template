from enum import Enum
from typing import List, Dict, Optional

class Permission(Enum):
    """Attributes for roles"""

    # User management attributes
    VIEW_USERS = ("view-users", "system-management", "user-management")
    MANAGE_USERS = ("manage-users", "system-management", "user-management")
    
    # Role management attributes
    VIEW_ROLES = ("view-roles", "system-management", "role-management")
    MANAGE_ROLES = ("manage-roles", "system-management", "role-management")
    
    def __init__(
        self,
        value: str,
        group: Optional[str] = None,
        category: Optional[str] = None,
    ):
        self._value_ = value
        self.group = group
        self.category = category
    
    def __str__(self) -> str:
        """Return string value of Permission.VIEW_USERS"""
        return self.value

def get_attributes() -> List[Dict[str, str]]:
    """Get default role attributes configuration"""
    return [
        {
            "name": permission.value,
            "group": getattr(permission, "group", None),
            "category": getattr(permission, "category", None)
        }
        for permission in Permission
    ]