import json
from collections import Counter
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import UserProfile
from apps.notifications.models import SystemSetting
from apps.questions.models import (
    Question,
    QuestionAnswer,
    QuestionBlankAnswer,
    QuestionCategory,
    QuestionMatchingPair,
    QuestionOption,
    QuestionOrderingItem,
    QuestionTag,
    QuestionTagRelation,
)
from apps.subjects.models import Subject

User = get_user_model()

OPTION_LETTERS = [choice.value for choice in QuestionOption.OptionLetter]
QUESTION_BANK_FILE = Path(__file__).resolve().parent / "data" / "question_bank.json"
EXPECTED_QUESTION_COUNT_PER_TYPE = 10
QUESTION_TYPE_SEQUENCE = [
    Question.QuestionType.MULTIPLE_CHOICE,
    Question.QuestionType.CHECKBOX,
    Question.QuestionType.ORDERING,
    Question.QuestionType.MATCHING,
    Question.QuestionType.FILL_IN_BLANK,
    Question.QuestionType.ESSAY,
    Question.QuestionType.SHORT_ANSWER,
]

ADMIN_ACCOUNT = {
    "username": "admin",
    "email": "admin@mail.com",
    "password": "admin123",
    "first_name": "System",
    "last_name": "Administrator",
    "role": User.Role.ADMIN,
}

TEACHER_ACCOUNTS = [
    {
        "username": "olivia.carter",
        "email": "olivia.carter@mail.com",
        "password": "teacher123",
        "first_name": "Olivia",
        "last_name": "Carter",
        "teacher_id": "TCH-1001",
        "subject_specialization": "Mathematics",
    },
    {
        "username": "michael.reed",
        "email": "michael.reed@mail.com",
        "password": "teacher123",
        "first_name": "Michael",
        "last_name": "Reed",
        "teacher_id": "TCH-1002",
        "subject_specialization": "Science",
    },
    {
        "username": "sophia.bennett",
        "email": "sophia.bennett@mail.com",
        "password": "teacher123",
        "first_name": "Sophia",
        "last_name": "Bennett",
        "teacher_id": "TCH-1003",
        "subject_specialization": "Humanities and Technology",
    },
]

STUDENT_ACCOUNTS = [
    {
        "username": "ethan.walker",
        "email": "ethan.walker@mail.com",
        "password": "student123",
        "first_name": "Ethan",
        "last_name": "Walker",
        "student_id": "STU-2001",
        "class_grade": "11th Grade - A",
    },
    {
        "username": "ava.thompson",
        "email": "ava.thompson@mail.com",
        "password": "student123",
        "first_name": "Ava",
        "last_name": "Thompson",
        "student_id": "STU-2002",
        "class_grade": "11th Grade - B",
    },
    {
        "username": "noah.parker",
        "email": "noah.parker@mail.com",
        "password": "student123",
        "first_name": "Noah",
        "last_name": "Parker",
        "student_id": "STU-2003",
        "class_grade": "12th Grade - A",
    },
]

SUBJECTS = [
    {
        "code": "ALG2",
        "name": "Algebra II",
        "description": "Functions, equations, and polynomial operations for U.S. high school math.",
    },
    {
        "code": "GEOM",
        "name": "Geometry",
        "description": "Core geometry concepts, proofs, and measurement.",
    },
    {
        "code": "BIO",
        "name": "Biology",
        "description": "Cells, genetics, ecosystems, and scientific reasoning.",
    },
    {
        "code": "CHEM",
        "name": "Chemistry",
        "description": "Matter, atoms, reactions, and stoichiometry.",
    },
    {
        "code": "PHYS",
        "name": "Physics",
        "description": "Motion, forces, energy, and waves.",
    },
    {
        "code": "ENG-LIT",
        "name": "English Literature",
        "description": "Reading analysis, literary devices, and theme.",
    },
    {
        "code": "USHIST",
        "name": "U.S. History",
        "description": "Foundations of the United States and major historical events.",
    },
    {
        "code": "CS",
        "name": "Computer Science",
        "description": "Programming fundamentals, algorithms, and digital logic.",
    },
]

