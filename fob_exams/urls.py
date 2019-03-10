from django.contrib import admin
from django.contrib import auth
from django.urls import include
from django.urls import path
from django.urls import re_path
from django.views.generic import RedirectView

import exams
from exams.views import logout_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("exams/", include("exams.urls")),
    path(
        "accounts/login/",
        auth.views.LoginView.as_view(
            authentication_form=exams.forms.LoginForm
        ),
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path("logout/", logout_view, name="logout"),
    re_path(r"^$", RedirectView.as_view(url="/exams/student/"), name="home"),
]
