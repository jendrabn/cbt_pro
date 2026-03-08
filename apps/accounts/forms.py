from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import UserProfile

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email/Username",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan email atau username",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan password",
                "autocomplete": "current-password",
            }
        ),
    )
    remember_me = forms.BooleanField(
        label="Ingat Saya",
        required=False,
        initial=False,
    )

    error_messages = {
        "invalid_login": _(
            "Email/username atau password salah. Silakan periksa kembali."
        ),
        "inactive": _("Akun ini tidak aktif. Hubungi admin."),
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if getattr(user, "is_deleted", False):
            raise ValidationError(
                _("Akun ini tidak dapat digunakan. Hubungi admin."),
                code="deleted",
            )


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nama Depan",
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Masukkan nama depan"}
        ),
    )
    last_name = forms.CharField(
        label="Nama Belakang",
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Masukkan nama belakang"}
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Masukkan email"}
        ),
    )
    phone_number = forms.CharField(
        label="Nomor Telepon",
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Masukkan nomor telepon"}
        ),
    )
    bio = forms.CharField(
        label="Bio",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 3, "placeholder": "Tentang Anda..."}
        ),
    )

    class Meta:
        model = UserProfile
        fields = ["phone_number", "bio"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["first_name"].initial = self.user.first_name
            self.fields["last_name"].initial = self.user.last_name
            self.fields["email"].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data.get("first_name", "")
            self.user.last_name = self.cleaned_data.get("last_name", "")
            self.user.email = self.cleaned_data.get("email", "")
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile


class AvatarUploadForm(forms.ModelForm):
    profile_picture = forms.ImageField(
        label="Foto Profil",
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
    )

    class Meta:
        model = UserProfile
        fields = ["profile_picture"]

    def clean_profile_picture(self):
        image = self.cleaned_data.get("profile_picture")
        if image:
            if image.size > 2 * 1024 * 1024:
                raise ValidationError("Ukuran file maksimal 2MB.")
            allowed_types = ["image/jpeg", "image/png", "image/gif"]
            if image.content_type not in allowed_types:
                raise ValidationError("Format file harus JPG, PNG, atau GIF.")
        return image


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Password Lama",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan password lama",
                "autocomplete": "current-password",
            }
        ),
    )
    new_password1 = forms.CharField(
        label="Password Baru",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan password baru",
                "autocomplete": "new-password",
            }
        ),
        )


class RoleRegistrationForm(UserCreationForm):
    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username unik (tanpa spasi)",
                "autocomplete": "username",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email aktif",
                "autocomplete": "email",
            }
        ),
    )
    first_name = forms.CharField(
        label="Nama Depan",
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nama depan"},
        ),
    )
    last_name = forms.CharField(
        label="Nama Belakang",
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nama belakang"},
        ),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Buat password",
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Konfirmasi Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ulangi password",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email sudah terdaftar.")
        return email
    new_password2 = forms.CharField(
        label="Konfirmasi Password Baru",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Konfirmasi password baru",
                "autocomplete": "new-password",
            }
        ),
    )