SYSTEM_SETTINGS = [
    {
        "setting_key": "institution_name",
        "setting_value": "Riverside High School",
        "setting_type": "string",
        "category": "branding",
        "description": "Nama sekolah/lembaga",
        "is_public": True,
    },
    {
        "setting_key": "institution_type",
        "setting_value": "High School",
        "setting_type": "string",
        "category": "branding",
        "description": "Jenis lembaga (SMA/SMK/MA/Universitas)",
        "is_public": True,
    },
    {
        "setting_key": "institution_address",
        "setting_value": "1250 Lincoln Ave, Portland, OR 97205",
        "setting_type": "string",
        "category": "branding",
        "description": "Alamat lembaga",
        "is_public": False,
    },
    {
        "setting_key": "institution_phone",
        "setting_value": "+1 503-555-0117",
        "setting_type": "string",
        "category": "branding",
        "description": "Nomor telepon/WA lembaga",
        "is_public": False,
    },
    {
        "setting_key": "institution_email",
        "setting_value": "hello@riversidehigh.edu",
        "setting_type": "string",
        "category": "branding",
        "description": "Email resmi lembaga",
        "is_public": False,
    },
    {
        "setting_key": "institution_website",
        "setting_value": "https://www.riversidehigh.edu",
        "setting_type": "string",
        "category": "branding",
        "description": "Website resmi lembaga",
        "is_public": True,
    },
    {
        "setting_key": "institution_logo_url",
        "setting_value": "",
        "setting_type": "string",
        "category": "branding",
        "description": "Path logo utama",
        "is_public": True,
    },
    {
        "setting_key": "institution_logo_dark_url",
        "setting_value": "",
        "setting_type": "string",
        "category": "branding",
        "description": "Path logo dark",
        "is_public": True,
    },
    {
        "setting_key": "institution_favicon_url",
        "setting_value": "",
        "setting_type": "string",
        "category": "branding",
        "description": "Path favicon",
        "is_public": True,
    },
    {
        "setting_key": "login_page_headline",
        "setting_value": "Welcome Back",
        "setting_type": "string",
        "category": "branding",
        "description": "Headline login page",
        "is_public": True,
    },
    {
        "setting_key": "login_page_subheadline",
        "setting_value": "Sign in to manage exams, question banks, and student sessions.",
        "setting_type": "string",
        "category": "branding",
        "description": "Subheadline login page",
        "is_public": True,
    },
    {
        "setting_key": "login_page_background_url",
        "setting_value": "",
        "setting_type": "string",
        "category": "branding",
        "description": "Path background login",
        "is_public": True,
    },
    {
        "setting_key": "primary_color",
        "setting_value": "#0d6efd",
        "setting_type": "string",
        "category": "branding",
        "description": "Warna utama UI",
        "is_public": True,
    },
    {
        "setting_key": "landing_page_enabled",
        "setting_value": "true",
        "setting_type": "boolean",
        "category": "general",
        "description": "Aktifkan landing page di URL root",
        "is_public": True,
    },
    {
        "setting_key": "default_exam_duration",
        "setting_value": "120",
        "setting_type": "number",
        "category": "exam_defaults",
        "description": "Default exam duration in minutes",
        "is_public": False,
    },
    {
        "setting_key": "default_passing_score",
        "setting_value": "60",
        "setting_type": "number",
        "category": "exam_defaults",
        "description": "Default passing score percentage",
        "is_public": False,
    },
    {
        "setting_key": "max_login_attempts",
        "setting_value": "5",
        "setting_type": "number",
        "category": "security",
        "description": "Maximum login attempts before lockout",
        "is_public": False,
    },
    {
        "setting_key": "session_timeout_minutes",
        "setting_value": "120",
        "setting_type": "number",
        "category": "security",
        "description": "User session timeout in minutes",
        "is_public": False,
    },
    {
        "setting_key": "certificates_enabled",
        "setting_value": "true",
        "setting_type": "boolean",
        "category": "certificates",
        "description": "Master switch fitur sertifikat",
        "is_public": False,
    },
    {
        "setting_key": "certificate_number_prefix",
        "setting_value": "CERT",
        "setting_type": "string",
        "category": "certificates",
        "description": "Prefix nomor sertifikat",
        "is_public": False,
    },
    {
        "setting_key": "certificate_pdf_dpi",
        "setting_value": "150",
        "setting_type": "number",
        "category": "certificates",
        "description": "Resolusi render PDF sertifikat",
        "is_public": False,
    },
    {
        "setting_key": "certificate_storage_path",
        "setting_value": "certificates/",
        "setting_type": "string",
        "category": "certificates",
        "description": "Direktori penyimpanan sertifikat",
        "is_public": False,
    },
    {
        "setting_key": "certificate_email_enabled",
        "setting_value": "false",
        "setting_type": "boolean",
        "category": "certificates",
        "description": "Kirim email saat sertifikat siap",
        "is_public": False,
    },
    {
        "setting_key": "certificate_verify_public",
        "setting_value": "true",
        "setting_type": "boolean",
        "category": "certificates",
        "description": "Verifikasi sertifikat publik",
        "is_public": True,
    },
]


