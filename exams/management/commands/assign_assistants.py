from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db.models import Count
from pulp import CPLEX
from pulp import LpInteger
from pulp import LpMinimize
from pulp import LpProblem
from pulp import LpVariable
from pulp import lpSum
from pulp import value

from exams.models import AcademicYear
from exams.models import Period
from exams.models import Sitting
from exams.models import Timetable
from exams.models import AssistantAssignment
from exams.models import Assistant
from exams.models import AssistedCourse


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--period", required=True)

    def handle(self, *args, **options):
        academic_year = AcademicYear.objects.get(active=True)
        period = Period.objects.get(
            academic_year=academic_year, period=options["period"]
        )
        assistants = Assistant.objects.exclude(user__is_active=False)
        sittings = Sitting.objects.filter(exam__period=period)
        times = Timetable.objects.filter(exam__period=period)
        times = (
            times.values_list("session__long_code", flat=True)
            .order_by()
            .distinct()
        )
        days = [time // 10 for time in times]
        days = sorted(list(set(days)))
        ast_assignment = LpVariable.dicts(
            "X", (assistants, sittings), 0, 1, LpInteger
        )
        assignment_penalty = LpVariable.dicts("AP", sittings, 0, 1, LpInteger)
        assisted_penalty = LpVariable.dicts("ASP", (assistants, sittings), 0)
        day_penalty = LpVariable.dicts("DYP", assistants, 0, 1, LpInteger)
        department_penalty = LpVariable.dicts("DP", sittings, 0)
        max_exams = LpVariable("max_exams")
        min_exams = LpVariable("min_exams")
        prob = LpProblem("assistant assignment", LpMinimize)
        assisted_courses = AssistedCourse.objects.filter(
            offering__academic_year=period.academic_year
        )
        lst = []
        for obj in assisted_courses:
            if (
                obj.offering.exam_set.get(period=period).sitting_set.count()
                > 0
            ):
                item = (
                    obj.assistant,
                    obj.offering.exam_set.get(period=period)
                    .sitting_set.annotate(count=Count("layout"))
                    .order_by("-count")
                    .first(),
                )
                lst.append(item)
        assisted_courses = lst
        z_assisted_penalty = lpSum(
            assisted_penalty[tup[0]][tup[1]] for tup in assisted_courses
        )
        prob += (
            +1000 * max_exams
            - 1000 * min_exams
            + 1000
            * lpSum(
                sitting.layout_set.count() * assignment_penalty[sitting]
                for sitting in sittings
            )
            + 0.001
            * lpSum(department_penalty[sitting] for sitting in sittings)
            + 1000 * lpSum(day_penalty[assistant] for assistant in assistants)
            + 0.1 * z_assisted_penalty
        )
        for assistant in assistants:
            for time in times:
                sittings_at = Sitting.objects.filter(
                    exam__period=period,
                    exam__timetable__session__long_code=time,
                )
                prob += (
                    lpSum(
                        ast_assignment[assistant][sitting]
                        for sitting in sittings_at
                    )
                    <= 1
                )
        for sitting in sittings:
            prob += (
                lpSum(
                    ast_assignment[assistant][sitting]
                    for assistant in assistants
                )
                == 2 - assignment_penalty[sitting]
            )
        for assistant, sitting in assisted_courses:
            prob += (
                ast_assignment[assistant][sitting]
                + assisted_penalty[assistant][sitting]
                == 1
            )

        for assistant in assistants:
            prob += (
                lpSum(
                    ast_assignment[assistant][sitting] for sitting in sittings
                )
                <= max_exams
            )

        for assistant in assistants:
            prob += (
                lpSum(
                    ast_assignment[assistant][sitting] for sitting in sittings
                )
                >= min_exams
            )
        for day in days:
            for assistant in assistants:
                exams_at_day = sittings.filter(
                    exam__timetable__session__long_code__startswith=day
                )
                prob += (
                    lpSum(
                        ast_assignment[assistant][exam]
                        for exam in exams_at_day
                    )
                    <= 3 + day_penalty[assistant]
                )
        for sitting in sittings:
            dep_assistants = assistants.filter(
                department=sitting.exam.offering.department
            )
            prob += (
                lpSum(
                    ast_assignment[assistant][sitting]
                    for assistant in dep_assistants
                )
                == 2 - department_penalty[sitting]
            )
        status = prob.solve(CPLEX())
        if status in [0, -1, -2]:
            raise CommandError("Assistant problem is infeasible.")
        AssistantAssignment.objects.filter(
            sitting__exam__period=period
        ).delete()
        objs = []
        for assistant in assistants:
            for sitting in sittings:
                if abs(value(ast_assignment[assistant][sitting])) > 0.0001:
                    obj = AssistantAssignment(
                        assistant=assistant, sitting=sitting, active=True
                    )
                    objs.append(obj)
        AssistantAssignment.objects.bulk_create(objs)
        self.stdout.write(self.style.SUCCESS("Done."))
