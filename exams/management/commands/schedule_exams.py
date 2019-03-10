from itertools import combinations
from itertools import product

import pandas as pd
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from pulp import CPLEX
from pulp import LpInteger
from pulp import LpMinimize
from pulp import LpProblem
from pulp import LpVariable
from pulp import lpSum
from pulp import value

from exams.models import AcademicYear
from exams.models import Enrollment
from exams.models import Exam
from exams.models import NoExam
from exams.models import Period
from exams.models import TimeCode
from exams.models import Timetable


class Command(BaseCommand):
    def handle(self, *args, **options):
        academic_year = AcademicYear.objects.get(active=True)
        mt_pr = Period.objects.get(
            academic_year=academic_year, period="midterm"
        )
        fn_pr = Period.objects.get(academic_year=academic_year, period="final")
        no_mt = NoExam.objects.filter(period=mt_pr).values_list(
            "course__id", flat=True
        )
        no_fn = NoExam.objects.filter(period=fn_pr).values_list(
            "course__id", flat=True
        )
        courses_with_no_exam = no_mt.intersection(no_fn)
        queryset = Enrollment.objects.filter(exam__period=mt_pr).exclude(
            exam__offering__course__id__in=courses_with_no_exam
        )
        data = queryset.values(
            "student__tckn", "exam__offering__course__code"
        ).order_by("exam__offering__course__code")

        df = pd.DataFrame.from_records(data).rename(
            columns={
                "student__tckn": "student_id",
                "exam__offering__course__code": "course_code",
            }
        )
        course_sizes = df.groupby("course_code").size()
        max_size = course_sizes.max()
        large_courses = course_sizes[lambda ser: ser > 400].index
        small_courses = course_sizes[lambda ser: ser <= 400].index
        course_list = course_sizes.index
        students = df["student_id"].unique()
        self._solve_regular(
            df,
            course_list,
            students,
            max_size,
            course_sizes,
            large_courses,
            small_courses,
        )
        self._solve_resit(df, course_list, students)

    def _solve_regular(
        self,
        df,
        course_list,
        students,
        max_size,
        course_sizes,
        large_courses,
        small_courses,
    ):
        prob = LpProblem("regular exam assignment", LpMinimize)
        days = range(10)
        sessions = range(4)

        exam = LpVariable.dicts(
            "course assignment", (course_list, days, sessions), 0, 1, LpInteger
        )
        daily_soft_penalty = LpVariable.dicts(
            "daily soft penalty", (students, days), 0, 1, LpInteger
        )
        daily_hard_penalty = LpVariable.dicts(
            "daily hard penalty", (students, days), 0, 1, LpInteger
        )
        conf_two = {}
        for student_id, grouped_df in df.groupby("student_id"):
            courses = grouped_df["course_code"]
            for c1, c2 in combinations(courses, 2):
                exists = conf_two.get((c1, c2))
                if not exists:
                    conf_two[c1, c2] = 1
                    for day, session in product(days, sessions):
                        prob += (
                            exam[c1][day][session] + exam[c2][day][session]
                        ) <= 1
            for day in days:
                prob += (
                    (
                        lpSum(
                            exam[course][day][session]
                            for session in sessions
                            for course in courses
                        )
                    )
                    <= 1
                    + daily_soft_penalty[student_id][day]
                    + daily_hard_penalty[student_id][day]
                )
        for course in course_list:
            prob += (
                lpSum(
                    exam[course][day][session]
                    for day, session in product(days, sessions)
                )
                == 1
            )
        for day, session in product(days, sessions):
            prob += (
                lpSum(
                    exam[course][day][session] * course_sizes[course]
                    for course in course_list
                )
                <= max_size
            )
        for day, session in product(days, sessions):
            for large_course in large_courses:
                prob += lpSum(
                    exam[small_course][day][session]
                    for small_course in small_courses
                ) <= 20 * (1 - exam[large_course][day][session])

            prob += (
                lpSum(
                    exam[course][day][session] * course_sizes[course]
                    for course in small_courses
                )
                <= max_size
            )

        prob += lpSum(
            daily_soft_penalty[student][day]
            + daily_hard_penalty[student][day] * 100
            for student in students
            for day in days
        )
        status = prob.solve(CPLEX(timeLimit=10000))
        if status in [0, -1, -2]:
            raise CommandError("Timetabling problem is infeasible.")
        academic_year = AcademicYear.objects.get(active=True)
        periods = [
            Period.objects.get(academic_year=academic_year, period=period)
            for period in ("midterm", "final")
        ]
        Timetable.objects.filter(
            exam__offering__academic_year=academic_year
        ).delete()
        objs = []
        for course, day, session in product(course_list, days, sessions):
            if abs(value(exam[course][day][session])) > 0.01:
                for period in periods:
                    time_code, created = TimeCode.objects.get_or_create(
                        short_code=4 * day + session,
                        long_code=(day // 5 + 1) * 100
                        + (day % 5 + 1) * 10
                        + session
                        + 1,
                        period=period,
                    )
                    related_exams = Exam.objects.filter(
                        period=period, offering__course__code=course
                    )
                    for r_exam in related_exams:
                        obj = Timetable(exam=r_exam, session=time_code)
                        objs.append(obj)
        Timetable.objects.bulk_create(objs)
        self.stdout.write(
            self.style.SUCCESS("Midterm & final problem have been solved.")
        )

    def _solve_resit(self, df, course_list, students):
        prob = LpProblem("resit exam assignment", LpMinimize)
        days = range(5)
        sessions = range(5)

        exam = LpVariable.dicts(
            "course assignment", (course_list, days, sessions), 0, 1, LpInteger
        )
        daily_soft_penalty = LpVariable.dicts(
            "daily soft penalty", (students, days), 0, 1, LpInteger
        )
        daily_hard_penalty = LpVariable.dicts(
            "daily hard penalty", (students, days), 0, 1, LpInteger
        )
        conf_two = {}
        for student_id, grouped_df in df.groupby("student_id"):
            courses = grouped_df["course_code"]
            for c1, c2 in combinations(courses, 2):
                exists = conf_two.get((c1, c2))
                if not exists:
                    conf_two[c1, c2] = 1
                    for day, session in product(days, sessions):
                        prob += (
                            exam[c1][day][session] + exam[c2][day][session]
                        ) <= 1
            for day in days:
                prob += (
                    (
                        lpSum(
                            exam[course][day][session]
                            for session in sessions
                            for course in courses
                        )
                    )
                    <= 2
                    + daily_soft_penalty[student_id][day]
                    + daily_hard_penalty[student_id][day]
                )
        for course in course_list:
            prob += (
                lpSum(
                    exam[course][day][session]
                    for day, session in product(days, sessions)
                )
                == 1
            )

        prob += lpSum(
            daily_soft_penalty[student][day]
            + daily_hard_penalty[student][day] * 100
            for student in students
            for day in days
        )
        status = prob.solve(CPLEX(timeLimit=3600))
        if status in [0, -1, -2]:
            raise CommandError("Timetabling problem is infeasible.")

        academic_year = AcademicYear.objects.get(active=True)
        period = Period.objects.get(
            academic_year=academic_year, period="resit"
        )
        objs = []
        for course, day, session in product(course_list, days, sessions):
            if abs(value(exam[course][day][session])) > 0.01:
                time_code, created = TimeCode.objects.get_or_create(
                    short_code=5 * day + session,
                    long_code=(day // 5 + 1) * 100
                    + (day % 5 + 1) * 10
                    + session
                    + 1,
                    period=period,
                )
                related_exams = Exam.objects.filter(
                    period=period, offering__course__code=course
                )
                for r_exam in related_exams:
                    obj = Timetable(exam=r_exam, session=time_code)
                    objs.append(obj)
        Timetable.objects.bulk_create(objs)

        self.stdout.write(self.style.SUCCESS("Resit problem has been solved."))