class Command(BaseCommand):
    help = "Seed demo data with sample users, U.S. high school subjects, and rich media example questions."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting database seeding..."))

        question_bank = self._load_question_bank()
        self.create_admin_user()
        teachers = self.create_teacher_users()
        self.create_student_users()
        subjects = self.create_subjects()
        self.create_question_bank(question_bank, teachers, subjects)
        self.create_system_settings()

        self.stdout.write(self.style.SUCCESS("Database seeding completed."))

    def _load_question_bank(self):
        try:
            payload = json.loads(QUESTION_BANK_FILE.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise CommandError(f"Question seed file not found: {QUESTION_BANK_FILE}") from exc
        except json.JSONDecodeError as exc:
            raise CommandError(f"Question seed file is not valid JSON: {exc}") from exc

        if not isinstance(payload, dict):
            raise CommandError("Question seed file must be a JSON object keyed by question type.")

        unexpected_keys = set(payload.keys()) - set(QUESTION_TYPE_SEQUENCE)
        if unexpected_keys:
            raise CommandError(
                f"Unexpected question type sections in JSON seed file: {', '.join(sorted(unexpected_keys))}"
            )

        question_bank = []
        for question_type in QUESTION_TYPE_SEQUENCE:
            items = payload.get(question_type, [])
            if not isinstance(items, list):
                raise CommandError(f"Section '{question_type}' must be a list.")
            if len(items) != EXPECTED_QUESTION_COUNT_PER_TYPE:
                raise CommandError(
                    f"Section '{question_type}' must contain exactly "
                    f"{EXPECTED_QUESTION_COUNT_PER_TYPE} questions."
                )
            for item in items:
                if not isinstance(item, dict):
                    raise CommandError(f"Each item in '{question_type}' must be an object.")
                question_row = dict(item)
                question_row["question_type"] = question_type
                question_bank.append(question_row)

        counts = Counter(item["question_type"] for item in question_bank)
        for question_type in QUESTION_TYPE_SEQUENCE:
            if counts[question_type] != EXPECTED_QUESTION_COUNT_PER_TYPE:
                raise CommandError(
                    f"Question type '{question_type}' has {counts[question_type]} rows, "
                    f"expected {EXPECTED_QUESTION_COUNT_PER_TYPE}."
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {len(question_bank)} question seeds from {QUESTION_BANK_FILE.name}."
            )
        )
        return question_bank

    def _upsert_user(self, account_data, role, is_superuser=False):
        defaults = {
            "email": account_data["email"],
            "first_name": account_data["first_name"],
            "last_name": account_data["last_name"],
            "role": role,
            "is_active": True,
            "is_deleted": False,
        }
        if is_superuser:
            defaults["is_staff"] = True
            defaults["is_superuser"] = True
        else:
            defaults["is_staff"] = False
            defaults["is_superuser"] = False

        user, created = User.objects.get_or_create(
            username=account_data["username"],
            defaults=defaults,
        )

        changed_fields = []
        for field, value in defaults.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed_fields.append(field)

        if created or not user.check_password(account_data["password"]):
            user.set_password(account_data["password"])
            changed_fields.append("password")

        if changed_fields:
            user.save()

        action = "Created" if created else "Updated" if changed_fields else "Unchanged"
        self.stdout.write(self.style.SUCCESS(f"{action} {role} user: {user.username}"))
        return user

    def create_admin_user(self):
        self._upsert_user(ADMIN_ACCOUNT, User.Role.ADMIN, is_superuser=True)

    def create_teacher_users(self):
        teachers = {}
        for teacher_data in TEACHER_ACCOUNTS:
            user = self._upsert_user(teacher_data, User.Role.TEACHER)
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "teacher_id": teacher_data["teacher_id"],
                    "subject_specialization": teacher_data["subject_specialization"],
                },
            )
            teachers[user.username] = user
        return teachers

    def create_student_users(self):
        students = {}
        for student_data in STUDENT_ACCOUNTS:
            user = self._upsert_user(student_data, User.Role.STUDENT)
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "student_id": student_data["student_id"],
                    "class_grade": student_data["class_grade"],
                },
            )
            students[user.username] = user
        return students

    def create_subjects(self):
        subject_map = {}
        for subject_data in SUBJECTS:
            subject = Subject.objects.filter(code=subject_data["code"]).first()
            if subject is None:
                subject = Subject.objects.filter(name=subject_data["name"]).first()

            created = subject is None
            if created:
                subject = Subject.objects.create(
                    code=subject_data["code"],
                    name=subject_data["name"],
                    description=subject_data["description"],
                    is_active=True,
                )
            else:
                changed = False
                for field, value in {
                    "code": subject_data["code"],
                    "name": subject_data["name"],
                    "description": subject_data["description"],
                    "is_active": True,
                }.items():
                    if getattr(subject, field) != value:
                        setattr(subject, field, value)
                        changed = True
                if changed:
                    subject.save()

            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} subject: {subject.name}"))
            subject_map[subject_data["code"]] = subject
        return subject_map

    def _get_or_create_category(self, name):
        category, created = QuestionCategory.objects.get_or_create(
            name=name,
            parent=None,
            defaults={
                "description": f"Sample category for {name}.",
                "is_active": True,
            },
        )
        if not created and not category.is_active:
            category.is_active = True
            category.save(update_fields=["is_active", "updated_at"])
        return category

    def _sync_question_options(self, question, options_data):
        if len(options_data) > len(OPTION_LETTERS):
            raise CommandError(f"Question '{question.question_text[:40]}' has too many options.")

        if question.question_type not in {
            Question.QuestionType.MULTIPLE_CHOICE,
            Question.QuestionType.CHECKBOX,
        }:
            QuestionOption.objects.filter(question=question).delete()
            return

        QuestionOption.objects.filter(question=question).delete()
        QuestionOption.objects.bulk_create(
            [
                QuestionOption(
                    question=question,
                    option_letter=OPTION_LETTERS[index],
                    option_text=option_data["text"],
                    option_image_url=option_data.get("image_url", ""),
                    is_correct=option_data["is_correct"],
                    display_order=index + 1,
                )
                for index, option_data in enumerate(options_data)
            ]
        )

    def _sync_question_answer(self, question, question_data):
        if question.question_type in {
            Question.QuestionType.MULTIPLE_CHOICE,
            Question.QuestionType.CHECKBOX,
            Question.QuestionType.ORDERING,
            Question.QuestionType.MATCHING,
            Question.QuestionType.FILL_IN_BLANK,
        }:
            QuestionAnswer.objects.filter(question=question).delete()
            return

        QuestionAnswer.objects.update_or_create(
            question=question,
            defaults={
                "answer_text": question_data.get("answer_text", ""),
                "keywords": question_data.get("keywords", []),
                "is_case_sensitive": bool(question_data.get("is_case_sensitive", False))
                if question.question_type == Question.QuestionType.SHORT_ANSWER
                else False,
                "max_word_count": question_data.get("max_word_count"),
            },
        )

    def _sync_question_ordering_items(self, question, ordering_items):
        if question.question_type != Question.QuestionType.ORDERING:
            QuestionOrderingItem.objects.filter(question=question).delete()
            return

        QuestionOrderingItem.objects.filter(question=question).delete()
        QuestionOrderingItem.objects.bulk_create(
            [
                QuestionOrderingItem(
                    question=question,
                    item_text=item_text,
                    correct_order=index,
                )
                for index, item_text in enumerate(ordering_items, start=1)
            ]
        )

    def _sync_question_matching_pairs(self, question, matching_pairs):
        if question.question_type != Question.QuestionType.MATCHING:
            QuestionMatchingPair.objects.filter(question=question).delete()
            return

        QuestionMatchingPair.objects.filter(question=question).delete()
        QuestionMatchingPair.objects.bulk_create(
            [
                QuestionMatchingPair(
                    question=question,
                    prompt_text=pair_data["prompt_text"],
                    answer_text=pair_data["answer_text"],
                    pair_order=index,
                )
                for index, pair_data in enumerate(matching_pairs, start=1)
            ]
        )

    def _sync_question_blank_answers(self, question, blank_answers):
        if question.question_type != Question.QuestionType.FILL_IN_BLANK:
            QuestionBlankAnswer.objects.filter(question=question).delete()
            return

        QuestionBlankAnswer.objects.filter(question=question).delete()
        QuestionBlankAnswer.objects.bulk_create(
            [
                QuestionBlankAnswer(
                    question=question,
                    blank_number=int(blank_data["blank_number"]),
                    accepted_answers=list(blank_data.get("accepted_answers") or []),
                    is_case_sensitive=bool(blank_data.get("is_case_sensitive", False)),
                    blank_points=blank_data.get("blank_points"),
                )
                for blank_data in blank_answers
            ]
        )

    def _sync_question_tags(self, question, tag_names):
        QuestionTagRelation.objects.filter(question=question).delete()
        for tag_name in dict.fromkeys(tag_names):
            tag, _ = QuestionTag.objects.get_or_create(name=tag_name)
            QuestionTagRelation.objects.create(question=question, tag=tag)

    def create_question_bank(self, question_bank, teachers, subjects):
        for question_data in question_bank:
            try:
                teacher = teachers[question_data["teacher_username"]]
                subject = subjects[question_data["subject_code"]]
            except KeyError as exc:
                raise CommandError(f"Unknown teacher or subject reference in question seed: {question_data}") from exc

            category = self._get_or_create_category(question_data["category"])
            question_type = question_data.get("question_type", Question.QuestionType.MULTIPLE_CHOICE)

            question, created = Question.objects.update_or_create(
                created_by=teacher,
                subject=subject,
                question_text=question_data["question_text"],
                defaults={
                    "category": category,
                    "question_type": question_type,
                    "points": question_data["points"],
                    "difficulty_level": question_data["difficulty_level"],
                    "explanation": question_data.get("explanation", ""),
                    "question_image_url": question_data.get("question_image_url", ""),
                    "audio_play_limit": question_data.get("audio_play_limit"),
                    "video_play_limit": question_data.get("video_play_limit"),
                    "checkbox_scoring": question_data.get(
                        "checkbox_scoring",
                        Question.CheckboxScoring.ALL_OR_NOTHING,
                    ),
                    "allow_previous": bool(question_data.get("allow_previous", True)),
                    "allow_next": bool(question_data.get("allow_next", True)),
                    "force_sequential": bool(question_data.get("force_sequential", False)),
                    "time_limit_seconds": question_data.get("time_limit_seconds"),
                    "is_active": True,
                    "is_deleted": False,
                },
            )

            self._sync_question_options(question, question_data.get("options", []))
            self._sync_question_ordering_items(question, question_data.get("ordering_items", []))
            self._sync_question_matching_pairs(question, question_data.get("matching_pairs", []))
            self._sync_question_blank_answers(question, question_data.get("blank_answers", []))
            self._sync_question_answer(question, question_data)
            self._sync_question_tags(question, question_data.get("tags", []))

            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} sample question: {subject.code} [{question.question_type}] - {question.question_text[:60]}"
                )
            )

    def create_system_settings(self):
        for setting_data in SYSTEM_SETTINGS:
            setting, created = SystemSetting.objects.get_or_create(
                setting_key=setting_data["setting_key"],
                defaults=setting_data,
            )
            action = "Created" if created else "Unchanged"
            self.stdout.write(self.style.SUCCESS(f"{action} setting: {setting.setting_key}"))
