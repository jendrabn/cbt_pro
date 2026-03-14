import json
from collections import Counter
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import UserProfile
from apps.exams.models import Class, Exam, ExamAssignment, ExamQuestion
from apps.exams.services import sync_classes_from_student_profiles
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

DATA_DIR = Path(__file__).resolve().parent / "data"
SUBJECTS_FILE = DATA_DIR / "subjects.json"
SYSTEM_SETTINGS_FILE = DATA_DIR / "system_settings.json"
EXAM_SEED_FILE = DATA_DIR / "exam_seed.json"
QUESTION_BANK_FILE = DATA_DIR / "question_bank.json"
OPTION_LETTERS = [choice.value for choice in QuestionOption.OptionLetter]
EXPECTED_TOPICS_PER_SUBJECT = 5
QUESTION_TYPE_SEQUENCE = [
    Question.QuestionType.MULTIPLE_CHOICE,
    Question.QuestionType.CHECKBOX,
    Question.QuestionType.ORDERING,
    Question.QuestionType.MATCHING,
    Question.QuestionType.FILL_IN_BLANK,
    Question.QuestionType.ESSAY,
    Question.QuestionType.SHORT_ANSWER,
]
POINTS_BY_TYPE = {
    Question.QuestionType.MULTIPLE_CHOICE: Decimal("5.00"),
    Question.QuestionType.CHECKBOX: Decimal("6.00"),
    Question.QuestionType.ORDERING: Decimal("6.00"),
    Question.QuestionType.MATCHING: Decimal("8.00"),
    Question.QuestionType.FILL_IN_BLANK: Decimal("6.00"),
    Question.QuestionType.ESSAY: Decimal("10.00"),
    Question.QuestionType.SHORT_ANSWER: Decimal("4.00"),
}
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


