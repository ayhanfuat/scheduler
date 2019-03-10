import random

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db.models import Sum
from pulp import CPLEX
from pulp import LpInteger
from pulp import LpMinimize
from pulp import LpProblem
from pulp import LpVariable
from pulp import lpSum
from pulp import value

from exams.models import AcademicYear
from exams.models import Classroom
from exams.models import Exam
from exams.models import Layout
from exams.models import Period
from exams.models import Sitting
from exams.models import TimeCode
from exams.models import Timetable


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--period", required=True)

    def handle(self, *args, **options):
        academic_year = AcademicYear.objects.get(active=True)
        period = Period.objects.get(
            academic_year=academic_year, period=options["period"]
        )
        times = TimeCode.objects.filter(period=period)
        probs = {}
        for time in times:
            probs[time] = LpProblem(f"Problem {time}", LpMinimize)
        all_exams = Timetable.objects.filter(exam__period=period)
        classrooms = Classroom.objects.all()
        class_vars = LpVariable.dicts(
            name="classroom_assignment",
            indexs=(classrooms, all_exams),
            lowBound=0,
            upBound=1,
            cat=LpInteger,
        )
        for time in times:
            prob = probs[time]
            exams = all_exams.filter(exam__timetable__session=time)
            for classroom in classrooms:
                prob += (
                    lpSum(class_vars[classroom][exam] for exam in exams) <= 1
                )
            classrooms_used = lpSum(
                class_vars[classroom][exam]
                for classroom in classrooms
                for exam in exams
            )
            for exam in exams:
                prob += (
                    lpSum(
                        class_vars[classroom][exam] * classroom.capacity
                        for classroom in classrooms
                    )
                    >= exam.exam.enrollment_set.count()
                )
            prob += classrooms_used
            status = prob.solve(CPLEX())
            if status in [0, -1, -2]:
                raise CommandError("Classroom problem is infeasible.")
        Sitting.objects.filter(exam__period=period).delete()
        objs = []
        for ex in all_exams:
            for classroom in classrooms:
                result = value(class_vars[classroom][ex])
                if result is not None:
                    if abs(result - 1) < 0.01:
                        obj = Sitting(exam=ex.exam, classroom=classroom)
                        objs.append(obj)

        Sitting.objects.bulk_create(objs)
        self.stdout.write(
            self.style.SUCCESS(
                "Classrooms have been assigned to exams."
                " Students are being assigned to classrooms."
            )
        )
        self._assign_students_to_classrooms(period)
        self.stdout.write(
            self.style.SUCCESS(
                "Students have been assigned to classrooms."
                " They are being assigned to their seats."
            )
        )
        self._assign_seats(period)
        self.stdout.write(self.style.SUCCESS("Done."))

    def _assign_students_to_classrooms(self, period):
        exams = Exam.objects.filter(timetable__isnull=False, period=period)
        objs = []
        for exam in exams:
            students = exam.enrollment_set.order_by("student__user__password")
            sittings = exam.sitting_set.order_by("classroom__capacity")
            total_capacity = sittings.aggregate(Sum("classroom__capacity"))[
                "classroom__capacity__sum"
            ]
            total_number_of_students = students.count()
            total_slack = total_capacity - total_number_of_students
            num_classrooms = sittings.count()
            if total_slack < 0:
                raise CommandError("Classroom capacity is not enough.")
            else:
                per_slack = total_slack // num_classrooms
                remaining = total_slack - per_slack * num_classrooms
                start = 0
                for idx, sitting in enumerate(sittings):
                    num = sitting.classroom.capacity - per_slack
                    if idx < remaining:
                        num = num - 1
                    enrollments = students[start:start + num].values_list(
                        "pk", flat=True
                    )
                    students_to_assign = students.filter(pk__in=enrollments)
                    for enr in students_to_assign:
                        obj = Layout(student=enr.student, sitting=sitting)
                        objs.append(obj)
                    start = start + num
        Layout.objects.bulk_create(objs)

    def _assign_seats(self, period):
        random.seed(27)
        sittings = Sitting.objects.filter(exam__period=period)
        for sitting in sittings:
            classroom = sitting.classroom
            count = sitting.layout_set.count()
            chairs = classroom.chair_set.filter(assign_order__lt=count + 1)
            chairs = list(chairs)
            random.shuffle(chairs)
            pairs = zip(sitting.layout_set.all(), chairs)
            for layout, chair in pairs:
                layout.chair = chair
                layout.save()
