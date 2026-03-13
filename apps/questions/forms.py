from __future__ import annotations

import re
from html import unescape

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.html import strip_tags

from apps.subjects.models import Subject

from .models import Question, QuestionAnswer, QuestionCategory, QuestionOption, QuestionTagRelation


OPTION_LETTERS = [choice.value for choice in QuestionOption.OptionLetter]
DEFAULT_OPTION_LETTERS = OPTION_LETTERS[:2]
ORDERING_ITEM_INDEXES = tuple(range(1, 11))
DEFAULT_ORDERING_ITEM_INDEXES = ORDERING_ITEM_INDEXES[:2]
MATCHING_PAIR_INDEXES = tuple(range(1, 9))
DEFAULT_MATCHING_PAIR_INDEXES = MATCHING_PAIR_INDEXES[:2]
BLANK_ANSWER_INDEXES = tuple(range(1, 11))
DEFAULT_BLANK_ANSWER_INDEXES = BLANK_ANSWER_INDEXES[:1]
RICH_TEXT_EMBED_TAG_RE = re.compile(r"<\s*(img|video|audio|iframe|table|embed|object)\b", re.IGNORECASE)
BLANK_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\d+)\s*\}\}")


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
    raw_value = str(value or "")
    if RICH_TEXT_EMBED_TAG_RE.search(raw_value):
        return False
    plain_text = strip_tags(raw_value)
    plain_text = unescape(plain_text).replace("\xa0", " ").strip()
    return not plain_text


def _normalize_choice_values(value):
    if value in (None, ""):
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _extract_blank_numbers(value):
    numbers = []
    seen = set()
    for match in BLANK_PLACEHOLDER_RE.finditer(str(value or "")):
        try:
            number = int(match.group(1))
        except (TypeError, ValueError):
            continue
        if number in seen:
            continue
        seen.add(number)
        numbers.append(number)
    return numbers


def _parse_blank_answer_aliases(value):
    raw_items = re.split(r"[\n,;]+", str(value or ""))
    normalized = []
    seen = set()
    for item in raw_items:
        text = item.strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(text)
    return normalized


