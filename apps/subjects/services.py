from django.db.models import Count, Q

from .models import Subject


def annotate_subject_usage(queryset=None):
    if queryset is None:
        queryset = Subject.objects.all()
    return queryset.annotate(
        question_count=Count("questions", filter=Q(questions__is_deleted=False), distinct=True),
        exam_count=Count("exams", filter=Q(exams__is_deleted=False), distinct=True),
    )


def get_subject_usage_summary(subject_id):
    from apps.attempts.models import ExamAttempt, ExamViolation, ProctoringScreenshot, StudentAnswer
    from apps.exams.models import ExamAssignment, ExamQuestion
    from apps.questions.models import Question, QuestionOption
    from apps.results.models import ExamResult

    questions_count = Question.objects.filter(subject_id=subject_id).count()
    question_options_count = QuestionOption.objects.filter(question__subject_id=subject_id).count()
    exams_count = Subject.objects.filter(id=subject_id).aggregate(total=Count("exams"))["total"] or 0
    exam_questions_count = ExamQuestion.objects.filter(exam__subject_id=subject_id).count()
    exam_assignments_count = ExamAssignment.objects.filter(exam__subject_id=subject_id).count()
    exam_attempts_count = ExamAttempt.objects.filter(exam__subject_id=subject_id).count()
    student_answers_count = StudentAnswer.objects.filter(attempt__exam__subject_id=subject_id).count()
    exam_results_count = ExamResult.objects.filter(attempt__exam__subject_id=subject_id).count()
    violations_count = ExamViolation.objects.filter(attempt__exam__subject_id=subject_id).count()
    screenshots_count = ProctoringScreenshot.objects.filter(attempt__exam__subject_id=subject_id).count()

    return {
        "questions_count": questions_count,
        "question_options_count": question_options_count,
        "exams_count": exams_count,
        "exam_questions_count": exam_questions_count,
        "exam_assignments_count": exam_assignments_count,
        "exam_attempts_count": exam_attempts_count,
        "student_answers_count": student_answers_count,
        "exam_results_count": exam_results_count,
        "violations_count": violations_count,
        "screenshots_count": screenshots_count,
    }


def list_subjects_for_dropdown(active_only=True):
    queryset = Subject.objects.all()
    if active_only:
        queryset = queryset.filter(is_active=True)
    return queryset.order_by("name")

