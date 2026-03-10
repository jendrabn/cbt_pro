from __future__ import annotations

import os
import re

from django import forms

from .models import CertificateTemplate


HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _bootstrap_widget(field):
    if isinstance(field.widget, forms.CheckboxInput):
        css_class = "form-check-input"
    elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
        css_class = "form-select"
    elif isinstance(field.widget, forms.RadioSelect):
        css_class = "form-check-input"
    else:
        css_class = "form-control"
    current = field.widget.attrs.get("class", "")
    field.widget.attrs["class"] = f"{current} {css_class}".strip()


class CertificateTemplateForm(forms.ModelForm):
    background_image = forms.FileField(required=False)
    signatory_signature = forms.FileField(required=False)
    remove_background_image = forms.BooleanField(required=False)
    remove_signatory_signature = forms.BooleanField(required=False)

    class Meta:
        model = CertificateTemplate
        fields = [
            "template_name",
            "layout_preset",
            "layout_type",
            "paper_size",
            "primary_color",
            "secondary_color",
            "show_logo",
            "show_score",
            "show_grade",
            "show_rank",
            "show_qr_code",
            "qr_code_size",
            "header_text",
            "body_text_template",
            "footer_text",
            "signatory_name",
            "signatory_title",
        ]
        widgets = {
            "layout_preset": forms.Select(),
            "header_text": forms.Textarea(attrs={"rows": 2}),
            "body_text_template": forms.Textarea(attrs={"rows": 8}),
            "footer_text": forms.Textarea(attrs={"rows": 2}),
            "layout_type": forms.Select(),
            "paper_size": forms.Select(),
            "qr_code_size": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            _bootstrap_widget(field)

        switch_fields = [
            "show_logo",
            "show_score",
            "show_grade",
            "show_rank",
            "show_qr_code",
            "remove_background_image",
            "remove_signatory_signature",
        ]
        for name in switch_fields:
            self.fields[name].widget.attrs["role"] = "switch"

        self.fields["template_name"].widget.attrs.setdefault("placeholder", "Template Sertifikat UAS")
        self.fields["primary_color"].widget.attrs.setdefault("type", "color")
        self.fields["secondary_color"].widget.attrs.setdefault("type", "color")
        self.fields["body_text_template"].widget.attrs.setdefault(
            "placeholder",
            "Gunakan placeholder seperti {{ student_full_name }}, {{ exam_title }}, {{ final_score }}",
        )

    def clean_primary_color(self):
        value = (self.cleaned_data.get("primary_color") or "").strip()
        if not HEX_COLOR_PATTERN.match(value):
            raise forms.ValidationError("Primary color harus format HEX, contoh: #1A56DB")
        return value

    def clean_secondary_color(self):
        value = (self.cleaned_data.get("secondary_color") or "").strip()
        if not HEX_COLOR_PATTERN.match(value):
            raise forms.ValidationError("Secondary color harus format HEX, contoh: #0E9F6E")
        return value

    def clean_background_image(self):
        return self._validate_file("background_image", {"png", "jpg", "jpeg"}, 5 * 1024 * 1024)

    def clean_signatory_signature(self):
        return self._validate_file("signatory_signature", {"png", "jpg", "jpeg"}, 2 * 1024 * 1024)

    def clean(self):
        cleaned_data = super().clean()
        preset = (cleaned_data.get("layout_preset") or "").strip()
        if preset == CertificateTemplate.LayoutPreset.PORTRAIT_ACHIEVEMENT:
            cleaned_data["layout_type"] = CertificateTemplate.LayoutType.PORTRAIT
        elif preset in {
            CertificateTemplate.LayoutPreset.CLASSIC_FORMAL,
            CertificateTemplate.LayoutPreset.MODERN_MINIMAL,
        }:
            cleaned_data["layout_type"] = CertificateTemplate.LayoutType.LANDSCAPE
        return cleaned_data

    def _validate_file(self, field_name, allowed_ext, max_size):
        file_obj = self.cleaned_data.get(field_name)
        if not file_obj:
            return file_obj
        ext = os.path.splitext(str(file_obj.name or ""))[1].lower().replace(".", "")
        if ext not in allowed_ext:
            raise forms.ValidationError(f"Format file tidak valid. Gunakan: {', '.join(sorted(allowed_ext))}.")
        if int(getattr(file_obj, "size", 0) or 0) > max_size:
            raise forms.ValidationError("Ukuran file melebihi batas yang diizinkan.")
        return file_obj


class EssayManualGradingForm(forms.Form):
    action = forms.CharField()
    answer_id = forms.UUIDField()
    points_awarded = forms.DecimalField(min_value=0, max_digits=5, decimal_places=2)
    feedback = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def clean_action(self):
        value = (self.cleaned_data.get("action") or "").strip()
        if value != "grade_essay":
            raise forms.ValidationError("Aksi grading tidak valid.")
        return value

    def clean_feedback(self):
        return (self.cleaned_data.get("feedback") or "").strip()
