from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import UserProfile
from apps.notifications.models import SystemSetting
from apps.questions.models import (
    Question,
    QuestionAnswer,
    QuestionCategory,
    QuestionOption,
    QuestionTag,
    QuestionTagRelation,
)
from apps.subjects.models import Subject

User = get_user_model()

OPTION_LETTERS = [choice.value for choice in QuestionOption.OptionLetter]

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

QUESTION_BANK = [
    {
        "subject_code": "ALG2",
        "teacher_username": "olivia.carter",
        "category": "Linear Equations",
        "question_text": "Solve for x: 2x + 5 = 17",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "Subtract 5 from both sides to get 2x = 12, then divide by 2.",
        "tags": ["algebra", "linear-equations"],
        "options": [
            {"text": "4", "is_correct": False},
            {"text": "5", "is_correct": False},
            {"text": "6", "is_correct": True},
            {"text": "7", "is_correct": False},
        ],
    },
    {
        "subject_code": "ALG2",
        "teacher_username": "olivia.carter",
        "category": "Quadratic Expressions",
        "question_text": "Which expression is equivalent to x^2 - 5x + 6?",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 5,
        "explanation": "Look for two numbers that multiply to 6 and add to -5.",
        "tags": ["algebra", "factoring", "quadratics"],
        "options": [
            {"text": "(x - 2)(x - 3)", "is_correct": True},
            {"text": "(x + 2)(x + 3)", "is_correct": False},
            {"text": "(x - 1)(x - 6)", "is_correct": False},
            {"text": "(x + 1)(x + 6)", "is_correct": False},
        ],
    },
    {
        "subject_code": "GEOM",
        "teacher_username": "olivia.carter",
        "category": "Angle Relationships",
        "question_text": "What is the sum of the interior angles of any triangle?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "All triangles have interior angles that add up to 180 degrees.",
        "tags": ["geometry", "angles"],
        "options": [
            {"text": "90 degrees", "is_correct": False},
            {"text": "180 degrees", "is_correct": True},
            {"text": "270 degrees", "is_correct": False},
            {"text": "360 degrees", "is_correct": False},
        ],
    },
    {
        "subject_code": "BIO",
        "teacher_username": "michael.reed",
        "category": "Cell Biology",
        "question_text": "Which organelle is known as the powerhouse of the cell?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "Mitochondria produce ATP, which cells use for energy.",
        "tags": ["biology", "cells"],
        "options": [
            {"text": "Nucleus", "is_correct": False},
            {"text": "Mitochondrion", "is_correct": True},
            {"text": "Ribosome", "is_correct": False},
            {"text": "Golgi apparatus", "is_correct": False},
        ],
    },
    {
        "subject_code": "CHEM",
        "teacher_username": "michael.reed",
        "category": "Atomic Structure",
        "question_text": "What is the atomic number of oxygen?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "Atomic number tells you how many protons are in the nucleus. Oxygen has 8.",
        "tags": ["chemistry", "atoms"],
        "options": [
            {"text": "6", "is_correct": False},
            {"text": "7", "is_correct": False},
            {"text": "8", "is_correct": True},
            {"text": "9", "is_correct": False},
        ],
    },
    {
        "subject_code": "PHYS",
        "teacher_username": "michael.reed",
        "category": "Forces and Motion",
        "question_text": "A net force of 20 N acts on a 4 kg object. What is the acceleration?",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 5,
        "explanation": "Use Newton's second law: a = F / m = 20 / 4 = 5.",
        "tags": ["physics", "newton-laws", "motion"],
        "options": [
            {"text": "4 m/s^2", "is_correct": False},
            {"text": "5 m/s^2", "is_correct": True},
            {"text": "8 m/s^2", "is_correct": False},
            {"text": "16 m/s^2", "is_correct": False},
        ],
    },
    {
        "subject_code": "ENG-LIT",
        "teacher_username": "sophia.bennett",
        "category": "Literary Devices",
        "question_text": "What is a metaphor?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "A metaphor compares two unlike things without using 'like' or 'as'.",
        "tags": ["english", "literary-devices"],
        "options": [
            {"text": "A comparison using 'like' or 'as'", "is_correct": False},
            {"text": "A direct comparison without using 'like' or 'as'", "is_correct": True},
            {"text": "An exaggeration used for emphasis", "is_correct": False},
            {"text": "A repeated consonant sound", "is_correct": False},
        ],
    },
    {
        "subject_code": "ENG-LIT",
        "teacher_username": "sophia.bennett",
        "category": "Reading Analysis",
        "question_text": "Which statement best describes the theme of a story?",
        "difficulty_level": Question.Difficulty.MEDIUM,
        "points": 5,
        "explanation": "Theme is the central message or insight a reader can take from the story.",
        "tags": ["english", "theme", "reading-analysis"],
        "options": [
            {"text": "The list of characters in the story", "is_correct": False},
            {"text": "The lesson or central message explored by the story", "is_correct": True},
            {"text": "The place where the story happens", "is_correct": False},
            {"text": "The order of events in the plot", "is_correct": False},
        ],
    },
    {
        "subject_code": "USHIST",
        "teacher_username": "sophia.bennett",
        "category": "Founding Documents",
        "question_text": "What is the name of the first ten amendments to the U.S. Constitution?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "The first ten amendments are collectively called the Bill of Rights.",
        "tags": ["history", "constitution", "government"],
        "options": [
            {"text": "The Federalist Papers", "is_correct": False},
            {"text": "The Articles of Confederation", "is_correct": False},
            {"text": "The Bill of Rights", "is_correct": True},
            {"text": "The Emancipation Proclamation", "is_correct": False},
        ],
    },
    {
        "subject_code": "CS",
        "teacher_username": "sophia.bennett",
        "category": "Programming Fundamentals",
        "question_text": "In Python, what does len([3, 4, 5]) return?",
        "difficulty_level": Question.Difficulty.EASY,
        "points": 5,
        "explanation": "The len function returns the number of items in a list. This list has 3 items.",
        "tags": ["computer-science", "python", "lists"],
        "options": [
            {"text": "2", "is_correct": False},
            {"text": "3", "is_correct": True},
            {"text": "4", "is_correct": False},
            {"text": "12", "is_correct": False},
        ],
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
    help = "Seed demo data with sample users, U.S. high school subjects, and example questions."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting database seeding..."))

        self.create_admin_user()
        teachers = self.create_teacher_users()
        self.create_student_users()
        subjects = self.create_subjects()
        self.create_question_bank(teachers, subjects)
        self.create_system_settings()

        self.stdout.write(self.style.SUCCESS("Database seeding completed."))

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
            raise ValueError(f"Question '{question.question_text[:40]}' has too many options.")

        QuestionOption.objects.filter(question=question).delete()
        options = []
        for index, option_data in enumerate(options_data):
            options.append(
                QuestionOption(
                    question=question,
                    option_letter=OPTION_LETTERS[index],
                    option_text=option_data["text"],
                    option_image_url=option_data.get("image_url", ""),
                    is_correct=option_data["is_correct"],
                    display_order=index + 1,
                )
            )
        QuestionOption.objects.bulk_create(options)

    def _sync_question_tags(self, question, tag_names):
        QuestionTagRelation.objects.filter(question=question).delete()
        for tag_name in dict.fromkeys(tag_names):
            tag, _ = QuestionTag.objects.get_or_create(name=tag_name)
            QuestionTagRelation.objects.create(question=question, tag=tag)

    def create_question_bank(self, teachers, subjects):
        for question_data in QUESTION_BANK:
            teacher = teachers[question_data["teacher_username"]]
            subject = subjects[question_data["subject_code"]]
            category = self._get_or_create_category(question_data["category"])

            question, created = Question.objects.update_or_create(
                created_by=teacher,
                subject=subject,
                question_text=question_data["question_text"],
                defaults={
                    "category": category,
                    "question_type": Question.QuestionType.MULTIPLE_CHOICE,
                    "points": question_data["points"],
                    "difficulty_level": question_data["difficulty_level"],
                    "explanation": question_data["explanation"],
                    "question_image_url": question_data.get("question_image_url", ""),
                    "allow_previous": True,
                    "allow_next": True,
                    "force_sequential": False,
                    "time_limit_seconds": None,
                    "is_active": True,
                    "is_deleted": False,
                },
            )

            QuestionAnswer.objects.filter(question=question).delete()
            self._sync_question_options(question, question_data["options"])
            self._sync_question_tags(question, question_data["tags"])

            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} sample question: {subject.code} - {question.question_text[:60]}"
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
