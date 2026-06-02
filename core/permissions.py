from rest_framework.permissions import BasePermission

from apps.accounts.models import UserRole


class IsAdminUser(BasePermission):
    message = "Only administrators may perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.ADMIN)


class IsWarehouseManagerOrAdmin(BasePermission):
    message = "Only warehouse managers or administrators may perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in {UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER}
        )


class IsProcurementManagerOrAdmin(BasePermission):
    message = "Only procurement managers or administrators may perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in {UserRole.ADMIN, UserRole.PROCUREMENT_MANAGER}
        )


class IsWarehouseManagerOrAdminOrStaff(BasePermission):
    message = "Only warehouse managers, staff, or administrators may perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in {UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER, UserRole.STAFF}
        )


class IsOwnerOrAdmin(BasePermission):
    message = "Only the owner or an administrator may access this object."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == UserRole.ADMIN:
            return True
        for field_name in ("created_by", "performed_by"):
            owner = getattr(obj, field_name, None)
            if owner and owner == request.user:
                return True
        return False

