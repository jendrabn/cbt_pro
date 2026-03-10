from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import models

from apps.accounts.models import User, UserImportLog
from apps.attempts.models import ExamAttempt, ExamViolation, StudentAnswer
from apps.exams.models import Exam, ExamAssignment
from apps.notifications.models import Notification, SystemLog, SystemSetting
from apps.questions.models import Question, QuestionImportLog


@dataclass(frozen=True)
class EnumBadgeDefinition:
    enum_cls: type[models.TextChoices]
    tones: dict[str, str]
    default_tone: str = "secondary"


def choice_label(enum_cls: type[models.TextChoices], value: Any, default: str = "") -> str:
    if value in (None, ""):
        return default
    try:
        return str(enum_cls(value).label)
    except ValueError:
        return default or str(value)


def choice_dict(enum_cls: type[models.TextChoices]) -> dict[str, str]:
    return {member.value: str(member.label) for member in enum_cls}


ENUM_BADGE_REGISTRY: dict[str, EnumBadgeDefinition] = {
    "user_role": EnumBadgeDefinition(
        enum_cls=User.Role,
        tones={
            User.Role.ADMIN: "danger",
            User.Role.TEACHER: "info",
            User.Role.STUDENT: "primary",
        },
    ),
    "user_import_status": EnumBadgeDefinition(
        enum_cls=UserImportLog.Status,
        tones={
            UserImportLog.Status.PENDING: "secondary",
            UserImportLog.Status.PROCESSING: "info",
            UserImportLog.Status.COMPLETED: "success",
            UserImportLog.Status.FAILED: "danger",
        },
    ),
    "exam_status": EnumBadgeDefinition(
        enum_cls=Exam.Status,
        tones={
            Exam.Status.DRAFT: "secondary",
            Exam.Status.PUBLISHED: "info",
            Exam.Status.ONGOING: "warning",
            Exam.Status.COMPLETED: "success",
            Exam.Status.CANCELLED: "danger",
        },
    ),
    "exam_retake_score_policy": EnumBadgeDefinition(
        enum_cls=Exam.RetakeScorePolicy,
        tones={
            Exam.RetakeScorePolicy.HIGHEST: "success",
            Exam.RetakeScorePolicy.LATEST: "info",
            Exam.RetakeScorePolicy.AVERAGE: "warning",
        },
    ),
    "exam_assignment_type": EnumBadgeDefinition(
        enum_cls=ExamAssignment.AssignmentType,
        tones={
            ExamAssignment.AssignmentType.CLASS: "info",
            ExamAssignment.AssignmentType.STUDENT: "primary",
        },
    ),
    "attempt_status": EnumBadgeDefinition(
        enum_cls=ExamAttempt.Status,
        tones={
            ExamAttempt.Status.NOT_STARTED: "secondary",
            ExamAttempt.Status.IN_PROGRESS: "warning",
            ExamAttempt.Status.SUBMITTED: "info",
            ExamAttempt.Status.AUTO_SUBMITTED: "danger",
            ExamAttempt.Status.GRADING: "primary",
            ExamAttempt.Status.COMPLETED: "success",
        },
    ),
    "answer_type": EnumBadgeDefinition(
        enum_cls=StudentAnswer.AnswerType,
        tones={
            StudentAnswer.AnswerType.MULTIPLE_CHOICE: "primary",
            StudentAnswer.AnswerType.CHECKBOX: "info",
            StudentAnswer.AnswerType.ORDERING: "warning",
            StudentAnswer.AnswerType.MATCHING: "primary",
            StudentAnswer.AnswerType.FILL_IN_BLANK: "secondary",
            StudentAnswer.AnswerType.ESSAY: "info",
            StudentAnswer.AnswerType.SHORT_ANSWER: "secondary",
        },
    ),
    "violation_type": EnumBadgeDefinition(
        enum_cls=ExamViolation.ViolationType,
        tones={
            ExamViolation.ViolationType.TAB_SWITCH: "warning",
            ExamViolation.ViolationType.FULLSCREEN_EXIT: "danger",
            ExamViolation.ViolationType.COPY_ATTEMPT: "warning",
            ExamViolation.ViolationType.PASTE_ATTEMPT: "warning",
            ExamViolation.ViolationType.RIGHT_CLICK: "secondary",
            ExamViolation.ViolationType.SUSPICIOUS_ACTIVITY: "danger",
        },
    ),
    "violation_severity": EnumBadgeDefinition(
        enum_cls=ExamViolation.Severity,
        tones={
            ExamViolation.Severity.LOW: "success",
            ExamViolation.Severity.MEDIUM: "warning",
            ExamViolation.Severity.HIGH: "danger",
            ExamViolation.Severity.CRITICAL: "danger",
        },
    ),
    "question_type": EnumBadgeDefinition(
        enum_cls=Question.QuestionType,
        tones={
            Question.QuestionType.MULTIPLE_CHOICE: "primary",
            Question.QuestionType.CHECKBOX: "info",
            Question.QuestionType.ORDERING: "warning",
            Question.QuestionType.MATCHING: "primary",
            Question.QuestionType.FILL_IN_BLANK: "secondary",
            Question.QuestionType.ESSAY: "info",
            Question.QuestionType.SHORT_ANSWER: "secondary",
        },
    ),
    "question_difficulty": EnumBadgeDefinition(
        enum_cls=Question.Difficulty,
        tones={
            Question.Difficulty.EASY: "success",
            Question.Difficulty.MEDIUM: "warning",
            Question.Difficulty.HARD: "danger",
        },
    ),
    "question_import_status": EnumBadgeDefinition(
        enum_cls=QuestionImportLog.Status,
        tones={
            QuestionImportLog.Status.PENDING: "secondary",
            QuestionImportLog.Status.PROCESSING: "info",
            QuestionImportLog.Status.COMPLETED: "success",
            QuestionImportLog.Status.FAILED: "danger",
        },
    ),
    "notification_type": EnumBadgeDefinition(
        enum_cls=Notification.Type,
        tones={
            Notification.Type.INFO: "info",
            Notification.Type.SUCCESS: "success",
            Notification.Type.WARNING: "warning",
            Notification.Type.ERROR: "danger",
            Notification.Type.ANNOUNCEMENT: "primary",
        },
    ),
    "system_setting_type": EnumBadgeDefinition(
        enum_cls=SystemSetting.SettingType,
        tones={
            SystemSetting.SettingType.STRING: "primary",
            SystemSetting.SettingType.NUMBER: "info",
            SystemSetting.SettingType.BOOLEAN: "warning",
            SystemSetting.SettingType.JSON: "success",
        },
    ),
    "system_log_level": EnumBadgeDefinition(
        enum_cls=SystemLog.Level,
        tones={
            SystemLog.Level.DEBUG: "secondary",
            SystemLog.Level.INFO: "info",
            SystemLog.Level.WARNING: "warning",
            SystemLog.Level.ERROR: "danger",
            SystemLog.Level.CRITICAL: "danger",
        },
    ),
}


def get_enum_badge_tone(kind: str, value: Any) -> str:
    definition = ENUM_BADGE_REGISTRY[kind]
    return definition.tones.get(str(value), definition.default_tone)


def get_enum_badge(kind: str, value: Any, *, label: str | None = None) -> dict[str, str]:
    definition = ENUM_BADGE_REGISTRY[kind]
    resolved_label = label if label is not None else choice_label(definition.enum_cls, value, default=str(value or "-"))
    return {
        "label": resolved_label,
        "tone": get_enum_badge_tone(kind, value),
    }
