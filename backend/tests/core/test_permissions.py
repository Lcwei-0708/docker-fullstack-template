from core.permissions import Permission, get_attributes


class TestPermission:
    def test_permission_values_and_metadata(self):
        assert Permission.VIEW_USERS.value == "view-users"
        assert Permission.VIEW_USERS.group == "system-management"
        assert Permission.VIEW_USERS.category == "user-management"
        assert Permission.MANAGE_ROLES.value == "manage-roles"
        assert Permission.MANAGE_ROLES.category == "role-management"


class TestGetAttributes:
    def test_get_attributes_covers_all_permissions(self):
        attributes = get_attributes()
        names = {item["name"] for item in attributes}
        assert names == {permission.value for permission in Permission}
        view_users = next(item for item in attributes if item["name"] == "view-users")
        assert view_users["group"] == "system-management"
        assert view_users["category"] == "user-management"
