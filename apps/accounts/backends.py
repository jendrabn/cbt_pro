from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import User


class UsernameOrEmailBackend(ModelBackend):
    """
    Authenticate user with either username or email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        login_value = username or kwargs.get(User.USERNAME_FIELD)
        if not login_value or not password:
            return None

        login_value = login_value.strip()

        try:
            user = User.objects.get(
                Q(username__iexact=login_value) | Q(email__iexact=login_value),
                is_deleted=False,
            )
        except User.DoesNotExist:
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id, is_deleted=False)
        except User.DoesNotExist:
            return None
