from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator

from .models import Assistant
from .models import Classroom
from .models import Course
from .models import Department
from .models import Instructor
from .models import Period


class SelectPeriodForm(forms.Form):
    period = forms.ModelChoiceField(queryset=Period.objects.all())
    file = forms.FileField()


class SelectStudentForm(forms.Form):
    student_number = forms.IntegerField(
        validators=[
            MinValueValidator(
                1_000_000_000, message="Please enter a valid student number."
            ),
            MaxValueValidator(
                2_600_000_000, message="Please enter a valid student number."
            ),
        ],
        widget=forms.NumberInput(attrs={"class": "form-control input"}),
    )


class SelectInstructorForm(forms.Form):
    instructor = forms.ModelChoiceField(
        queryset=Instructor.objects.exclude().order_by("slug"),
        widget=forms.Select(attrs={"class": "form-control input"}),
        empty_label="Type in the name of the instructor",
    )


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class SelectAssistantForm(forms.Form):
    assistant = UserModelChoiceField(
        queryset=Assistant.objects.filter(user__is_active=True).order_by(
            "user__first_name"
        ),
        widget=forms.Select(attrs={"class": "form-control input"}),
        empty_label="Type in the name of the assistant",
    )


class SelectCourseForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.order_by("code"),
        widget=forms.Select(attrs={"class": "form-control input"}),
        empty_label="Type in the name of the course",
    )


class SelectDepartmentForm(forms.Form):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        widget=forms.Select(attrs={"class": "form-control input"}),
        empty_label="Type in the name of the department",
    )


class SelectClassroomForm(forms.Form):
    classroom = forms.ModelChoiceField(
        queryset=Classroom.objects.order_by("name"),
        widget=forms.Select(attrs={"class": "form-control input"}),
    )


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        max_length=30,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username"}
        ),
    )
    password = forms.CharField(
        label="Password",
        max_length=30,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )
