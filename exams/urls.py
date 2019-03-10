from django.urls import path

from . import views, report_views


urlpatterns = [
    path("", views.exam_home, name="exam-home"),
    path("student/", views.select_student, name="student"),
    path(
        "student/<int:student_number>/",
        views.LayoutListView.as_view(),
        name="layout-list",
    ),
    path(
        "student/<int:student_number>/<period>/",
        views.EnrollmentListView.as_view(),
        name="enrollment-list",
    ),
    path("instructor/", views.select_instructor, name="instructor"),
    path(
        "instructor/<slug:slug>/",
        views.ExamListView.as_view(),
        name="instructor-list",
    ),
    path("assistant/", views.select_assistant, name="assistant"),
    path(
        "assistant/<slug:slug>/",
        views.AssistantAssignmentListView.as_view(),
        name="assistant-list",
    ),
    path(
        "assistant-print/<slug:slug>/",
        report_views.generate_assistant_report,
        name="assistant-print",
    ),
    path("course/", views.select_course, name="course"),
    path(
        "course/<int:pk>", views.CourseListView.as_view(), name="course-list"
    ),
    path("department/", views.select_department, name="department"),
    path(
        "department/<int:pk>",
        views.DepartmentListView.as_view(),
        name="department-list",
    ),
    path("lists/", views.select_list, name="lists"),
    path(
        "attendance/day/<int:day>/",
        report_views.generate_attendance_sheets,
        name="attendance-day",
    ),
    path(
        "attendance/session/<int:session>/",
        report_views.generate_attendance_sheets,
        name="attendance-session",
    ),
    path(
        "seating_plan/day/<int:day>/",
        report_views.generate_door_lists,
        name="seating-day",
    ),
    path(
        "seating_plan/session/<int:session>/",
        report_views.generate_door_lists,
        name="seating-session",
    ),
    path("classroom/", views.select_classroom, name="classroom"),
    path(
        "classroom/<int:pk>",
        views.ClassroomListView.as_view(),
        name="classroom-list",
    ),
    path("dolubos/", report_views.dolubos, name="dolubos"),
]
