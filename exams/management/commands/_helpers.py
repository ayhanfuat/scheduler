import pandas as pd
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.utils.text import slugify

from exams.models import Course
from exams.models import Department
from exams.models import Enrollment
from exams.models import Exam
from exams.models import Instructor
from exams.models import Offering
from exams.models import Period
from exams.models import Student

from ._constants import DEPARTMENT_LIST
from ._constants import DEPTID_LONG_DICT
from ._constants import TURKISH_CHAR


def slugify_tr(name):
    return slugify(name.translate(TURKISH_CHAR))


def add_departments_to_db():
    existing = set(Department.objects.values_list("code", flat=True))
    objs = []
    for department in DEPARTMENT_LIST:
        if department[0] not in existing:
            objs.append(
                Department(
                    code=department[0],
                    name_en=department[1],
                    name_tr=department[2],
                )
            )
    if objs:
        Department.objects.bulk_create(objs)


def add_periods_to_db(academic_year):
    for period in ("midterm", "final", "resit"):
        Period.objects.get_or_create(
            academic_year=academic_year, period=period
        )


def add_instructors_to_db(ser):
    instructors = (
        ser.str.split(",", expand=True)
        .stack()
        .drop_duplicates()
        .reset_index(drop=True)
    )
    existing_users = set(User.objects.values_list("username", flat=True))
    existing_inst = set(Instructor.objects.values_list("slug", flat=True))
    to_register_inst = instructors[
        ~instructors.apply(slugify_tr).isin(existing_inst)
    ]
    to_register_user = instructors[
        ~instructors.apply(slugify_tr).isin(existing_users)
    ]
    if not to_register_user.empty:
        user_objects = []
        for record in to_register_user:
            user = User(username=slugify_tr(record))
            password = User.objects.make_random_password()
            user.set_password(password)
            user_objects.append(user)
        User.objects.bulk_create(user_objects)
    if not to_register_inst.empty:
        instructor_objects = []
        for record in to_register_inst:
            user = User.objects.get(username=slugify_tr(record))
            user.groups.add(Group.objects.get(name="instructors"))
            instructor = Instructor(
                user=user,
                name=record,
                display_name=record,
                slug=slugify_tr(record),
            )
            instructor_objects.append(instructor)
        Instructor.objects.bulk_create(instructor_objects)


def add_courses_to_db(df):
    seen = set(Course.objects.values_list("code", flat=True))
    courses = df[["course_code", "course_name"]].drop_duplicates()
    courses = courses.set_index("course_code")["course_name"].to_dict()
    objs = []
    for course_code, course_name in courses.items():
        if course_code not in seen:
            objs.append(Course(code=course_code, name=course_name))
    return Course.objects.bulk_create(objs)


def add_offerings_to_db(df, academic_year):
    Offering.objects.filter(academic_year=academic_year).delete()
    grouper_cols = [
        "course_code",
        "course_dept",
        "course_section",
        "course_instructor",
    ]
    exam_pivot = df.groupby(grouper_cols).size()
    exam_pivot = exam_pivot.reset_index(name="num_students")

    objs = []
    for _, row in exam_pivot.iterrows():
        instructor = row["course_instructor"].split(",")[0]
        course_code = row["course_code"]
        dept = row["course_dept"]
        section = row["course_section"]
        offering = Offering(
            course=Course.objects.get(code=course_code),
            department=Department.objects.get(code=dept),
            section=section,
            academic_year=academic_year,
            instructor_in_charge=Instructor.objects.get(
                slug=slugify_tr(instructor)
            ),
        )
        objs.append(offering)
    Offering.objects.bulk_create(objs)