class Command(BaseCommand):
    help = "Seed data simulasi BUMN dan CPNS dengan bank soal 35 soal per subject untuk setiap guru."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting database seeding..."))
        subject_rows = self._load_subjects()
        system_setting_rows = self._load_system_settings()
        exam_config = self._load_exam_seed()
        question_bank = self._load_question_bank(subject_rows)
        self._category_cache = {}
        self._tag_cache = {}

        self.create_admin_user()
        teachers = self.create_teacher_users()
        students = self.create_student_users()
        subjects = self.create_subjects(subject_rows)
        classes = self.sync_seed_classes()
        self.create_question_bank(question_bank=question_bank, teachers=teachers, subjects=subjects)
        self.create_teacher_exams(
            exam_config=exam_config,
            teacher_rows=TEACHER_ACCOUNTS,
            teachers=teachers,
            subject_rows=subject_rows,
            subjects=subjects,
            classes=classes,
            students=students,
        )
        self.create_system_settings(system_setting_rows)
        self.stdout.write(self.style.SUCCESS("Database seeding completed."))

    def _load_json_file(self, file_path, *, expected_type=dict):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise CommandError(f"Seed file not found: {file_path}") from exc
        except json.JSONDecodeError as exc:
            raise CommandError(f"Seed file is not valid JSON ({file_path.name}): {exc}") from exc
        if not isinstance(payload, expected_type):
            raise CommandError(
                f"Seed file {file_path.name} must be a JSON {expected_type.__name__}."
            )
        return payload

    def _load_subjects(self):
        payload = self._load_json_file(SUBJECTS_FILE, expected_type=list)
        if not payload:
            raise CommandError(f"{SUBJECTS_FILE.name} must contain at least one subject.")
        return payload

    def _load_system_settings(self):
        payload = self._load_json_file(SYSTEM_SETTINGS_FILE, expected_type=list)
        if not payload:
            raise CommandError(f"{SYSTEM_SETTINGS_FILE.name} must contain at least one setting.")
        return payload

    def _load_exam_seed(self):
        payload = self._load_json_file(EXAM_SEED_FILE, expected_type=dict)
        required_keys = {
            "days_per_exam",
            "duration_minutes",
            "passing_score",
            "allow_retake",
            "max_retake_attempts",
            "retake_score_policy",
            "retake_cooldown_minutes",
            "allow_review",
            "show_results_immediately",
            "question_navigation_override",
            "randomize_questions",
            "randomize_options",
            "require_fullscreen",
            "require_camera",
            "require_microphone",
            "detect_tab_switch",
            "disable_right_click",
            "block_copy_paste",
            "enable_screenshot_proctoring",
            "max_violations_allowed",
            "title_template",
            "description_template",
            "instructions_template",
        }
        missing = required_keys - set(payload.keys())
        if missing:
            raise CommandError(
                f"Exam seed config is missing required keys: {', '.join(sorted(missing))}"
            )
        return payload

    def _load_question_bank(self, subject_rows):
        configured_subject_codes = [row["code"] for row in subject_rows]
        payload = self._load_json_file(QUESTION_BANK_FILE, expected_type=dict)
        subject_packs = payload.get("subjects")
        if not isinstance(subject_packs, list):
            raise CommandError(
                f"{QUESTION_BANK_FILE.name} must contain a 'subjects' array."
            )

        question_bank = {}
        for subject_pack in subject_packs:
            if not isinstance(subject_pack, dict):
                raise CommandError(
                    f"Each item in {QUESTION_BANK_FILE.name}['subjects'] must be an object."
                )
            subject_code = str(subject_pack.get("subject_code") or "").strip()
            topics = subject_pack.get("topics")
            if not subject_code:
                raise CommandError(
                    f"Each subject pack in {QUESTION_BANK_FILE.name} must contain subject_code."
                )
            if subject_code in question_bank:
                raise CommandError(f"Duplicate question pack for subject {subject_code}.")
            if subject_code not in configured_subject_codes:
                raise CommandError(
                    f"Question pack {QUESTION_BANK_FILE.name} references unknown subject {subject_code}."
                )
            if not isinstance(topics, list) or len(topics) != EXPECTED_TOPICS_PER_SUBJECT:
                raise CommandError(
                    f"Question pack {QUESTION_BANK_FILE.name} for {subject_code} must contain exactly "
                    f"{EXPECTED_TOPICS_PER_SUBJECT} topics."
                )
            question_bank[subject_code] = topics

        missing_subject_codes = sorted(set(configured_subject_codes) - set(question_bank.keys()))
        if missing_subject_codes:
            raise CommandError(
                f"Missing question packs for subject codes: {', '.join(missing_subject_codes)}"
            )

        total_topic_count = sum(len(items) for items in question_bank.values())
        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {len(question_bank)} subject packs and {total_topic_count} compact topic seeds."
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
            "is_staff": is_superuser,
            "is_superuser": is_superuser,
        }
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
        for row in TEACHER_ACCOUNTS:
            user = self._upsert_user(row, User.Role.TEACHER)
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "teacher_id": row["teacher_id"],
                    "subject_specialization": row["subject_specialization"],
                },
            )
            teachers[row["username"]] = user
        return teachers

    def create_student_users(self):
        students = {}
        for row in STUDENT_ACCOUNTS:
            user = self._upsert_user(row, User.Role.STUDENT)
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "student_id": row["student_id"],
                    "class_grade": row["class_grade"],
                },
            )
            students[row["username"]] = user
        return students

    def create_subjects(self, subject_rows):
        subject_map = {}
        for row in subject_rows:
            subject, created = Subject.objects.get_or_create(
                code=row["code"],
                defaults={
                    "name": row["name"],
                    "description": row.get("description", ""),
                },
            )
            changed_fields = []
            for field, value in {
                "name": row["name"],
                "description": row.get("description", ""),
            }.items():
                if getattr(subject, field) != value:
                    setattr(subject, field, value)
                    changed_fields.append(field)
            if changed_fields:
                subject.save(update_fields=changed_fields + ["updated_at"])
            action = "Created" if created else "Updated" if changed_fields else "Unchanged"
            self.stdout.write(self.style.SUCCESS(f"{action} subject: {subject.name}"))
            subject_map[row["code"]] = subject
        return subject_map

    def sync_seed_classes(self):
        sync_classes_from_student_profiles()
        classes = list(Class.objects.order_by("name"))
        self.stdout.write(self.style.SUCCESS(f"Prepared {len(classes)} classes for exam assignment."))
        return classes

    def _get_or_create_category(self, name):
        if name in self._category_cache:
            return self._category_cache[name]
        category, _ = QuestionCategory.objects.get_or_create(
            name=name,
            parent=None,
            defaults={
                "description": f"Kategori seed untuk {name}.",
                "is_active": True,
            },
        )
        if not category.is_active:
            category.is_active = True
            category.save(update_fields=["is_active", "updated_at"])
        self._category_cache[name] = category
        return category

    def _get_or_create_tag(self, tag_name):
        normalized = (tag_name or "").strip()
        if not normalized:
            return None
        if normalized in self._tag_cache:
            return self._tag_cache[normalized]
        tag, _ = QuestionTag.objects.get_or_create(name=normalized)
        self._tag_cache[normalized] = tag
        return tag

    def _sync_question_options(self, question, options_data):
        if question.question_type not in {
            Question.QuestionType.MULTIPLE_CHOICE,
            Question.QuestionType.CHECKBOX,
        }:
            QuestionOption.objects.filter(question=question).delete()
            return

        if len(options_data) > len(OPTION_LETTERS):
            raise CommandError(f"Question '{question.question_text[:40]}' has too many options.")

        QuestionOption.objects.filter(question=question).delete()
        QuestionOption.objects.bulk_create(
            [
                QuestionOption(
                    question=question,
                    option_letter=OPTION_LETTERS[index],
                    option_text=row["text"],
                    option_image_url=row.get("image_url", ""),
                    is_correct=row["is_correct"],
                    display_order=index + 1,
                )
                for index, row in enumerate(options_data)
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
                "is_case_sensitive": False,
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
                    prompt_text=row["prompt"],
                    answer_text=row["answer"],
                    pair_order=index,
                )
                for index, row in enumerate(matching_pairs, start=1)
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
                    blank_number=int(row["blank_number"]),
                    accepted_answers=list(row.get("accepted_answers") or []),
                    is_case_sensitive=False,
                    blank_points=Decimal(str(row.get("blank_points") or 0)),
                )
                for row in blank_answers
            ]
        )

    def _sync_question_tags(self, question, tag_names):
        QuestionTagRelation.objects.filter(question=question).delete()
        for tag_name in dict.fromkeys(tag_names):
            tag = self._get_or_create_tag(tag_name)
            if tag:
                QuestionTagRelation.objects.create(question=question, tag=tag)

    def _topic_tag_list(self, subject_row, topic_row, question_type):
        return [
            subject_row["code"].lower(),
            slugify(subject_row["name"])[:50],
            slugify(topic_row["title"])[:50],
            question_type.replace("_", "-"),
        ]

    def _derive_keywords(self, topic_row):
        keywords = [topic_row["key_term"], topic_row["title"]]
        for token in str(topic_row.get("summary", "")).split():
            normalized = token.strip(".,:;!?()").lower()
            if normalized and len(normalized) > 4:
                keywords.append(normalized)
            if len(keywords) >= 5:
                break
        return list(dict.fromkeys(item for item in keywords if item))

    def _build_question_payloads_for_subject(self, subject_row, topic_rows):
        payloads = []
        for topic in topic_rows:
            difficulty = topic.get("difficulty", Question.Difficulty.MEDIUM)
            category_name = f"{subject_row['code']} - {topic['title']}"
            common = {
                "category_name": category_name,
                "difficulty_level": difficulty,
                "explanation": topic.get("summary", ""),
                "allow_previous": True,
                "allow_next": True,
                "force_sequential": False,
                "checkbox_scoring": Question.CheckboxScoring.PARTIAL_NO_PENALTY,
            }

            mc = topic["multiple_choice"]
            payloads.append(
                {
                    **common,
                    "question_type": Question.QuestionType.MULTIPLE_CHOICE,
                    "question_text": mc["question"],
                    "points": POINTS_BY_TYPE[Question.QuestionType.MULTIPLE_CHOICE],
                    "tags": self._topic_tag_list(subject_row, topic, Question.QuestionType.MULTIPLE_CHOICE),
                    "options": (
                        [{"text": mc["correct_option"], "is_correct": True}]
                        + [{"text": item, "is_correct": False} for item in mc["wrong_options"]]
                    ),
                }
            )

            checkbox = topic["checkbox"]
            payloads.append(
                {
                    **common,
                    "question_type": Question.QuestionType.CHECKBOX,
                    "question_text": checkbox["question"],
                    "points": POINTS_BY_TYPE[Question.QuestionType.CHECKBOX],
                    "tags": self._topic_tag_list(subject_row, topic, Question.QuestionType.CHECKBOX),
                    "options": (
                        [{"text": item, "is_correct": True} for item in checkbox["correct_options"]]
                        + [{"text": item, "is_correct": False} for item in checkbox["wrong_options"]]
                    ),
                }
            )

            ordering = topic["ordering"]
            payloads.append(
                {
                    **common,
                    "question_type": Question.QuestionType.ORDERING,
                    "question_text": ordering["question"],
                    "points": POINTS_BY_TYPE[Question.QuestionType.ORDERING],
                    "tags": self._topic_tag_list(subject_row, topic, Question.QuestionType.ORDERING),
                    "ordering_items": ordering["items"],
                }
            )

            matching = topic["matching"]
            payloads.append(
                {
                    **common,
                    "question_type": Question.QuestionType.MATCHING,
                    "question_text": matching["question"],
                    "points": POINTS_BY_TYPE[Question.QuestionType.MATCHING],
                    "tags": self._topic_tag_list(subject_row, topic, Question.QuestionType.MATCHING),
                    "matching_pairs": matching["pairs"],
                }
            )

            fill_in_blank = topic["fill_in_blank"]
            payloads.append(
                {
                    **common,
                    "question_type": Question.QuestionType.FILL_IN_BLANK,
                    "question_text": fill_in_blank["question"],
                    "points": POINTS_BY_TYPE[Question.QuestionType.FILL_IN_BLANK],
                    "tags": self._topic_tag_list(subject_row, topic, Question.QuestionType.FILL_IN_BLANK),
                    "blank_answers": fill_in_blank["answers"],
                }
            )

            payloads.append(
                {
                    **common,
                    "question_type": Question.QuestionType.ESSAY,
                    "question_text": f"Jelaskan inti materi {topic['title']} dalam konteks {subject_row['name']}.",
                    "points": POINTS_BY_TYPE[Question.QuestionType.ESSAY],
                    "tags": self._topic_tag_list(subject_row, topic, Question.QuestionType.ESSAY),
                    "answer_text": topic.get("summary", ""),
                    "keywords": self._derive_keywords(topic),
                    "max_word_count": 140,
                }
            )

            payloads.append(
                {
                    **common,
                    "question_type": Question.QuestionType.SHORT_ANSWER,
                    "question_text": f"Apa istilah utama yang paling terkait dengan materi {topic['title']}?",
                    "points": POINTS_BY_TYPE[Question.QuestionType.SHORT_ANSWER],
                    "tags": self._topic_tag_list(subject_row, topic, Question.QuestionType.SHORT_ANSWER),
                    "answer_text": topic["key_term"],
                    "keywords": list(dict.fromkeys([topic["key_term"], str(topic["key_term"]).lower()])),
                    "max_word_count": max(3, len(str(topic["key_term"]).split()) + 1),
                }
            )

        type_counts = Counter(row["question_type"] for row in payloads)
        for question_type in QUESTION_TYPE_SEQUENCE:
            if type_counts[question_type] != EXPECTED_TOPICS_PER_SUBJECT:
                raise CommandError(
                    f"Generated {type_counts[question_type]} questions for {subject_row['code']} {question_type}; "
                    f"expected {EXPECTED_TOPICS_PER_SUBJECT}."
                )
        return payloads

    def create_question_bank(self, question_bank, teachers, subjects):
        subject_rows = [
            {"code": code, "name": subject.name}
            for code, subject in subjects.items()
        ]
        subject_row_map = {row["code"]: row for row in subject_rows}
        total_processed = 0

        for teacher in teachers.values():
            for subject_code, subject in subjects.items():
                topic_rows = question_bank[subject_code]
                payloads = self._build_question_payloads_for_subject(subject_row_map[subject_code], topic_rows)
                created_count = 0
                updated_count = 0
                for question_data in payloads:
                    category = self._get_or_create_category(question_data["category_name"])
                    question, created = Question.objects.update_or_create(
                        created_by=teacher,
                        subject=subject,
                        question_text=question_data["question_text"],
                        defaults={
                            "category": category,
                            "question_type": question_data["question_type"],
                            "points": question_data["points"],
                            "difficulty_level": question_data["difficulty_level"],
                            "explanation": question_data.get("explanation", ""),
                            "question_image_url": "",
                            "audio_play_limit": None,
                            "video_play_limit": None,
                            "checkbox_scoring": question_data.get(
                                "checkbox_scoring",
                                Question.CheckboxScoring.ALL_OR_NOTHING,
                            ),
                            "allow_previous": question_data.get("allow_previous", True),
                            "allow_next": question_data.get("allow_next", True),
                            "force_sequential": question_data.get("force_sequential", False),
                            "time_limit_seconds": None,
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
                    total_processed += 1
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Question pack synced: {teacher.username} | {subject.code} | "
                        f"{len(payloads)} items ({created_count} created, {updated_count} updated)"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f"Processed {total_processed} question payloads across all teachers.")
        )

    def _ordered_questions_for_exam(self, teacher, subject):
        ordered_rows = []
        for question_type in QUESTION_TYPE_SEQUENCE:
            rows = list(
                Question.objects.filter(
                    created_by=teacher,
                    subject=subject,
                    question_type=question_type,
                    is_deleted=False,
                    is_active=True,
                ).order_by("question_text")
            )
            ordered_rows.extend(rows)

        expected_total = EXPECTED_TOPICS_PER_SUBJECT * len(QUESTION_TYPE_SEQUENCE)
        if len(ordered_rows) != expected_total:
            raise CommandError(
                f"Teacher {teacher.username} subject {subject.code} has {len(ordered_rows)} questions; "
                f"expected {expected_total}."
            )
        return ordered_rows

    def create_teacher_exams(self, exam_config, teacher_rows, teachers, subject_rows, subjects, classes, students):
        days_per_exam = int(exam_config["days_per_exam"])
        duration_minutes = int(exam_config["duration_minutes"])
        schedule_start = timezone.localtime(timezone.now()).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        student_list = list(students.values())

        for teacher_row in teacher_rows:
            teacher = teachers[teacher_row["username"]]
            for index, subject_row in enumerate(subject_rows, start=1):
                subject = subjects[subject_row["code"]]
                start_time = schedule_start + timedelta(days=(index - 1) * days_per_exam)
                end_time = start_time + timedelta(days=days_per_exam)
                title = exam_config["title_template"].format(index=index, subject_name=subject.name)
                description = exam_config["description_template"].format(
                    subject_name=subject.name,
                    days_per_exam=days_per_exam,
                )
                instructions = exam_config["instructions_template"].format(
                    subject_name=subject.name,
                    days_per_exam=days_per_exam,
                    max_retake_attempts=exam_config["max_retake_attempts"],
                )

                exam, created = Exam.objects.update_or_create(
                    created_by=teacher,
                    title=title,
                    defaults={
                        "subject": subject,
                        "description": description,
                        "instructions": instructions,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_minutes": duration_minutes,
                        "passing_score": Decimal(str(exam_config["passing_score"])),
                        "randomize_questions": bool(exam_config["randomize_questions"]),
                        "randomize_options": bool(exam_config["randomize_options"]),
                        "show_results_immediately": bool(exam_config["show_results_immediately"]),
                        "allow_review": bool(exam_config["allow_review"]),
                        "allow_retake": bool(exam_config["allow_retake"]),
                        "max_retake_attempts": int(exam_config["max_retake_attempts"]),
                        "retake_score_policy": exam_config["retake_score_policy"],
                        "retake_cooldown_minutes": int(exam_config["retake_cooldown_minutes"]),
                        "retake_show_review": True,
                        "certificate_enabled": False,
                        "certificate_template": None,
                        "override_question_navigation": bool(exam_config["question_navigation_override"]),
                        "global_allow_previous": True,
                        "global_allow_next": True,
                        "global_force_sequential": False,
                        "require_fullscreen": bool(exam_config["require_fullscreen"]),
                        "require_camera": bool(exam_config["require_camera"]),
                        "require_microphone": bool(exam_config["require_microphone"]),
                        "detect_tab_switch": bool(exam_config["detect_tab_switch"]),
                        "disable_right_click": bool(exam_config["disable_right_click"]),
                        "block_copy_paste": bool(exam_config["block_copy_paste"]),
                        "enable_screenshot_proctoring": bool(exam_config["enable_screenshot_proctoring"]),
                        "screenshot_interval_seconds": 300,
                        "max_violations_allowed": int(exam_config["max_violations_allowed"]),
                        "status": Exam.Status.PUBLISHED,
                    },
                )

                questions = self._ordered_questions_for_exam(teacher, subject)
                ExamQuestion.objects.filter(exam=exam).delete()
                total_points = Decimal("0.00")
                exam_question_rows = []
                for display_order, question in enumerate(questions, start=1):
                    points_value = Decimal(str(question.points))
                    total_points += points_value
                    exam_question_rows.append(
                        ExamQuestion(
                            exam=exam,
                            question=question,
                            display_order=display_order,
                            points_override=points_value,
                            override_navigation=False,
                        )
                    )
                ExamQuestion.objects.bulk_create(exam_question_rows)

                ExamAssignment.objects.filter(exam=exam).delete()
                if classes:
                    ExamAssignment.objects.bulk_create(
                        [
                            ExamAssignment(
                                exam=exam,
                                assigned_to_type=ExamAssignment.AssignmentType.CLASS,
                                class_obj=class_obj,
                            )
                            for class_obj in classes
                        ]
                    )
                else:
                    ExamAssignment.objects.bulk_create(
                        [
                            ExamAssignment(
                                exam=exam,
                                assigned_to_type=ExamAssignment.AssignmentType.STUDENT,
                                student=student,
                            )
                            for student in student_list
                        ]
                    )

                exam.total_points = total_points
                exam.save(update_fields=["total_points", "updated_at"])
                action = "Created" if created else "Updated"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{action} exam: {teacher.username} | {title} | {len(questions)} questions"
                    )
                )

    def create_system_settings(self, setting_rows):
        for row in setting_rows:
            setting, created = SystemSetting.objects.get_or_create(
                setting_key=row["setting_key"],
                defaults=row,
            )
            changed_fields = []
            for field, value in row.items():
                if getattr(setting, field) != value:
                    setattr(setting, field, value)
                    changed_fields.append(field)
            if changed_fields:
                setting.save(update_fields=changed_fields + ["updated_at"])
            action = "Created" if created else "Updated" if changed_fields else "Unchanged"
            self.stdout.write(self.style.SUCCESS(f"{action} setting: {setting.setting_key}"))
