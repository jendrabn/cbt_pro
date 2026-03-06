from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


def _bootstrap_widget(field):
    if isinstance(field.widget, forms.CheckboxInput):
        css_class = "form-check-input"
    elif isinstance(field.widget, forms.RadioSelect):
        css_class = ""
    else:
        css_class = "form-control"
    existing = field.widget.attrs.get("class", "")
    field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class BaseUserForm(forms.ModelForm):
    phone_number = forms.CharField(label="Nomor Telepon", max_length=20, required=False)
    teacher_id = forms.CharField(label="NIP", max_length=50, required=False)
    subject_specialization = forms.CharField(label="Spesialisasi Mata Pelajaran", max_length=100, required=False)
    student_id = forms.CharField(label="NIS", max_length=50, required=False)
    class_grade = forms.CharField(label="Kelas/Tingkat", max_length=50, required=False)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "username",
            "role",
            "is_active",
        ]
        labels = {
            "first_name": "Nama Depan",
            "last_name": "Nama Belakang",
            "email": "Email",
            "username": "Username",
            "role": "Role",
            "is_active": "Status Aktif",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            _bootstrap_widget(field)

        self.fields["role"].widget.attrs.update({"x-model": "role"})
        self.fields["first_name"].widget.attrs["placeholder"] = "Contoh: Budi"
        self.fields["last_name"].widget.attrs["placeholder"] = "Contoh: Santoso"
        self.fields["email"].widget.attrs["placeholder"] = "nama@email.com"
        self.fields["username"].widget.attrs["placeholder"] = "username"
        self.fields["phone_number"].widget.attrs["placeholder"] = "08xxxxxxxxxx"
        self.fields["teacher_id"].widget.attrs["placeholder"] = "Contoh: NIP-1001"
        self.fields["student_id"].widget.attrs["placeholder"] = "Contoh: NIS-2001"
        self.fields["subject_specialization"].widget.attrs["placeholder"] = "Contoh: Matematika"
        self.fields["class_grade"].widget.attrs["placeholder"] = "Contoh: XII IPA 1"

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        teacher_id = (cleaned_data.get("teacher_id") or "").strip()
        student_id = (cleaned_data.get("student_id") or "").strip()

        if role == "teacher" and not teacher_id:
            self.add_error("teacher_id", "NIP wajib diisi untuk role guru.")
        if role == "student" and not student_id:
            self.add_error("student_id", "NIS wajib diisi untuk role siswa.")

        if role == "teacher":
            cleaned_data["student_id"] = ""
            cleaned_data["class_grade"] = ""
        elif role == "student":
            cleaned_data["teacher_id"] = ""
            cleaned_data["subject_specialization"] = ""
        else:
            cleaned_data["teacher_id"] = ""
            cleaned_data["subject_specialization"] = ""
            cleaned_data["student_id"] = ""
            cleaned_data["class_grade"] = ""
        return cleaned_data


class UserCreateForm(BaseUserForm):
    password = forms.CharField(
        label="Password",
        required=True,
        strip=False,
        error_messages={"required": "Password wajib diisi."},
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "Masukkan password"}),
    )
    send_password_email = forms.BooleanField(
        label="Kirim password ke email pengguna",
        required=False,
        initial=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widget(self.fields["password"])
        self.fields["send_password_email"].widget.attrs["class"] = "form-check-input"

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error("password", exc)
        return cleaned_data


class UserEditForm(BaseUserForm):
    password = forms.CharField(
        label="Password",
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Kosongkan jika tidak ingin mengganti password",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widget(self.fields["password"])

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error("password", exc)
        return cleaned_data


class UserImportForm(forms.Form):
    import_file = forms.FileField(
        label="File Import",
        required=True,
    )
    role = forms.ChoiceField(
        label="Role User",
        choices=[("teacher", "Teacher"), ("student", "Student")],
        required=True,
    )
    send_credentials_email = forms.BooleanField(
        label="Kirim kredensial ke email masing-masing user setelah import",
        required=False,
        initial=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            _bootstrap_widget(field)
        self.fields["import_file"].widget.attrs.update({"accept": ".xlsx,.xls"})
        self.fields["send_credentials_email"].widget.attrs["class"] = "form-check-input"

    def clean_import_file(self):
        uploaded_file = self.cleaned_data.get("import_file")
        if not uploaded_file:
            raise ValidationError("File wajib diunggah.")

        filename = uploaded_file.name.lower()
        if not (filename.endswith(".xlsx") or filename.endswith(".xls")):
            raise ValidationError("File harus berformat .xlsx atau .xls.")

        max_size_kb = 5 * 1024
        if uploaded_file.size > max_size_kb * 1024:
            raise ValidationError(f"Ukuran file maksimal {max_size_kb // 1024} MB.")

        return uploaded_file
