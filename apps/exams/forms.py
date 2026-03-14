from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.html import strip_tags
from django.utils import timezone

from apps.accounts.models import User
from apps.questions.models import Question, QuestionCategory
from apps.results.models import CertificateTemplate
from apps.subjects.models import Subject

from .models import Class, Exam
from .services import sync_classes_from_student_profiles


def _bootstrap_widget(field):
    if isinstance(field.widget, forms.CheckboxInput):
        css_class = "form-check-input"
    elif isinstance(field.widget, forms.RadioSelect):
        css_class = "form-check-input"
    elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
        css_class = "form-select"
    else:
        css_class = "form-control"
    existing = field.widget.attrs.get("class", "")
    field.widget.attrs["class"] = f"{existing} {css_class}".strip()


def _coerce_nullable_bool(value):
    if value in (None, "", "inherit"):
        return None
    if isinstance(value, bool):
        return value
    raw = str(value).strip().lower()
    if raw in {"true", "1", "ya", "yes"}:
        return True
    if raw in {"false", "0", "tidak", "no"}:
        return False
    raise ValidationError("Nilai override navigasi tidak valid.")


class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ["name", "grade_level", "academic_year", "is_active"]
        labels = {
            "name": "Nama Kelas",
            "grade_level": "Tingkat",
            "academic_year": "Tahun Ajaran",
            "is_active": "Status Aktif",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            _bootstrap_widget(field)
        self.fields["grade_level"].required = False
        self.fields["academic_year"].required = False
        self.fields["grade_level"].widget.attrs.setdefault("placeholder", "Contoh: XII")
        self.fields["academic_year"].widget.attrs.setdefault("placeholder", "Contoh: 2025/2026")

    def clean_name(self):
        value = (self.cleaned_data.get("name") or "").strip()
        if not value:
            raise forms.ValidationError("Nama kelas wajib diisi.")
        queryset = Class.objects.filter(name__iexact=value)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("Nama kelas sudah digunakan. Gunakan nama yang berbeda.")
        return value


class ExamWizardForm(forms.ModelForm):
    HELPER_TEXT_IDS = {
        "passing_score": "examPassingScoreHelp",
        "allow_retake": "examRetakeHelp",
        "max_retake_attempts": "examRetakeAttemptsHelp",
        "retake_cooldown_minutes": "examRetakeCooldownHelp",
        "certificate_enabled": "examCertificateHelp",
        "certificate_template": "examCertificateTemplateHelp",
        "override_question_navigation": "examNavigationOverrideHelp",
        "global_force_sequential": "examSequentialHelp",
        "require_camera": "examCameraHelp",
        "require_microphone": "examMicrophoneHelp",
        "disable_right_click": "examRightClickHelp",
        "block_copy_paste": "examCopyPasteHelp",
        "enable_screenshot_proctoring": "examScreenshotHelp",
        "screenshot_interval_seconds": "examScreenshotIntervalHelp",
        "max_violations_allowed": "examViolationsHelp",
    }

    selected_questions_payload = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
    assignment_payload = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
    status_action = forms.ChoiceField(
        required=False,
        choices=[("draft", "Simpan Draf"), ("publish", "Publikasikan")],
        widget=forms.HiddenInput(),
        initial="draft",
    )

    class Meta:
        model = Exam
        fields = [
            "title",
            "subject",
            "description",
            "instructions",
            "start_time",
            "end_time",
            "duration_minutes",
            "passing_score",
            "randomize_questions",
            "randomize_options",
            "show_results_immediately",
            "allow_review",
            "allow_retake",
            "max_retake_attempts",
            "retake_score_policy",
            "retake_cooldown_minutes",
            "retake_show_review",
            "certificate_enabled",
            "certificate_template",
            "override_question_navigation",
            "global_allow_previous",
            "global_allow_next",
            "global_force_sequential",
            "require_fullscreen",
            "require_camera",
            "require_microphone",
            "detect_tab_switch",
            "disable_right_click",
            "block_copy_paste",
            "enable_screenshot_proctoring",
            "screenshot_interval_seconds",
            "max_violations_allowed",
        ]
        labels = {
            "title": "Judul Ujian",
            "subject": "Mata Pelajaran",
            "description": "Deskripsi",
            "instructions": "Instruksi Ujian",
            "start_time": "Tanggal & Waktu Mulai",
            "end_time": "Tanggal & Waktu Selesai",
            "duration_minutes": "Durasi Ujian (menit)",
            "passing_score": "Nilai Kelulusan (%)",
            "randomize_questions": "Acak Urutan Soal",
            "randomize_options": "Acak Opsi Jawaban",
            "show_results_immediately": "Tampilkan hasil segera setelah submit",
            "allow_review": "Izinkan peninjauan jawaban",
            "allow_retake": "Izinkan ujian ulang (retake)",
            "max_retake_attempts": "Maksimal percobaan total",
            "retake_score_policy": "Kebijakan nilai retake",
            "retake_cooldown_minutes": "Jeda antar percobaan (menit)",
            "retake_show_review": "Izinkan review jawaban sebelum retake",
            "certificate_enabled": "Aktifkan sertifikat kelulusan",
            "certificate_template": "Template sertifikat",
            "override_question_navigation": "Gunakan aturan navigasi global ujian",
            "global_allow_previous": "Izinkan navigasi ke soal sebelumnya (global)",
            "global_allow_next": "Izinkan navigasi ke soal berikutnya (global)",
            "global_force_sequential": "Paksa pengerjaan berurutan (global)",
            "require_fullscreen": "Wajib fullscreen",
            "require_camera": "Wajib izinkan kamera",
            "require_microphone": "Wajib izinkan mikrofon",
            "detect_tab_switch": "Deteksi perpindahan tab",
            "disable_right_click": "Blokir klik kanan",
            "block_copy_paste": "Blokir copy, cut, dan paste",
            "enable_screenshot_proctoring": "Aktifkan screenshot proctoring",
            "screenshot_interval_seconds": "Interval screenshot (detik)",
            "max_violations_allowed": "Maksimal pelanggaran",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "instructions": forms.Textarea(attrs={"rows": 4}),
            "start_time": forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}),
            "retake_score_policy": forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)

        subject_queryset = Subject.objects.filter(is_active=True)
        if self.instance and self.instance.pk and self.instance.subject_id:
            subject_queryset = Subject.objects.filter(Q(is_active=True) | Q(id=self.instance.subject_id))
        self.fields["subject"].queryset = subject_queryset.order_by("name")

        for field in self.fields.values():
            _bootstrap_widget(field)
        for field_name, help_id in self.HELPER_TEXT_IDS.items():
            self.fields[field_name].widget.attrs["aria-describedby"] = help_id

        # default safer values for anti-cheat
        self.fields["screenshot_interval_seconds"].initial = self.fields["screenshot_interval_seconds"].initial or 300
        self.fields["max_violations_allowed"].initial = self.fields["max_violations_allowed"].initial or 3
        self.fields["max_retake_attempts"].initial = self.fields["max_retake_attempts"].initial or 1
        self.fields["retake_cooldown_minutes"].initial = self.fields["retake_cooldown_minutes"].initial or 0
        self.fields["max_retake_attempts"].required = False
        self.fields["retake_score_policy"].required = False
        self.fields["retake_cooldown_minutes"].required = False
        self.fields["max_retake_attempts"].widget.attrs.update({"min": 1, "max": 10})
        self.fields["retake_cooldown_minutes"].widget.attrs.update({"min": 0})

        if "certificate_template" in self.fields:
            template_qs = CertificateTemplate.objects.filter(is_default=True)
            if self.teacher:
                template_qs = CertificateTemplate.objects.filter(
                    Q(created_by=self.teacher) | Q(is_default=True)
                )
            if self.instance and self.instance.pk and self.instance.certificate_template_id:
                template_qs = template_qs | CertificateTemplate.objects.filter(id=self.instance.certificate_template_id)
            self.fields["certificate_template"].queryset = template_qs.distinct().order_by("template_name")
            self.fields["certificate_template"].required = False
            self.fields["certificate_template"].empty_label = "Gunakan template default sistem"

        self.available_questions = Question.objects.none()
        self.available_categories = QuestionCategory.objects.none()
        self.available_question_subjects = Subject.objects.none()
        self.available_question_type_choices = list(Question.QuestionType.choices)
        self.available_classes = Class.objects.none()
        self.available_students = User.objects.none()

        if self.teacher:
            sync_classes_from_student_profiles()
            self.available_categories = (
                QuestionCategory.objects.filter(
                    is_active=True,
                    questions__created_by=self.teacher,
                    questions__is_deleted=False,
                    questions__is_active=True,
                )
                .distinct()
                .order_by("name")
            )
            self.available_question_subjects = (
                Subject.objects.filter(
                    is_active=True,
                    questions__created_by=self.teacher,
                    questions__is_deleted=False,
                    questions__is_active=True,
                )
                .distinct()
                .order_by("name")
            )
            self.available_classes = (
                Class.objects.filter(
                    is_active=True,
                    students__student__role="student",
                    students__student__is_active=True,
                    students__student__is_deleted=False,
                )
                .distinct()
                .order_by("name")
            )
            self.available_students = User.objects.filter(
                role="student",
                is_active=True,
                is_deleted=False,
            ).order_by("first_name", "last_name", "username")

        if self.instance and self.instance.pk:
            start_local = timezone.localtime(self.instance.start_time).strftime("%Y-%m-%dT%H:%M")
            end_local = timezone.localtime(self.instance.end_time).strftime("%Y-%m-%dT%H:%M")
            self.initial["start_time"] = start_local
            self.initial["end_time"] = end_local

            questions_payload = []
            exam_questions = (
                self.instance.exam_questions.select_related("question", "question__subject", "question__category")
                .order_by("display_order")
            )
            for item in exam_questions:
                question = item.question
                questions_payload.append(
                    {
                        "question_id": str(question.id),
                        "display_order": item.display_order,
                        "points_override": float(item.points_override) if item.points_override is not None else "",
                        "override_navigation": bool(item.override_navigation),
                        "allow_previous_override": item.allow_previous_override,
                        "allow_next_override": item.allow_next_override,
                        "force_sequential_override": item.force_sequential_override,
                        "question_text": strip_tags(question.question_text or ""),
                        "question_type": question.question_type,
                        "subject_name": question.subject.name if question.subject_id else "",
                        "category_name": question.category.name if question.category_id else "",
                        "default_points": float(question.points),
                        "default_allow_previous": question.allow_previous,
                        "default_allow_next": question.allow_next,
                        "default_force_sequential": question.force_sequential,
                    }
                )
            self.initial.setdefault(
                "selected_questions_payload",
                json.dumps(questions_payload),
            )

            assignments_payload = []
            for assignment in self.instance.assignments.all():
                if assignment.assigned_to_type == "class" and assignment.class_obj_id:
                    assignments_payload.append(
                        {
                            "type": "class",
                            "id": str(assignment.class_obj_id),
                        }
                    )
                if assignment.assigned_to_type == "student" and assignment.student_id:
                    assignments_payload.append(
                        {
                            "type": "student",
                            "id": str(assignment.student_id),
                        }
                    )
            self.initial.setdefault("assignment_payload", json.dumps(assignments_payload))

    def _parse_selected_questions_payload(self):
        raw_payload = (self.cleaned_data.get("selected_questions_payload") or "").strip()
        if not raw_payload:
            return []
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Payload soal tidak valid: {exc}")
        if not isinstance(payload, list):
            raise ValidationError("Payload soal harus berupa list.")
        return payload

    def _parse_assignment_payload(self):
        raw_payload = (self.cleaned_data.get("assignment_payload") or "").strip()
        if not raw_payload:
            return []
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Payload penugasan tidak valid: {exc}")
        if not isinstance(payload, list):
            raise ValidationError("Payload penugasan harus berupa list.")
        return payload

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        duration_minutes = cleaned_data.get("duration_minutes")
        passing_score = cleaned_data.get("passing_score")
        enable_screenshot = cleaned_data.get("enable_screenshot_proctoring")
        require_camera = cleaned_data.get("require_camera")
        require_microphone = cleaned_data.get("require_microphone")
        screenshot_interval = cleaned_data.get("screenshot_interval_seconds")
        max_violations = cleaned_data.get("max_violations_allowed")
        status_action = (cleaned_data.get("status_action") or "draft").strip().lower()
        override_question_navigation = cleaned_data.get("override_question_navigation")
        global_force_sequential = cleaned_data.get("global_force_sequential")
        allow_retake = cleaned_data.get("allow_retake")
        max_retake_attempts = cleaned_data.get("max_retake_attempts")
        retake_score_policy = (cleaned_data.get("retake_score_policy") or "").strip().lower()
        retake_cooldown_minutes = cleaned_data.get("retake_cooldown_minutes")
        certificate_enabled = cleaned_data.get("certificate_enabled")

        if status_action not in {"draft", "publish"}:
            self.add_error("status_action", "Aksi status tidak valid.")

        if start_time and timezone.is_naive(start_time):
            cleaned_data["start_time"] = timezone.make_aware(start_time, timezone.get_current_timezone())
            start_time = cleaned_data["start_time"]
        if end_time and timezone.is_naive(end_time):
            cleaned_data["end_time"] = timezone.make_aware(end_time, timezone.get_current_timezone())
            end_time = cleaned_data["end_time"]

        if start_time and end_time and end_time <= start_time:
            self.add_error("end_time", "Waktu selesai harus lebih besar dari waktu mulai.")

        if duration_minutes is not None and duration_minutes <= 0:
            self.add_error("duration_minutes", "Durasi harus lebih dari 0 menit.")

        if start_time and end_time and duration_minutes:
            total_available_minutes = int((end_time - start_time) / timedelta(minutes=1))
            if duration_minutes > total_available_minutes:
                self.add_error(
                    "duration_minutes",
                    "Durasi ujian melebihi rentang waktu mulai-selesai.",
                )

        if passing_score is not None and (passing_score < 0 or passing_score > 100):
            self.add_error("passing_score", "Nilai kelulusan harus berada pada rentang 0-100.")

        if enable_screenshot:
            if not require_camera:
                self.add_error(
                    "require_camera",
                    "Kamera wajib diizinkan jika screenshot proctoring diaktifkan.",
                )
            if screenshot_interval is None or screenshot_interval <= 0:
                self.add_error("screenshot_interval_seconds", "Interval screenshot harus lebih dari 0.")
        else:
            cleaned_data["screenshot_interval_seconds"] = 300

        if not require_camera and not require_microphone:
            cleaned_data["enable_screenshot_proctoring"] = False
            cleaned_data["screenshot_interval_seconds"] = 300

        if max_violations is None or max_violations <= 0:
            self.add_error("max_violations_allowed", "Maksimal pelanggaran harus lebih dari 0.")

        if allow_retake:
            if max_retake_attempts is None:
                self.add_error("max_retake_attempts", "Maksimal percobaan wajib diisi.")
            elif max_retake_attempts < 2 or max_retake_attempts > 10:
                self.add_error("max_retake_attempts", "Maksimal percobaan retake harus pada rentang 2-10.")

            if retake_score_policy not in {"highest", "latest", "average"}:
                self.add_error("retake_score_policy", "Kebijakan nilai retake tidak valid.")

            if retake_cooldown_minutes is None or retake_cooldown_minutes < 0:
                self.add_error("retake_cooldown_minutes", "Jeda retake minimal 0 menit.")
        else:
            cleaned_data["max_retake_attempts"] = 1
            cleaned_data["retake_score_policy"] = "highest"
            cleaned_data["retake_cooldown_minutes"] = 0
            cleaned_data["retake_show_review"] = False

        if not certificate_enabled:
            cleaned_data["certificate_template"] = None

        if override_question_navigation and global_force_sequential:
            cleaned_data["global_allow_previous"] = False

        question_items = []
        try:
            parsed_questions = self._parse_selected_questions_payload()
            if not parsed_questions:
                self.add_error("selected_questions_payload", "Pilih minimal satu soal untuk ujian.")
            seen_ids = set()
            for idx, item in enumerate(parsed_questions, start=1):
                if not isinstance(item, dict):
                    raise ValidationError(f"Data soal ke-{idx} tidak valid.")
                question_id = str(item.get("question_id") or "").strip()
                if not question_id:
                    raise ValidationError(f"Soal ke-{idx} tidak memiliki ID.")
                if question_id in seen_ids:
                    raise ValidationError(f"Soal duplikat ditemukan pada payload: {question_id}.")
                seen_ids.add(question_id)

                display_order = item.get("display_order") or idx
                try:
                    display_order = int(display_order)
                except (ValueError, TypeError):
                    raise ValidationError(f"Urutan soal ke-{idx} tidak valid.")
                if display_order <= 0:
                    raise ValidationError(f"Urutan soal ke-{idx} harus lebih dari 0.")

                points_override = item.get("points_override")
                if points_override in ("", None):
                    parsed_points_override = None
                else:
                    try:
                        parsed_points_override = Decimal(str(points_override))
                    except Exception:
                        raise ValidationError(f"Nilai poin override soal ke-{idx} tidak valid.")
                    if parsed_points_override <= 0:
                        raise ValidationError(f"Nilai poin override soal ke-{idx} harus lebih dari 0.")

                override_navigation = bool(item.get("override_navigation"))
                allow_previous_override = _coerce_nullable_bool(item.get("allow_previous_override"))
                allow_next_override = _coerce_nullable_bool(item.get("allow_next_override"))
                force_sequential_override = _coerce_nullable_bool(item.get("force_sequential_override"))

                question_items.append(
                    {
                        "question_id": question_id,
                        "display_order": display_order,
                        "points_override": parsed_points_override,
                        "override_navigation": override_navigation,
                        "allow_previous_override": allow_previous_override,
                        "allow_next_override": allow_next_override,
                        "force_sequential_override": force_sequential_override,
                    }
                )

            question_ids = [item["question_id"] for item in question_items]
            question_map = {
                str(question.id): question
                for question in Question.objects.filter(
                    id__in=question_ids,
                    created_by=self.teacher,
                    is_deleted=False,
                    is_active=True,
                ).select_related("subject", "category")
            }
            if len(question_map) != len(question_ids):
                self.add_error("selected_questions_payload", "Ada soal yang tidak valid atau bukan milik guru ini.")
            for item in question_items:
                question = question_map.get(item["question_id"])
                if not question:
                    continue
                item["question_obj"] = question
                item["default_points"] = question.points

        except ValidationError as exc:
            self.add_error("selected_questions_payload", exc.message)

        assignment_items = []
        try:
            parsed_assignments = self._parse_assignment_payload()
            if not parsed_assignments:
                self.add_error("assignment_payload", "Pilih minimal satu assignment kelas atau siswa.")

            class_ids = []
            student_ids = []
            for idx, item in enumerate(parsed_assignments, start=1):
                if not isinstance(item, dict):
                    raise ValidationError(f"Data assignment ke-{idx} tidak valid.")
                item_type = str(item.get("type") or "").strip()
                item_id = str(item.get("id") or "").strip()
                if item_type not in {"class", "student"}:
                    raise ValidationError(f"Tipe assignment ke-{idx} tidak valid.")
                if not item_id:
                    raise ValidationError(f"ID assignment ke-{idx} wajib diisi.")
                assignment_items.append({"type": item_type, "id": item_id})
                if item_type == "class":
                    class_ids.append(item_id)
                else:
                    student_ids.append(item_id)

            valid_class_ids = set(
                str(item.id)
                for item in Class.objects.filter(id__in=class_ids, is_active=True)
            )
            valid_student_ids = set(
                str(item.id)
                for item in User.objects.filter(
                    id__in=student_ids,
                    role="student",
                    is_active=True,
                    is_deleted=False,
                )
            )
            for item in assignment_items:
                if item["type"] == "class" and item["id"] not in valid_class_ids:
                    raise ValidationError(f"Penugasan kelas tidak valid: {item['id']}")
                if item["type"] == "student" and item["id"] not in valid_student_ids:
                    raise ValidationError(f"Penugasan siswa tidak valid: {item['id']}")

        except ValidationError as exc:
            self.add_error("assignment_payload", exc.message)

        cleaned_data["parsed_questions"] = question_items
        cleaned_data["parsed_assignments"] = assignment_items
        return cleaned_data
