from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.db.models.fields import DateField
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic import ListView

from .forms import SelectAssistantForm
from .forms import SelectClassroomForm
from .forms import SelectCourseForm
from .forms import SelectDepartmentForm
from .forms import SelectInstructorForm
from .forms import SelectStudentForm
from .models import AcademicYear
from .models import Assistant
from .models import AssistantAssignment
from .models import Classroom
from .models import Course
from .models import Department
from .models import Enrollment
from .models import Exam
from .models import Instructor
from .models import Layout
from .models import Period
from .models import Sitting
from .models import Student
from .models import TimeCode

PERIOD = Period.objects.get(active=True)
AY = AcademicYear.objects.get(active=True)


def exam_home(request):
    return redirect(f"/exams/student/")


def logout_view(request):
    logout(request)
    return redirect(f"/exams/student/")


def custom_login(request):
    if request.user.is_authenticated:
        messages.info(
            request,
            "You are already logged in as "
            f"{request.user.first_name} {request.user.last_name}."
            "If you want to login as a different user, please logout first.",
        )
        return exam_home(request)
    else:
        return login(request)


def is_assistant(user):
    return user.groups.filter(name="assistants").exists()


def is_administrative(user):
    return user.groups.filter(name="administratives").exists()


def is_student(user):
    return user.groups.filter(name="students").exists()


def select_student(request):
    if request.method == "POST":
        form = SelectStudentForm(request.POST)
        if form.is_valid():
            student_number = form.cleaned_data["student_number"]
            try:
                student = Student.objects.get(user__username=student_number)
                return redirect(f"../student/{student_number}")
            except Student.DoesNotExist:
                messages.info(
                    request,
                    f"{student_number} cannot be found in our system."
                    " Please make sure you have entered your student number"
                    " correctly. If you are an Erasmus student, please"
                    " check the examination times from the courses page.",
                )
                return redirect(f"../student/")
    else:
        form = SelectStudentForm()
    return render(request, "student/select_student.html", {"form": form})


