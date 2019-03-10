from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone as djtimezone

from .validators import validate_noexam


class Course(models.Model):
    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=100, default=None)

    @property
    def title(self):
        return f"{self.code} - {self.name}"

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("code",)


class Department(models.Model):
    code = models.CharField(max_length=4, unique=True)
    name_en = models.CharField(max_length=50)
    name_tr = models.CharField(max_length=50)

    def __str__(self):
        return self.code

    class Meta:
        ordering = ("code",)


class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, null=True
    )
    tckn = models.BigIntegerField(null=True)

    def __str__(self):
        return (
            f"{self.user.username}"
            f" - {self.user.first_name} {self.user.last_name}"
        )


class Instructor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True
    )
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)


class Assistant(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.user.username

    class Meta:
        ordering = ("slug",)


class Classroom(models.Model):
    name = models.CharField(max_length=6, unique=True)
    soft_capacity = models.PositiveSmallIntegerField(default=0)
    capacity = models.PositiveSmallIntegerField(default=0)
    block = models.CharField(max_length=2)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)


class AcademicYear(models.Model):
    YEAR_CHOICES = []
    for r in range(2017, (datetime.now().year + 1)):
        YEAR_CHOICES.append((r, f"{r}-{r+1}"))

    SEMESTER_CHOICES = [
        ("fall", "Fall"),
        ("spring", "Spring"),
        ("summer", "Summer School"),
    ]

    year = models.PositiveSmallIntegerField(choices=YEAR_CHOICES)
    semester = models.CharField(max_length=6, choices=SEMESTER_CHOICES)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.active:
            AcademicYear.objects.filter(active=True).update(active=False)
            Period.objects.exclude(academic_year=self).update(active=False)
        super(AcademicYear, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_year_display()} {self.get_semester_display()}"

    class Meta:
        unique_together = ("year", "semester")


class Period(models.Model):
    PERIOD_CHOICES = [
        ("midterm", "Midterm"),
        ("makeup", "Make-up"),
        ("final", "Final"),
        ("resit", "Resit"),
    ]
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.active:
            Period.objects.filter(active=True).update(active=False)
            AcademicYear.objects.exclude(pk=self.academic_year.pk).update(
                active=False
            )
            AcademicYear.objects.filter(pk=self.academic_year.pk).update(
                active=True
            )
        super(Period, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.academic_year} {self.get_period_display()}"

    class Meta:
        unique_together = ("academic_year", "period")


class ActiveYearManager(models.Manager):
    def get_queryset(self):
        return (
            super(ActiveYearManager, self)
            .get_queryset()
            .filter(academic_year=AcademicYear.objects.get(active=True))
        )


class Offering(models.Model):
    SECTION_CHOICES = [(i, i) for i in range(1, 11)]
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    section = models.PositiveSmallIntegerField(choices=SECTION_CHOICES)
    instructors = models.ManyToManyField(Instructor)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    objects = models.Manager()
    active_year_objects = ActiveYearManager()
    instructor_in_charge = models.ForeignKey(
        Instructor,
        on_delete=models.CASCADE,
        related_name="instructor_in_charge",
    )

    class Meta:
        unique_together = (
            ("course", "department", "section", "academic_year"),
        )

    def __str__(self):
        return f"{self.course.code} - {self.department.code} - {self.section}"


class ActivePeriodManager(models.Manager):
    def get_queryset(self):
        return (
            super(ActivePeriodManager, self)
            .get_queryset()
            .filter(period=Period.objects.get(active=True))
        )


class Exam(models.Model):
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    objects = models.Manager()
    active_period_objects = ActivePeriodManager()

    class Meta:
        unique_together = (("offering", "period"),)


class TimeCode(models.Model):
    short_code = models.PositiveSmallIntegerField()
    long_code = models.PositiveSmallIntegerField()
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    time = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = (
            ("short_code", "period"),
            ("long_code", "period"),
            ("time", "period"),
        )

    def __str__(self):
        return f"{self.long_code} - {self.period}"


class Timetable(models.Model):
    exam = models.OneToOneField(
        Exam, on_delete=models.CASCADE, validators=[validate_noexam]
    )
    session = models.ForeignKey(TimeCode, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        Timetable.objects.filter(
            exam__offering__course=self.exam.offering.course,
            exam__period=self.exam.period,
        ).update(session=self.session)
        super(Timetable, self).save(*args, **kwargs)

    @property
    def time_until(self):
        return (self.session.time - djtimezone.now()).total_seconds() / 60

    def __str__(self):
        return f"{self.id}"


class Sitting(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    assistants = models.ManyToManyField(
        Assistant, through="AssistantAssignment"
    )

    class Meta:
        unique_together = (("exam", "classroom"),)


class AssistantAssignment(models.Model):
    sitting = models.ForeignKey(Sitting, on_delete=models.CASCADE)
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    def __str__(self):
        return (
            f"{self.assistant.slug} {self.sitting.exam.offering.course.code}"
        )


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("student", "exam"),)

    def __str__(self):
        return "Enrollment {0:05}".format(self.id)


class Chair(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    COLUMN_CHOICES = [(col, col) for col in list("ABCDEF")]
    ROW_CHOICES = [(row, row) for row in range(1, 10)]
    column = models.CharField(max_length=1, choices=COLUMN_CHOICES)
    row = models.PositiveSmallIntegerField(choices=ROW_CHOICES)
    assign_order = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = (
            ("classroom", "column", "row"),
            ("classroom", "assign_order"),
        )

    def __str__(self):
        return f"{self.classroom.name} {self.column}{self.row}"


class Layout(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    sitting = models.ForeignKey(Sitting, on_delete=models.CASCADE)
    chair = models.ForeignKey(
        Chair, on_delete=models.CASCADE, null=True, blank=True
    )

    def clean(self):
        if self.chair and (self.chair.classroom != self.sitting.classroom):
            raise ValidationError(
                "Classroom for sitting and chair are not the same"
            )

    def __str__(self):
        return f"{self.student} - {self.sitting}"

    class Meta:
        unique_together = (("student", "sitting"), ("sitting", "chair"))


class NoExam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("course", "period"),)

    def __str__(self):
        return f"{self.course} - {self.period}"


class AssistedCourse(models.Model):
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE)
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.assistant.slug} -> {self.offering.course.code}"
