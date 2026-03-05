from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Role-based access control for class-based views.

    - Anonymous users are redirected to LOGIN_URL.
    - Authenticated users with wrong role get HTTP 403 (PermissionDenied).
    """

    required_role = None
    required_roles = None
    permission_denied_message = "Anda tidak memiliki izin untuk mengakses halaman ini."

    def get_required_roles(self):
        if self.required_roles:
            return tuple(self.required_roles)
        if self.required_role:
            return (self.required_role,)
        raise ImproperlyConfigured(
            f"{self.__class__.__name__} harus mendefinisikan `required_role` "
            "atau `required_roles`."
        )

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if getattr(user, "is_deleted", False):
            return False
        return getattr(user, "role", None) in self.get_required_roles()

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied(self.permission_denied_message)
        return super().handle_no_permission()
