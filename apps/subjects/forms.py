from django import forms
from django.core.exceptions import ValidationError

from .models import Subject


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code", "description", "is_active"]
        labels = {
            "name": "Nama Mata Pelajaran",
            "code": "Kode",
            "description": "Deskripsi",
            "is_active": "Status Aktif",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            else:
                css_class = "form-control"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()

        self.fields["name"].widget.attrs["placeholder"] = "Contoh: Matematika"
        self.fields["code"].widget.attrs["placeholder"] = "Contoh: MTK"
        self.fields["description"].widget.attrs["placeholder"] = "Opsional"
        self.fields["code"].widget.attrs["style"] = "text-transform: uppercase;"

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise ValidationError("Nama mata pelajaran wajib diisi.")

        duplicate = Subject.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise ValidationError("Nama mata pelajaran sudah digunakan.")
        return name

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().upper()
        if not code:
            raise ValidationError("Kode mata pelajaran wajib diisi.")

        duplicate = Subject.objects.filter(code__iexact=code)
        if self.instance and self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise ValidationError("Kode mata pelajaran sudah digunakan.")
        return code

