from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


class UsernameOrEmailBackend(ModelBackend):
    """
    Authenticate user with either username or email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        login_value = username or kwargs.get(User.USERNAME_FIELD)
        if not login_value or not password:
            return None

        login_value = login_value.strip()

        user_queryset = User._default_manager.filter(
            Q(username__iexact=login_value) | Q(email__iexact=login_value)
        )
        if hasattr(User, "is_deleted"):
            user_queryset = user_queryset.filter(is_deleted=False)

        try:
            user = user_queryset.get()
        except User.DoesNotExist:
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            queryset = User._default_manager.filter(pk=user_id)
            if hasattr(User, "is_deleted"):
                queryset = queryset.filter(is_deleted=False)
            return queryset.get()
        except User.DoesNotExist:
            return None
