from django.contrib import admin

from .models import AcademicYear
from .models import Assistant
from .models import AssistedCourse
from .models import Chair
from .models import Classroom
from .models import Course
from .models import Department
from .models import Enrollment
from .models import Exam
from .models import Instructor
from .models import Layout
from .models import NoExam
from .models import Offering
from .models import Period
from .models import Sitting
from .models import Student
from .models import TimeCode
from .models import Timetable


class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "exam_details", "get_period")

    def exam_details(self, obj):
        return f"{obj.exam.offering.course.title}"

    def get_period(self, obj):
        return f"{obj.exam.period}"


class OfferingAdmin(admin.ModelAdmin):
    list_display = (
        "course",
        "instructor_in_charge",
        "department",
        "section",
        "academic_year",
    )
    ordering = ("course",)
    list_filter = ("academic_year", "department")
    search_fields = ("course__code", "instructor_in_charge__name")


class ExamAdmin(admin.ModelAdmin):
    list_display = ("offering", "period")

    list_filter = ("period",)


class ChairAdmin(admin.ModelAdmin):
    list_display = ("classroom", "column", "row", "assign_order")
    list_filter = ("classroom", "column", "row")
    ordering = ("classroom", "column", "row")


class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    ordering = ("code",)


admin.site.register(AcademicYear)
admin.site.register(Assistant)
admin.site.register(AssistedCourse)
admin.site.register(Chair, ChairAdmin)
admin.site.register(Classroom)
admin.site.register(Course, CourseAdmin)
admin.site.register(Department)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(Instructor)
admin.site.register(Layout)
admin.site.register(NoExam)
admin.site.register(Offering, OfferingAdmin)
admin.site.register(Sitting)
admin.site.register(Student)
admin.site.register(Period)
admin.site.register(TimeCode)
admin.site.register(Timetable)
