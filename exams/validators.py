from django.core.exceptions import ValidationError


def validate_noexam(exam_pk):
    from .models import Exam, NoExam

    exam = Exam.objects.get(pk=exam_pk)
    qs = NoExam.objects.filter(course=exam.offering.course, period=exam.period)
    if qs.count() > 0:
        raise ValidationError(
            f"There is a NoExam record for {exam}.", params={"exam": exam}
        )