class LayoutListView(ListView):
    model = Layout
    template_name = "student/layout_list.html"

    def get_queryset(self):
        self.student = get_object_or_404(
            Student, user__username=self.kwargs["student_number"]
        )
        qs = self.model.objects.filter(
            student=self.student, sitting__exam__period=PERIOD
        ).order_by("sitting__exam__timetable__session__time")
        return qs

    def dispatch(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if not qs:
            return redirect(f"../{self.student.user.username}/final/")
        else:
            return super(LayoutListView, self).dispatch(
                request, *args, **kwargs
            )


class EnrollmentListView(ListView):
    model = Enrollment
    template_name = "student/enrollment_list.html"

    def get_queryset(self):
        self.student = get_object_or_404(
            Student, user__username=self.kwargs["student_number"]
        )
        period = Period.objects.get(
            academic_year=AY, period=self.kwargs["period"]
        )
        return (
            self.model.objects.filter(
                student=self.student, exam__period=period
            )
            .order_by("exam__timetable__session__time")
            .exclude(exam__timetable__isnull=True)
        )


def select_instructor(request):
    if request.method == "POST":
        form = SelectInstructorForm(request.POST)
        if form.is_valid():
            instructor = form.cleaned_data["instructor"]
            return redirect(f"../instructor/{instructor.slug}")
    else:
        form = SelectInstructorForm()
    return render(request, "instructor/select_instructor.html", {"form": form})


class ExamListView(ListView):
    model = Exam
    template_name = "instructor/exam_list.html"

    def get_queryset(self):
        instructor = get_object_or_404(Instructor, slug=self.kwargs["slug"])
        return self.model.objects.filter(
            offering__instructor_in_charge=instructor,
            period=PERIOD,
            timetable__isnull=False,
        ).order_by(
            "timetable__session__time",
            "offering__course__code",
            "offering__department__code",
            "offering__section",
        )

    def get_context_data(self, *args, **kwargs):
        context = super(ExamListView, self).get_context_data(*args, **kwargs)
        instructor = get_object_or_404(Instructor, slug=self.kwargs["slug"])
        ay = AcademicYear.objects.get(active=True)
        context["all_exams"] = (
            self.model.objects.filter(
                offering__instructor_in_charge=instructor,
                timetable__isnull=False,
                offering__academic_year=ay,
            )
            .order_by(
                "offering__course__code", "period", "timetable__session__time"
            )
            .distinct("offering__course__code", "period")
        )
        context["period"] = PERIOD
        context["ay"] = ay
        return context


def select_assistant(request):
    if request.method == "POST":
        form = SelectAssistantForm(request.POST)
        if form.is_valid():
            assistant = form.cleaned_data["assistant"]
            return redirect(f"../assistant/{assistant.slug}")
    else:
        form = SelectAssistantForm()
    return render(request, "assistant/select_assistant.html", {"form": form})


class AssistantAssignmentListView(ListView):
    model = AssistantAssignment
    template_name = "assistant/assistantassignment_list.html"

    def get_queryset(self):
        self.assistant = get_object_or_404(Assistant, slug=self.kwargs["slug"])
        return self.model.objects.filter(
            assistant=self.assistant, sitting__exam__period=PERIOD
        ).order_by("sitting__exam__timetable__session__time")

    def get_context_data(self, **kwargs):
        context = super(AssistantAssignmentListView, self).get_context_data(
            **kwargs
        )
        qs = self.get_queryset()
        context["id"] = qs.first().id
        for obj in self.get_queryset():
            if obj.sitting.exam.timetable.time_until > -60:
                context["closest_id"] = obj.id
                break
        return context


def select_course(request):
    if request.method == "POST":
        form = SelectCourseForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data["course"]
            return redirect(f"../course/{course.pk}")
    else:
        form = SelectCourseForm()
    return render(request, "course/select_course.html", {"form": form})


class CourseListView(ListView):
    model = Course
    template_name = "course/course_list.html"

    def get_queryset(self):
        course = get_object_or_404(Course, pk=self.kwargs["pk"])
        return Exam.objects.filter(period=PERIOD, offering__course=course)


def select_department(request):
    if request.method == "POST":
        form = SelectDepartmentForm(request.POST)
        if form.is_valid():
            department = form.cleaned_data["department"]
            return redirect(f"../department/{department.pk}")
    else:
        form = SelectDepartmentForm()
    return render(request, "department/select_department.html", {"form": form})


class DepartmentListView(ListView):
    model = Department
    template_name = "department/department_list.html"

    def get_queryset(self):
        department = get_object_or_404(Department, pk=self.kwargs["pk"])
        return Exam.objects.filter(
            period=PERIOD, offering__department=department
        ).order_by("offering__course__code", "offering__course__section")


def select_classroom(request):
    if request.method == "POST":
        form = SelectClassroomForm(request.POST)
        if form.is_valid():
            classroom = form.cleaned_data["classroom"]
            return redirect(f"../classroom/{classroom.pk}")
    else:
        form = SelectClassroomForm()
    return render(request, "classroom/select_classroom.html", {"form": form})


class ClassroomListView(ListView):
    model = Classroom
    template_name = "classroom/classroom_list.html"

    def get_queryset(self):
        classroom = get_object_or_404(Course, pk=self.kwargs["pk"])
        return Sitting.objects.filter(
            classroom=classroom.pk, exam__period=PERIOD
        ).order_by("exam__timetable__session__time")


class YoklamaListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        sitting = get_object_or_404(Sitting, pk=self.kwargs["pk"])
        return Enrollment.objects.filter(
            exam=sitting.exam, classroom=sitting.classroom
        )


@user_passes_test(is_administrative)
def select_list(request):
    qs = (
        TimeCode.objects.filter(period=Period.objects.get(active=True))
        .exclude(timetable__isnull=True)
        .annotate(date=Cast("time", DateField()), day=F("long_code") / 10)
        .order_by("time")
    )
    return render(request, "attendance/select.html", {"date_list": qs})
