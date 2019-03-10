from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from exams.models import AcademicYear

from ._constants import COL_DICT
from ._constants import DEPT_DICT
from ._constants import REQUIRED_COLS
from ._helpers import add_courses_to_db
from ._helpers import add_departments_to_db
from ._helpers import add_offerings_to_db
from ._helpers import add_instructors_to_db
from ._helpers import add_students_to_db
from ._helpers import add_exams_to_db
from ._helpers import add_enrollments_to_db
from ._helpers import read_excel_file
from ._helpers import add_periods_to_db


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--filepath", required=True)

    def handle(self, *args, **options):
        academic_year = AcademicYear.objects.get(active=True)
        add_departments_to_db()
        df = read_excel_file(options["filepath"])
        df = df.rename(columns=COL_DICT)
        for col in REQUIRED_COLS:
            if col not in df:
                raise CommandError(
                    f"One of the columns in the Excel file is missing or has a"
                    f" spelling error: {col}."
                )
        df["course_dept"] = df["course_dept"].str.strip().map(DEPT_DICT)
        df["course_section"] = (
            df["course_section"]
            .astype(str)
            .str.replace(".Şube", "")
            .astype("int")
        )
        df = df[REQUIRED_COLS].copy()
        shape_before = df.shape
        df = df.dropna()
        shape_after = df.shape
        if shape_before != shape_after:
            self.stdout.write(
                self.style.WARNING(
                    f"{shape_before[0] - shape_after[0]} row(s) dropped."
                    f" Large number of dropped rows is generally caused by a"
                    f" problem in the Excel file."
                )
            )
        add_departments_to_db()
        add_periods_to_db(academic_year)
        add_instructors_to_db(df["course_instructor"])
        add_courses_to_db(df)
        add_offerings_to_db(df, academic_year)
        add_students_to_db(df)
        add_exams_to_db(df, academic_year)
        add_enrollments_to_db(df, academic_year)
        self.stdout.write(self.style.SUCCESS(f"Data loaded."))
