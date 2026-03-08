from __future__ import annotations

from html import unescape

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.html import strip_tags

from apps.subjects.models import Subject

from .models import Question, QuestionAnswer, QuestionCategory, QuestionOption, QuestionTagRelation


OPTION_LETTERS = [choice.value for choice in QuestionOption.OptionLetter]


def _bootstrap_widget(field):
    if isinstance(field.widget, forms.CheckboxInput):
        css_class = "form-check-input"
    elif isinstance(field.widget, forms.RadioSelect):
        css_class = "form-check-input"
    else:
        css_class = "form-control"
    existing = field.widget.attrs.get("class", "")
    field.widget.attrs["class"] = f"{existing} {css_class}".strip()


def _is_empty_rich_text(value):
    plain_text = strip_tags(value or "")
    plain_text = unescape(plain_text).replace("\xa0", " ").strip()
    return not plain_text


class QuestionForm(forms.ModelForm):
    category_name = forms.CharField(
        label="Kategori Baru",
        required=False,
        max_length=100,
        help_text="Isi jika ingin membuat kategori baru.",
    )
    tags = forms.CharField(
        label="Tag (Pisahkan dengan koma)",
        required=False,
        help_text="Contoh: aljabar, persamaan, kelas-12",
    )
    question_image = forms.FileField(
        label="Unggah Gambar Soal",
        required=False,
    )

    option_a = forms.CharField(label="Opsi A", required=False)
    option_b = forms.CharField(label="Opsi B", required=False)
    option_c = forms.CharField(label="Opsi C", required=False)
    option_d = forms.CharField(label="Opsi D", required=False)
    option_e = forms.CharField(label="Opsi E", required=False)
    correct_option = forms.ChoiceField(
        label="Jawaban Benar",
        required=False,
        choices=[(letter, letter) for letter in OPTION_LETTERS],
        widget=forms.RadioSelect,
    )

    answer_text = forms.CharField(
        label="Kunci Jawaban / Rubrik",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    keywords = forms.CharField(
        label="Kata Kunci",
        required=False,
        help_text="Pisahkan kata kunci dengan koma.",
    )
    is_case_sensitive = forms.BooleanField(
        label="Peka Huruf Besar/Kecil (Jawaban Singkat)",
        required=False,
    )
    max_word_count = forms.IntegerField(
        label="Batas Maksimal Kata",
        required=False,
        min_value=1,
    )

    class Meta:
        model = Question
        fields = [
            "subject",
            "category",
            "question_type",
            "question_text",
            "points",
            "difficulty_level",
            "explanation",
            "allow_previous",
            "allow_next",
            "force_sequential",
            "time_limit_seconds",
            "is_active",
        ]
        labels = {
            "subject": "Mata Pelajaran",
            "category": "Kategori",
            "question_type": "Tipe Soal",
            "question_text": "Teks Soal",
            "points": "Bobot Nilai",
            "difficulty_level": "Tingkat Kesulitan",
            "explanation": "Pembahasan",
            "allow_previous": "Izinkan Kembali ke Soal Sebelumnya",
            "allow_next": "Izinkan Lanjut ke Soal Berikutnya",
            "force_sequential": "Paksa Urutan Berurutan",
            "time_limit_seconds": "Batas Waktu per Soal (detik, opsional)",
            "is_active": "Status Aktif",
        }
        widgets = {
            "question_text": forms.Textarea(attrs={"rows": 6}),
            "explanation": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        subject_queryset = Subject.objects.filter(is_active=True).only("id", "name")
        if self.instance and self.instance.pk and self.instance.subject_id:
            subject_queryset = Subject.objects.filter(Q(is_active=True) | Q(id=self.instance.subject_id)).only("id", "name")
        self.fields["subject"].queryset = subject_queryset.order_by("name")
        self.fields["category"].queryset = QuestionCategory.objects.filter(is_active=True).only("id", "name").order_by("name")
        self.fields["question_type"].choices = [
            ("multiple_choice", "Pilihan Ganda"),
            ("essay", "Esai"),
            ("short_answer", "Jawaban Singkat"),
        ]
        self.fields["difficulty_level"].choices = [
            ("", "---------"),
            ("easy", "Mudah"),
            ("medium", "Sedang"),
            ("hard", "Sulit"),
        ]

        for field in self.fields.values():
            _bootstrap_widget(field)

        for name in ["option_a", "option_b", "option_c", "option_d", "option_e"]:
            self.fields[name].widget = forms.Textarea(attrs={"rows": 2, "class": "form-control option-input"})

        # TinyMCE menyembunyikan textarea asli. Required native HTML5 pada elemen
        # tersembunyi bisa memicu "invalid form control is not focusable".
        self.fields["question_text"].required = False

        self.fields["question_text"].widget.attrs["placeholder"] = "Tulis soal di sini..."
        self.fields["explanation"].widget.attrs["placeholder"] = "Pembahasan / penjelasan tambahan..."
        self.fields["category_name"].widget.attrs["placeholder"] = "Contoh: Trigonometri Dasar"
        self.fields["tags"].widget.attrs["placeholder"] = "contoh: aljabar, persamaan"
        self.fields["keywords"].widget.attrs["placeholder"] = "contoh: variabel, koefisien"

        if self.instance and self.instance.pk and not self.instance._state.adding:
            options = {opt.option_letter: opt for opt in self.instance.options.all()}
            for letter in OPTION_LETTERS:
                field_name = f"option_{letter.lower()}"
                self.fields[field_name].initial = options.get(letter).option_text if letter in options else ""
                if letter in options and options[letter].is_correct:
                    self.fields["correct_option"].initial = letter

            answer = QuestionAnswer.objects.filter(question=self.instance).first()
            if answer:
                self.fields["answer_text"].initial = answer.answer_text
                self.fields["keywords"].initial = ", ".join(answer.keywords or [])
                self.fields["is_case_sensitive"].initial = answer.is_case_sensitive
                self.fields["max_word_count"].initial = answer.max_word_count

            tags = (
                QuestionTagRelation.objects.filter(question=self.instance)
                .select_related("tag")
                .values_list("tag__name", flat=True)
            )
            self.fields["tags"].initial = ", ".join(tags)

    def clean_question_image(self):
        file_obj = self.cleaned_data.get("question_image")
        if not file_obj:
            return file_obj
        lower_name = file_obj.name.lower()
        allowed_ext = (".png", ".jpg", ".jpeg", ".webp", ".gif")
        if not lower_name.endswith(allowed_ext):
            raise ValidationError("Format gambar tidak didukung. Gunakan PNG/JPG/JPEG/WEBP/GIF.")
        max_size = 5 * 1024 * 1024
        if file_obj.size > max_size:
            raise ValidationError("Ukuran gambar maksimal 5MB.")
        return file_obj

    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get("question_type")
        question_text = (cleaned_data.get("question_text") or "").strip()

        option_map = {
            "A": (cleaned_data.get("option_a") or "").strip(),
            "B": (cleaned_data.get("option_b") or "").strip(),
            "C": (cleaned_data.get("option_c") or "").strip(),
            "D": (cleaned_data.get("option_d") or "").strip(),
            "E": (cleaned_data.get("option_e") or "").strip(),
        }
        active_options = {letter: text for letter, text in option_map.items() if text}
        correct_option = cleaned_data.get("correct_option")
        answer_text = (cleaned_data.get("answer_text") or "").strip()
        time_limit = cleaned_data.get("time_limit_seconds")

        if time_limit is not None and time_limit <= 0:
            self.add_error("time_limit_seconds", "Batas waktu per soal harus lebih dari 0.")

        if _is_empty_rich_text(question_text):
            self.add_error("question_text", "Teks soal wajib diisi.")
        else:
            cleaned_data["question_text"] = question_text

        if question_type == "multiple_choice":
            if len(active_options) < 2:
                self.add_error("option_b", "Minimal isi dua opsi untuk soal pilihan ganda.")
            if not correct_option:
                self.add_error("correct_option", "Pilih jawaban benar untuk soal pilihan ganda.")
            elif correct_option not in active_options:
                self.add_error("correct_option", "Jawaban benar harus berasal dari opsi yang terisi.")
            cleaned_data["answer_text"] = ""
            cleaned_data["keywords"] = ""
            cleaned_data["is_case_sensitive"] = False
            cleaned_data["max_word_count"] = None
        else:
            if not answer_text:
                self.add_error("answer_text", "Kunci jawaban / rubrik wajib diisi.")
            cleaned_data["correct_option"] = ""

        if cleaned_data.get("force_sequential"):
            cleaned_data["allow_previous"] = False

        category_name = (cleaned_data.get("category_name") or "").strip()
        if category_name:
            category = QuestionCategory.objects.filter(name__iexact=category_name).first()
            if category:
                if not category.is_active:
                    category.is_active = True
                    category.save(update_fields=["is_active"])
            else:
                category = QuestionCategory.objects.create(name=category_name, is_active=True)
            cleaned_data["category"] = category

        return cleaned_data


class QuestionImportForm(forms.Form):
    import_file = forms.FileField(label="File Impor (Excel)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widget(self.fields["import_file"])
        self.fields["import_file"].widget.attrs.update({"accept": ".xlsx"})

    def clean_import_file(self):
        file_obj = self.cleaned_data.get("import_file")
        if not file_obj:
            return file_obj
        lower_name = file_obj.name.lower()
        allowed_ext = (".xlsx",)
        if not lower_name.endswith(allowed_ext):
            raise ValidationError("File harus berformat .xlsx.")
        max_size = 10 * 1024 * 1024
        if file_obj.size > max_size:
            raise ValidationError("Ukuran file import maksimal 10MB.")
        return file_obj