def _richtext_to_plain_text(value):
    raw_value = str(value or "").strip()
    if not raw_value:
        return ""
    raw_value = re.sub(r"<\s*br\s*/?\s*>", "\n", raw_value, flags=re.IGNORECASE)
    raw_value = re.sub(r"<\s*/\s*(p|div|li|tr|h[1-6])\s*>", "\n", raw_value, flags=re.IGNORECASE)
    plain_text = strip_tags(raw_value)
    plain_text = unescape(plain_text).replace("\xa0", " ")
    plain_text = re.sub(r"\r\n?", "\n", plain_text)
    plain_text = re.sub(r"[ \t]+\n", "\n", plain_text)
    plain_text = re.sub(r"\n{3,}", "\n\n", plain_text)
    return plain_text.strip()


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
    option_f = forms.CharField(label="Opsi F", required=False)
    option_g = forms.CharField(label="Opsi G", required=False)
    option_h = forms.CharField(label="Opsi H", required=False)
    option_i = forms.CharField(label="Opsi I", required=False)
    option_j = forms.CharField(label="Opsi J", required=False)
    correct_option = forms.ChoiceField(
        label="Jawaban Benar",
        required=False,
        choices=[(letter, letter) for letter in OPTION_LETTERS],
        widget=forms.RadioSelect,
    )
    correct_options = forms.MultipleChoiceField(
        label="Jawaban Benar (Checkbox)",
        required=False,
        choices=[(letter, letter) for letter in OPTION_LETTERS],
        widget=forms.CheckboxSelectMultiple,
    )
    checkbox_scoring = forms.ChoiceField(
        label="Metode Penilaian Checkbox",
        required=False,
        choices=Question.CheckboxScoring.choices,
    )

    matching_prompt_1 = forms.CharField(label="Prompt Pasangan 1", required=False)
    matching_answer_1 = forms.CharField(label="Jawaban Pasangan 1", required=False)
    matching_prompt_2 = forms.CharField(label="Prompt Pasangan 2", required=False)
    matching_answer_2 = forms.CharField(label="Jawaban Pasangan 2", required=False)

    answer_text = forms.CharField(
        label="Kunci Jawaban / Rubrik",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
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
            "audio_play_limit",
            "video_play_limit",
            "points",
            "difficulty_level",
            "explanation",
            "checkbox_scoring",
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
            "audio_play_limit": "Batas Putar Audio",
            "video_play_limit": "Batas Putar Video",
            "points": "Bobot Nilai",
            "difficulty_level": "Tingkat Kesulitan",
            "explanation": "Pembahasan",
            "checkbox_scoring": "Metode Penilaian Checkbox",
            "allow_previous": "Izinkan Kembali ke Soal Sebelumnya",
            "allow_next": "Izinkan Lanjut ke Soal Berikutnya",
            "force_sequential": "Paksa Urutan Berurutan",
            "time_limit_seconds": "Batas Waktu per Soal (detik, opsional)",
            "is_active": "Status Aktif",
        }
        widgets = {
            "question_text": forms.Textarea(attrs={"rows": 5, "data-tinymce": "true"}),
            "explanation": forms.Textarea(attrs={"rows": 5, "data-tinymce": "true"}),
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
            ("checkbox", "Checkbox"),
            ("ordering", "Ordering"),
            ("matching", "Matching"),
            ("fill_in_blank", "Fill In Blank"),
            ("essay", "Esai"),
            ("short_answer", "Jawaban Singkat"),
        ]
        if not self.is_bound and not (self.instance and self.instance.pk):
            self.initial.setdefault("question_type", Question.QuestionType.MULTIPLE_CHOICE)
            self.fields["question_type"].initial = Question.QuestionType.MULTIPLE_CHOICE
        self.fields["difficulty_level"].choices = [
            ("", "---------"),
            ("easy", "Mudah"),
            ("medium", "Sedang"),
            ("hard", "Sulit"),
        ]

        for letter in OPTION_LETTERS:
            field_name = f"option_{letter.lower()}"
            if field_name not in self.fields:
                self.fields[field_name] = forms.CharField(label=f"Opsi {letter}", required=False)

        for index in ORDERING_ITEM_INDEXES:
            field_name = f"ordering_item_{index}"
            if field_name not in self.fields:
                self.fields[field_name] = forms.CharField(label=f"Item Urutan {index}", required=False)

        for index in MATCHING_PAIR_INDEXES:
            prompt_name = f"matching_prompt_{index}"
            answer_name = f"matching_answer_{index}"
            if prompt_name not in self.fields:
                self.fields[prompt_name] = forms.CharField(label=f"Prompt Pasangan {index}", required=False)
            if answer_name not in self.fields:
                self.fields[answer_name] = forms.CharField(label=f"Jawaban Pasangan {index}", required=False)

        for index in BLANK_ANSWER_INDEXES:
            accepted_name = f"blank_accepted_answers_{index}"
            case_name = f"blank_case_sensitive_{index}"
            points_name = f"blank_points_{index}"
            if accepted_name not in self.fields:
                self.fields[accepted_name] = forms.CharField(label=f"Jawaban Blank {index}", required=False)
            if case_name not in self.fields:
                self.fields[case_name] = forms.BooleanField(label=f"Case Sensitive Blank {index}", required=False)
            if points_name not in self.fields:
                self.fields[points_name] = forms.DecimalField(
                    label=f"Poin Blank {index}",
                    required=False,
                    min_value=0,
                    decimal_places=2,
                    max_digits=5,
                )

        for field in self.fields.values():
            _bootstrap_widget(field)

        for letter in OPTION_LETTERS:
            name = f"option_{letter.lower()}"
            self.fields[name].widget = forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control option-input",
                    "data-tinymce": "true",
                    "placeholder": f"Tulis isi opsi {letter} atau sisipkan gambar/media...",
                }
            )

        for index in ORDERING_ITEM_INDEXES:
            field_name = f"ordering_item_{index}"
            self.fields[field_name].widget = forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control ordering-item-input",
                    "data-tinymce": "true",
                    "placeholder": f"Tulis item urutan {index} sesuai posisi jawaban benar...",
                }
            )

        for index in MATCHING_PAIR_INDEXES:
            prompt_name = f"matching_prompt_{index}"
            answer_name = f"matching_answer_{index}"
            self.fields[prompt_name].widget = forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control matching-prompt-input",
                    "placeholder": f"Tulis prompt pasangan {index}...",
                }
            )
            self.fields[answer_name].widget = forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control matching-answer-input",
                    "placeholder": f"Tulis jawaban pasangan {index}...",
                }
            )

        for index in BLANK_ANSWER_INDEXES:
            accepted_name = f"blank_accepted_answers_{index}"
            points_name = f"blank_points_{index}"
            self.fields[accepted_name].widget.attrs.update(
                {
                    "class": "form-control blank-accepted-input",
                    "placeholder": "Pisahkan beberapa jawaban dengan koma",
                }
            )
            self.fields[points_name].widget.attrs.update(
                {
                    "class": "form-control blank-points-input",
                    "min": 0,
                    "step": "0.01",
                    "placeholder": "Kosong = dibagi rata",
                }
            )

        # TinyMCE menyembunyikan textarea asli. Required native HTML5 pada elemen
        # tersembunyi bisa memicu "invalid form control is not focusable".
        self.fields["question_text"].required = False

        self.fields["question_text"].widget.attrs["placeholder"] = "Tulis soal di sini..."
        self.fields["audio_play_limit"].widget.attrs.update({"min": 1, "placeholder": "Kosongkan jika tanpa batas"})
        self.fields["video_play_limit"].widget.attrs.update({"min": 1, "placeholder": "Kosongkan jika tanpa batas"})
        self.fields["explanation"].widget.attrs["placeholder"] = "Pembahasan / penjelasan tambahan..."
        self.fields["category_name"].widget.attrs["placeholder"] = "Contoh: Trigonometri Dasar"
        self.fields["tags"].widget.attrs["placeholder"] = "contoh: aljabar, persamaan"
        self.fields["keywords"].widget.attrs["placeholder"] = "contoh: variabel, koefisien"
        self.fields["checkbox_scoring"].initial = Question.CheckboxScoring.ALL_OR_NOTHING

        if self.instance and self.instance.pk and not self.instance._state.adding:
            options = {opt.option_letter: opt for opt in self.instance.options.all()}
            for letter in OPTION_LETTERS:
                field_name = f"option_{letter.lower()}"
                self.fields[field_name].initial = options.get(letter).option_text if letter in options else ""
                if letter in options and options[letter].is_correct:
                    if self.instance.question_type == Question.QuestionType.CHECKBOX:
                        current = list(self.fields["correct_options"].initial or [])
                        current.append(letter)
                        self.fields["correct_options"].initial = current
                    else:
                        self.fields["correct_option"].initial = letter

            answer = QuestionAnswer.objects.filter(question=self.instance).first()
            if answer:
                self.fields["answer_text"].initial = answer.answer_text
                self.fields["keywords"].initial = ", ".join(answer.keywords or [])
                self.fields["is_case_sensitive"].initial = answer.is_case_sensitive
                self.fields["max_word_count"].initial = answer.max_word_count

            ordering_items = list(self.instance.ordering_items.order_by("correct_order"))
            for index in ORDERING_ITEM_INDEXES:
                field_name = f"ordering_item_{index}"
                self.fields[field_name].initial = ordering_items[index - 1].item_text if len(ordering_items) >= index else ""

            matching_pairs = list(self.instance.matching_pairs.order_by("pair_order"))
            for index in MATCHING_PAIR_INDEXES:
                prompt_name = f"matching_prompt_{index}"
                answer_name = f"matching_answer_{index}"
                if len(matching_pairs) >= index:
                    self.fields[prompt_name].initial = _richtext_to_plain_text(matching_pairs[index - 1].prompt_text)
                    self.fields[answer_name].initial = _richtext_to_plain_text(matching_pairs[index - 1].answer_text)
                else:
                    self.fields[prompt_name].initial = ""
                    self.fields[answer_name].initial = ""

            blank_answers = {item.blank_number: item for item in self.instance.blank_answers.all()}
            for index in BLANK_ANSWER_INDEXES:
                accepted_name = f"blank_accepted_answers_{index}"
                case_name = f"blank_case_sensitive_{index}"
                points_name = f"blank_points_{index}"
                blank_answer = blank_answers.get(index)
                if blank_answer:
                    self.fields[accepted_name].initial = ", ".join(blank_answer.accepted_answers or [])
                    self.fields[case_name].initial = blank_answer.is_case_sensitive
                    self.fields[points_name].initial = blank_answer.blank_points
                else:
                    self.fields[accepted_name].initial = ""
                    self.fields[case_name].initial = False
                    self.fields[points_name].initial = None

            tags = (
                QuestionTagRelation.objects.filter(question=self.instance)
                .select_related("tag")
                .values_list("tag__name", flat=True)
            )
            self.fields["tags"].initial = ", ".join(tags)

        selected_correct_option = str(self["correct_option"].value() or "").strip()
        selected_correct_options = set(_normalize_choice_values(self["correct_options"].value()))
        self.option_field_rows = []
        for index, letter in enumerate(OPTION_LETTERS):
            field_name = f"option_{letter.lower()}"
            bound_field = self[field_name]
            field_value = bound_field.value()
            should_show = (
                letter in DEFAULT_OPTION_LETTERS
                or bool(bound_field.errors)
                or not _is_empty_rich_text(field_value)
                or selected_correct_option == letter
                or letter in selected_correct_options
            )
            self.option_field_rows.append(
                {
                    "letter": letter,
                    "field": bound_field,
                    "default_visible": should_show,
                    "required_label": letter in DEFAULT_OPTION_LETTERS,
                    "removable": letter not in DEFAULT_OPTION_LETTERS,
                }
            )

        self.ordering_field_rows = []
        for index in ORDERING_ITEM_INDEXES:
            field_name = f"ordering_item_{index}"
            bound_field = self[field_name]
            field_value = bound_field.value()
            should_show = (
                index in DEFAULT_ORDERING_ITEM_INDEXES
                or bool(bound_field.errors)
                or not _is_empty_rich_text(field_value)
            )
            self.ordering_field_rows.append(
                {
                    "index": index,
                    "field": bound_field,
                    "default_visible": should_show,
                    "required_label": index in DEFAULT_ORDERING_ITEM_INDEXES,
                    "removable": index not in DEFAULT_ORDERING_ITEM_INDEXES,
                }
            )

        self.matching_field_rows = []
        for index in MATCHING_PAIR_INDEXES:
            prompt_name = f"matching_prompt_{index}"
            answer_name = f"matching_answer_{index}"
            prompt_field = self[prompt_name]
            answer_field = self[answer_name]
            should_show = (
                index in DEFAULT_MATCHING_PAIR_INDEXES
                or bool(prompt_field.errors)
                or bool(answer_field.errors)
                or not _is_empty_rich_text(prompt_field.value())
                or not _is_empty_rich_text(answer_field.value())
            )
            self.matching_field_rows.append(
                {
                    "index": index,
                    "prompt_field": prompt_field,
                    "answer_field": answer_field,
                    "default_visible": should_show,
                    "required_label": index in DEFAULT_MATCHING_PAIR_INDEXES,
                    "removable": index not in DEFAULT_MATCHING_PAIR_INDEXES,
                }
            )

        current_question_text_value = self["question_text"].value()
        visible_blank_numbers = set(_extract_blank_numbers(current_question_text_value))
        self.blank_answer_rows = []
        for index in BLANK_ANSWER_INDEXES:
            accepted_name = f"blank_accepted_answers_{index}"
            case_name = f"blank_case_sensitive_{index}"
            points_name = f"blank_points_{index}"
            accepted_field = self[accepted_name]
            case_field = self[case_name]
            points_field = self[points_name]
            should_show = (
                index in visible_blank_numbers
                or index in DEFAULT_BLANK_ANSWER_INDEXES
                or bool(accepted_field.errors)
                or bool(points_field.errors)
                or bool((accepted_field.value() or "").strip())
                or bool(points_field.value())
                or bool(case_field.value())
            )
            self.blank_answer_rows.append(
                {
                    "index": index,
                    "accepted_field": accepted_field,
                    "case_field": case_field,
                    "points_field": points_field,
                    "default_visible": should_show,
                }
            )

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
            letter: (cleaned_data.get(f"option_{letter.lower()}") or "").strip()
            for letter in OPTION_LETTERS
        }
        ordering_values = {
            index: (cleaned_data.get(f"ordering_item_{index}") or "").strip()
            for index in ORDERING_ITEM_INDEXES
        }
        matching_values = {
            index: {
                "prompt": _richtext_to_plain_text(cleaned_data.get(f"matching_prompt_{index}")),
                "answer": _richtext_to_plain_text(cleaned_data.get(f"matching_answer_{index}")),
            }
            for index in MATCHING_PAIR_INDEXES
        }
        for letter, text in option_map.items():
            cleaned_data[f"option_{letter.lower()}"] = "" if _is_empty_rich_text(text) else text
        for index, text in ordering_values.items():
            cleaned_data[f"ordering_item_{index}"] = "" if _is_empty_rich_text(text) else text
        for index, payload in matching_values.items():
            cleaned_data[f"matching_prompt_{index}"] = "" if _is_empty_rich_text(payload["prompt"]) else payload["prompt"]
            cleaned_data[f"matching_answer_{index}"] = "" if _is_empty_rich_text(payload["answer"]) else payload["answer"]
        active_options = {
            letter: cleaned_data[f"option_{letter.lower()}"]
            for letter in OPTION_LETTERS
            if cleaned_data.get(f"option_{letter.lower()}")
        }
        ordering_items = [
            cleaned_data[f"ordering_item_{index}"]
            for index in ORDERING_ITEM_INDEXES
            if cleaned_data.get(f"ordering_item_{index}")
        ]
        matching_pairs = []
        for index in MATCHING_PAIR_INDEXES:
            prompt_name = f"matching_prompt_{index}"
            answer_name = f"matching_answer_{index}"
            prompt_text = cleaned_data.get(prompt_name)
            answer_text_value = cleaned_data.get(answer_name)
            if not prompt_text and not answer_text_value:
                continue
            if not prompt_text:
                self.add_error(prompt_name, "Prompt pasangan wajib diisi.")
            if not answer_text_value:
                self.add_error(answer_name, "Jawaban pasangan wajib diisi.")
            if prompt_text and answer_text_value:
                matching_pairs.append(
                    {
                        "prompt_text": prompt_text,
                        "answer_text": answer_text_value,
                        "pair_order": index,
                    }
                )

        blank_numbers = _extract_blank_numbers(question_text)
        blank_answers = []
        for index in BLANK_ANSWER_INDEXES:
            accepted_name = f"blank_accepted_answers_{index}"
            case_name = f"blank_case_sensitive_{index}"
            points_name = f"blank_points_{index}"
            accepted_aliases = _parse_blank_answer_aliases(cleaned_data.get(accepted_name))
            if index in blank_numbers:
                if not accepted_aliases:
                    self.add_error(accepted_name, f"Jawaban untuk blank {{{{{index}}}}} wajib diisi.")
                else:
                    blank_answers.append(
                        {
                            "blank_number": index,
                            "accepted_answers": accepted_aliases,
                            "is_case_sensitive": False,
                            "blank_points": cleaned_data.get(points_name),
                        }
                    )
        correct_option = cleaned_data.get("correct_option")
        answer_text = (cleaned_data.get("answer_text") or "").strip()
        time_limit = cleaned_data.get("time_limit_seconds")

        if time_limit is not None and time_limit <= 0:
            self.add_error("time_limit_seconds", "Batas waktu per soal harus lebih dari 0.")

        if _is_empty_rich_text(question_text):
            self.add_error("question_text", "Teks soal wajib diisi.")
        else:
            cleaned_data["question_text"] = question_text

        if question_type == Question.QuestionType.MULTIPLE_CHOICE:
            if len(active_options) < 2:
                self.add_error("option_b", "Minimal isi dua opsi untuk soal pilihan ganda.")
            if not correct_option:
                self.add_error("correct_option", "Pilih jawaban benar untuk soal pilihan ganda.")
            elif correct_option not in active_options:
                self.add_error("correct_option", "Jawaban benar harus berasal dari opsi yang terisi.")
            cleaned_data["correct_options"] = []
            cleaned_data["checkbox_scoring"] = Question.CheckboxScoring.ALL_OR_NOTHING
            cleaned_data["answer_text"] = ""
            cleaned_data["keywords"] = ""
            cleaned_data["is_case_sensitive"] = False
            cleaned_data["max_word_count"] = None
            cleaned_data["ordering_items"] = []
            cleaned_data["matching_pairs"] = []
            cleaned_data["blank_answers"] = []
        elif question_type == Question.QuestionType.CHECKBOX:
            selected_correct_options = []
            seen_correct_options = set()
            for item in cleaned_data.get("correct_options", []):
                if item not in OPTION_LETTERS or item in seen_correct_options:
                    continue
                seen_correct_options.add(item)
                selected_correct_options.append(item)
            if len(active_options) < 2:
                self.add_error("option_b", "Minimal isi dua opsi untuk soal checkbox.")
            if len(selected_correct_options) < 2:
                self.add_error("correct_options", "Pilih minimal dua jawaban benar untuk soal checkbox.")
            else:
                invalid_correct = [letter for letter in selected_correct_options if letter not in active_options]
                if invalid_correct:
                    self.add_error("correct_options", "Jawaban benar checkbox harus berasal dari opsi yang terisi.")
            if not cleaned_data.get("checkbox_scoring"):
                cleaned_data["checkbox_scoring"] = Question.CheckboxScoring.ALL_OR_NOTHING
            cleaned_data["correct_options"] = selected_correct_options
            cleaned_data["correct_option"] = ""
            cleaned_data["answer_text"] = ""
            cleaned_data["keywords"] = ""
            cleaned_data["is_case_sensitive"] = False
            cleaned_data["max_word_count"] = None
            cleaned_data["ordering_items"] = []
            cleaned_data["matching_pairs"] = []
            cleaned_data["blank_answers"] = []
        elif question_type == Question.QuestionType.ORDERING:
            if len(ordering_items) < 2:
                self.add_error("ordering_item_2", "Minimal isi dua item untuk soal ordering.")
            cleaned_data["correct_option"] = ""
            cleaned_data["correct_options"] = []
            cleaned_data["checkbox_scoring"] = Question.CheckboxScoring.ALL_OR_NOTHING
            cleaned_data["answer_text"] = ""
            cleaned_data["keywords"] = ""
            cleaned_data["is_case_sensitive"] = False
            cleaned_data["max_word_count"] = None
            cleaned_data["ordering_items"] = ordering_items
            cleaned_data["matching_pairs"] = []
            cleaned_data["blank_answers"] = []
            for letter in OPTION_LETTERS:
                cleaned_data[f"option_{letter.lower()}"] = ""
        elif question_type == Question.QuestionType.MATCHING:
            if len(matching_pairs) < 2:
                self.add_error("matching_answer_2", "Minimal isi dua pasangan untuk soal matching.")
            cleaned_data["correct_option"] = ""
            cleaned_data["correct_options"] = []
            cleaned_data["checkbox_scoring"] = Question.CheckboxScoring.ALL_OR_NOTHING
            cleaned_data["answer_text"] = ""
            cleaned_data["keywords"] = ""
            cleaned_data["is_case_sensitive"] = False
            cleaned_data["max_word_count"] = None
            cleaned_data["ordering_items"] = []
            cleaned_data["matching_pairs"] = matching_pairs
            cleaned_data["blank_answers"] = []
            for letter in OPTION_LETTERS:
                cleaned_data[f"option_{letter.lower()}"] = ""
        elif question_type == Question.QuestionType.FILL_IN_BLANK:
            if any(number > max(BLANK_ANSWER_INDEXES) for number in blank_numbers):
                self.add_error("question_text", f"Blank maksimal menggunakan placeholder {{{{{max(BLANK_ANSWER_INDEXES)}}}}}.")
            if not blank_numbers:
                self.add_error("question_text", "Gunakan placeholder {{1}}, {{2}}, dan seterusnya untuk soal fill in blank.")
            cleaned_data["correct_option"] = ""
            cleaned_data["correct_options"] = []
            cleaned_data["checkbox_scoring"] = Question.CheckboxScoring.ALL_OR_NOTHING
            cleaned_data["answer_text"] = ""
            cleaned_data["keywords"] = ""
            cleaned_data["is_case_sensitive"] = False
            cleaned_data["max_word_count"] = None
            cleaned_data["ordering_items"] = []
            cleaned_data["matching_pairs"] = []
            cleaned_data["blank_answers"] = blank_answers
            for letter in OPTION_LETTERS:
                cleaned_data[f"option_{letter.lower()}"] = ""
        else:
            if not answer_text:
                self.add_error("answer_text", "Kunci jawaban / rubrik wajib diisi.")
            cleaned_data["correct_option"] = ""
            cleaned_data["correct_options"] = []
            cleaned_data["checkbox_scoring"] = Question.CheckboxScoring.ALL_OR_NOTHING
            cleaned_data["is_case_sensitive"] = False
            cleaned_data["max_word_count"] = None
            cleaned_data["ordering_items"] = []
            cleaned_data["matching_pairs"] = []
            cleaned_data["blank_answers"] = []

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