def add_students_to_db(df):
    std = df[["std_id", "std_name", "std_surname", "std_tc"]].copy()
    std = std.drop_duplicates(subset="std_id")
    std["std_id"] = std["std_id"].astype(str)
    std["std_tc"] = std["std_tc"].fillna(std["std_id"]).astype("int")
    existing_users = set(User.objects.values_list("username", flat=True))
    existing_std = set(
        Student.objects.values_list("user__username", flat=True)
    )
    to_register_std = std[~std["std_id"].isin(existing_std)]
    to_register_user = std[~std["std_id"].isin(existing_users)]
    if not to_register_user.empty:
        user_objects = []
        for _, record in to_register_user.iterrows():
            user = User(username=record["std_id"])
            user.first_name = record["std_name"]
            user.last_name = record["std_surname"]
            user.email = f"{record.std_id}@faculty.business"
            password = record["std_tc"]
            user.set_password(password)
            user_objects.append(user)
        User.objects.bulk_create(user_objects)
    if not to_register_std.empty:
        student_objects = []
        for _, record in to_register_std.iterrows():
            user = User.objects.get(username=record["std_id"])
            user.groups.add(Group.objects.get(name="students"))
            dept_code = DEPTID_LONG_DICT.get(int(record["std_id"][4:7]))
            student = Student(
                user=user,
                department=Department.objects.filter(code=dept_code).first(),
                tckn=record["std_tc"],
            )
            student_objects.append(student)
        Student.objects.bulk_create(student_objects)


def add_exams_to_db(df, academic_year):
    Exam.objects.filter(offering__academic_year=academic_year).delete()
    cols = ["course_code", "course_dept", "course_section"]
    exams = df.groupby(cols).size()
    objs = []
    periods = [
        Period.objects.get(academic_year=academic_year, period=period)
        for period in ["midterm", "final", "resit"]
    ]
    for course, department, section in exams.index:
        offering = Offering.objects.get(
            course=Course.objects.get(code=course),
            department=Department.objects.get(code=department),
            section=section,
            academic_year=academic_year,
        )

        for period in periods:
            exam = Exam(offering=offering, period=period)
            objs.append(exam)
    Exam.objects.bulk_create(objs)


def add_enrollments_to_db(df, academic_year):
    Enrollment.objects.filter(
        exam__offering__academic_year=academic_year
    ).delete()
    student_dict = {
        std_id: Student.objects.get(user__username=std_id)
        for std_id in df["std_id"].unique()
    }
    dept_dict = {
        dept_code: Department.objects.get(code=dept_code)
        for dept_code in df["course_dept"].unique()
    }
    course_dict = {
        course_code: Course.objects.get(code=course_code)
        for course_code in df["course_code"].unique()
    }

    offerings = df.groupby(
        ["course_code", "course_dept", "course_section"]
    ).size()
    offerings = offerings.reset_index(name="number_of_students")
    offering_objects = [
        Offering.objects.get(
            course=course_dict[row["course_code"]],
            department=dept_dict[row["course_dept"]],
            section=row["course_section"],
            academic_year=academic_year,
        )
        for idx, row in offerings.iterrows()
    ]
    offerings["offering_object"] = offering_objects
    periods = [
        Period.objects.get(academic_year=academic_year, period=period)
        for period in ("midterm", "final", "resit")
    ]
    exams = {
        period.period: [
            Exam.objects.get(offering=offering, period=period)
            for offering in offering_objects
        ]
        for period in periods
    }
    offerings = offerings.assign(**exams)
    before = len(df)
    df = df.merge(
        offerings, on=["course_code", "course_dept", "course_section"]
    )
    df["student_object"] = df["std_id"].map(student_dict)
    after = len(df)
    assert before == after, "The size is different after the merge."
    objs = []
    for idx, row in df.iterrows():
        for period in ("midterm", "final", "resit"):
            obj = Enrollment(student=row["student_object"], exam=row[period])
            objs.append(obj)
    Enrollment.objects.bulk_create(objs)


def read_excel_file(file_name):
    import xlrd

    filecontents = xlrd.open_workbook(file_name, encoding_override="iso8859-9")
    df = pd.read_excel(filecontents, engine="xlrd")
    return df
