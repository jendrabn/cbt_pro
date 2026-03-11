from __future__ import annotations

import re

from django import forms


class MarketingContactForm(forms.Form):
    full_name = forms.CharField(
        label="Nama lengkap",
        max_length=120,
    )
    school_name = forms.CharField(
        label="Nama sekolah atau lembaga",
        max_length=160,
    )
    email = forms.EmailField(
        label="Email aktif",
        max_length=160,
    )
    whatsapp = forms.CharField(
        label="Nomor WhatsApp",
        max_length=30,
    )
    message = forms.CharField(
        label="Ceritakan kebutuhan Anda",
        widget=forms.Textarea,
        max_length=1200,
    )
    consent = forms.BooleanField(
        label="Saya bersedia dihubungi untuk konsultasi dan demo CBT Pro.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_classes = "form-control form-control-lg marketing-input"
        self.fields["full_name"].widget.attrs.update(
            {
                "class": field_classes,
                "placeholder": "Nama PIC sekolah",
                "autocomplete": "name",
            }
        )
        self.fields["school_name"].widget.attrs.update(
            {
                "class": field_classes,
                "placeholder": "SMK, SMA, MA, bimbel, atau lembaga kursus",
                "autocomplete": "organization",
            }
        )
        self.fields["email"].widget.attrs.update(
            {
                "class": field_classes,
                "placeholder": "nama@sekolah.sch.id",
                "autocomplete": "email",
            }
        )
        self.fields["whatsapp"].widget.attrs.update(
            {
                "class": field_classes,
                "placeholder": "08xxxxxxxxxx atau 628xxxxxxxxxx",
                "autocomplete": "tel",
                "inputmode": "tel",
            }
        )
        self.fields["message"].widget.attrs.update(
            {
                "class": f"{field_classes} marketing-textarea",
                "placeholder": "Contoh: kami ingin ujian untuk 300 siswa serentak dengan randomisasi soal dan hasil otomatis.",
                "rows": 6,
            }
        )
        self.fields["consent"].widget.attrs.update({"class": "form-check-input"})

    def clean_whatsapp(self):
        raw_value = self.cleaned_data["whatsapp"]
        digits = re.sub(r"\D", "", raw_value or "")
        if digits.startswith("0"):
            digits = f"62{digits[1:]}"
        if len(digits) < 10 or len(digits) > 15:
            raise forms.ValidationError("Masukkan nomor WhatsApp yang valid.")
        return digits

    def clean_message(self):
        value = " ".join((self.cleaned_data["message"] or "").split())
        if len(value) < 20:
            raise forms.ValidationError("Pesan minimal 20 karakter agar kebutuhan Anda jelas.")
        return value
