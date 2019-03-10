import os

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Func
from django.http import HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Spacer
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.flowables import KeepTogether
from reportlab.platypus.tables import Table
from reportlab.platypus.tables import TableStyle

from .models import Assistant
from .models import Period
from .models import Sitting

styles = getSampleStyleSheet()
pdfmetrics.registerFont(
    TTFont(
        "liberation_sans",
        os.path.join(
            settings.BASE_DIR, "static", "fonts", "LiberationSans-Regular.ttf"
        ),
    )
)

PERIOD = Period.objects.get(active=True)

std_tr = Func(
    "student__user__first_name",
    function="tr_TR",
    template='(%(expressions)s) COLLATE "%(function)s"',
)


def is_assistant(user):
    return user.groups.filter(name="assistants").exists()


def is_administrative(user):
    return user.groups.filter(name="administratives").exists()


def is_student(user):
    return user.groups.filter(name="students").exists()


def attendance_elements(sitting):
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="centered", alignment=TA_CENTER, fontName="liberation_sans"
        )
    )
    elements = []
    enr = sitting.layout_set.all()
    data = list(
        enr.values_list(
            "student__user__username",
            "student__user__first_name",
            "student__user__last_name",
            "chair__column",
            "chair__row",
        ).order_by("chair__column", "chair__row")
    )
    data = [
        (
            idx + 1,
            tup[0],
            " ".join(tup[1:3]),
            f"{tup[3] if tup[3] else ''}{tup[4] if tup[4] else ''}",
            "",
        )
        for idx, tup in enumerate(data)
    ]
    data.insert(0, ("", "Numara", "Ad Soyad", "Sıra", "İmza"))

    table = Table(data, colWidths=[20, 70, 230, 30, 60])
    if len(data) < 35:
        font_size = 10
    elif len(data) <= 38:
        font_size = 9
    elif len(data) <= 41:
        font_size = 8
    else:
        font_size = 7
    table.setStyle(
        TableStyle(
            [
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("FONT", (0, 0), (-1, -1), "liberation_sans", font_size),
            ]
        )
    )
    p1 = "Dokuz Eylül Üniversitesi İşletme Fakültesi"
    p2 = (
        sitting.exam.offering.course.code
        + " "
        + sitting.exam.offering.course.name
    )
    p21 = (
        sitting.exam.offering.instructor_in_charge.name
        + " - "
        + sitting.exam.offering.department.name_tr
        + " "
        + f"{sitting.exam.offering.section}. Şube"
    )

    p4 = (
        timezone.localtime(sitting.exam.timetable.session.time).strftime(
            format="%d/%m/%Y %H:%M"
        )
        + " - "
        + sitting.classroom.name
    )
    p5 = "Sınava giren öğrenci sayısı: "

    elements.append(Paragraph(p1, styles["centered"]))
    elements.append(Paragraph(p2, styles["centered"]))

    elements.append(Paragraph(p21, styles["centered"]))
    elements.append(Paragraph(p4, styles["centered"]))
    if len(data) < 42:
        elements.append(Spacer(width=0, height=10))
    elements.append(table)
    height = 10 if len(data) > 40 else 25
    s = Spacer(width=0, height=height)
    elements.append(s)
    elements.append(Paragraph(p5, styles["centered"]))
    assignments = sitting.assistantassignment_set.all()
    assistants = [
        f"{assignment.assistant.user.first_name}"
        f" {assignment.assistant.user.last_name}"
        for assignment in assignments
    ]
    if len(assistants) < 2:
        for i in range(2 - len(assistants)):
            assistants.append("")
    assistants = [tuple(assistants)]

    table2 = Table(assistants, colWidths=210)
    table2.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "liberation_sans", 10),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )

    elements.append(table2)
    return elements


def door_list_elements(sitting):
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="centered",
            alignment=TA_CENTER,
            fontName="liberation_sans",
            fontSize=14,
        )
    )
    elements = []
    enr = sitting.layout_set.all()
    data = list(
        enr.values_list(
            "student__user__username",
            "student__user__first_name",
            "student__user__last_name",
            "chair__column",
            "chair__row",
        ).order_by("student__user__first_name", "student__user__last_name")
    )
    break_point = len(data) // 2 + len(data) % 2
    data_left = [("Numara", "Ad Soyad", "Sıra")]
    for tup in data[:break_point]:
        data_left.append((tup[0], " ".join(tup[1:3]), f"{tup[3]}{tup[4]}"))
    data_right = [("Numara", "Ad Soyad", "Sıra")]
    for tup in data[break_point:]:
        data_right.append((tup[0], " ".join(tup[1:3]), f"{tup[3]}{tup[4]}"))

    col_widths = [70, 230, 30]
    table_left = Table(data_left, colWidths=col_widths)
    table_left.setStyle(
        TableStyle(
            [
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("FONT", (0, 0), (-1, -1), "liberation_sans", 10),
            ]
        )
    )

    table_right = Table(data_right, colWidths=col_widths)
    table_right.setStyle(
        TableStyle(
            [
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("FONT", (0, 0), (-1, -1), "liberation_sans", 10),
            ]
        )
    )

    table = Table(
        [[table_left, table_right]], colWidths=[sum(col_widths) + 15] * 2
    )
    table.setStyle(TableStyle([("VALIGN", (-1, -1), (-1, -1), "TOP")]))
    p2 = (
        sitting.exam.offering.course.code
        + " "
        + sitting.exam.offering.course.name
    )
    p3 = sitting.exam.offering.instructor_in_charge.name
    s = Spacer(width=0, height=5)
    header_data = [
        [
            timezone.localtime(sitting.exam.timetable.session.time).strftime(
                format="%d/%m/%Y %H:%M"
            ),
            sitting.classroom.name,
        ]
    ]
    header_table = Table(header_data, colWidths=[sum(col_widths) + 5] * 2)
    header_table.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "liberation_sans", 14),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )
    elements.append(Paragraph(p2, styles["centered"]))
    elements.append(s)
    elements.append(Paragraph(p3, styles["centered"]))

    elements.append(header_table)
    elements.append(s)
    elements.append(table)

    return elements


@user_passes_test(is_administrative)
def generate_attendance_sheet(request, pk):
    sitting = Sitting.objects.get(id=pk)
    filename = slugify(
        "-".join(
            [
                sitting.exam.offering.course.code,
                sitting.exam.offering.course.name,
                str(sitting.exam.offering.section),
                sitting.classroom.name,
            ]
        )
    )
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={filename}.pdf"
    doc = SimpleDocTemplate(
        response,
        rightMargin=25,
        leftMargin=25,
        topMargin=15,
        bottomMargin=5,
        pagesize=A4,
    )
    doc.title = (
        f"{sitting.exam.offering.course.code}"
        f" {sitting.exam.offering.course.name}"
        f" {sitting.exam.offering.section} - {sitting.classroom.name}"
    )
    elements = attendance_elements(sitting)
    doc.build(elements)
    return response


@user_passes_test(is_administrative)
def generate_attendance_sheets(request, **kwargs):
    day = kwargs.get("day")
    session = kwargs.get("session")
    if day:
        sittings = Sitting.objects.filter(
            exam__period=PERIOD,
            exam__timetable__session__long_code__range=(
                day * 10,
                (day + 1) * 10,
            ),
        ).order_by("exam__timetable__session__time", "classroom")
        filename = sittings.first().exam.timetable.session.time.strftime(
            format="%d-%m-%Y"
        )
    elif session:
        sittings = Sitting.objects.filter(
            exam__period=PERIOD, exam__timetable__session__long_code=session
        ).order_by("classroom")
        filename = timezone.localtime(
            sittings.first().exam.timetable.session.time
        ).strftime(format="%d-%m-%Y %H %M")
    response = HttpResponse(content_type="application/pdf")
    response[
        "Content-Disposition"
    ] = f"attachment; filename={filename} - yoklama.pdf"
    doc = SimpleDocTemplate(
        response,
        rightMargin=25,
        leftMargin=25,
        topMargin=5,
        bottomMargin=5,
        pagesize=A4,
    )
    doc.title = filename
    elements = []
    for sitting in sittings:
        elements.extend(attendance_elements(sitting))
        elements.append(PageBreak())
    doc.build(elements)
    return response


@user_passes_test(is_administrative)
def generate_door_lists(request, **kwargs):
    day = kwargs.get("day")
    session = kwargs.get("session")
    if day:
        sittings = Sitting.objects.filter(
            exam__period=PERIOD,
            exam__timetable__session__long_code__range=(
                day * 10,
                (day + 1) * 10,
            ),
        ).order_by("exam__timetable__session__time", "classroom")
        filename = sittings.first().exam.timetable.session.time.strftime(
            format="%d-%m-%Y"
        )
    elif session:
        sittings = Sitting.objects.filter(
            exam__period=PERIOD, exam__timetable__session__long_code=session
        ).order_by("classroom")
        filename = timezone.localtime(
            sittings.first().exam.timetable.session.time
        ).strftime(format="%d-%m-%Y %H %M")
    response = HttpResponse(content_type="application/pdf")
    response[
        "Content-Disposition"
    ] = f"attachment; filename={filename} - oturum.pdf"
    doc = SimpleDocTemplate(
        response,
        rightMargin=25,
        leftMargin=25,
        topMargin=5,
        bottomMargin=5,
        pagesize=landscape(A4),
    )
    doc.title = filename
    elements = []
    for sitting in sittings:
        elements.extend(door_list_elements(sitting))
        elements.append(PageBreak())
    doc.build(elements)
    return response


@user_passes_test(is_administrative)
def dolubos(request):
    import pandas as pd

    qs = Sitting.objects.filter(
        exam__period=Period.objects.get(active=True)
    ).values(
        "classroom__name", "exam__timetable__session__time", "classroom__block"
    )
    df = pd.DataFrame.from_records(qs)
    df = df.rename(
        columns={
            "classroom__name": "classroom",
            "exam__timetable__session__time": "time",
            "classroom__block": "block",
        }
    )
    df["time"] = df["time"].dt.tz_convert("Europe/Istanbul")
    df = df.sort_values("classroom")
    df = df.drop_duplicates()
    idx = pd.MultiIndex.from_product(
        [df["time"].unique(), df["block"].unique()], names=["time", "block"]
    )
    ser = (
        df.groupby(["time", "block"])["classroom"]
        .apply(", ".join)
        .reindex(idx, fill_value="")
        .groupby(level=0)
        .apply("<br/>".join)
    )
    last_df = (
        pd.pivot(
            index=ser.index.date, columns=ser.index.time, values=ser.values
        )
        .fillna("")
        .rename_axis("Tarih")
    )
    last_df.columns = [str(col) for col in last_df]
    last_df = last_df.reset_index()
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="centered",
            alignment=TA_CENTER,
            fontName="liberation_sans",
            fontSize=8,
        )
    )
    last_df["Tarih"] = last_df["Tarih"].dt.strftime("%d-%m-%Y")
    last_df = last_df.applymap(lambda x: Paragraph(x, styles["centered"]))
    data = last_df.values.tolist()
    data.insert(0, last_df.columns.tolist())
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"filename=dolubos.pdf"
    doc = SimpleDocTemplate(
        response,
        rightMargin=10,
        leftMargin=10,
        topMargin=10,
        bottomMargin=10,
        pagesize=landscape(A4),
    )
    doc.title = "Dolubos"
    elements = []
    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    return response


def generate_assistant_report(request, slug):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={slug}.pdf"
    doc = SimpleDocTemplate(
        response, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="centered1",
            alignment=TA_CENTER,
            fontName="liberation_sans",
            fontSize=16,
            leading=30,
        )
    )
    styles.add(
        ParagraphStyle(
            name="right",
            alignment=TA_RIGHT,
            fontName="liberation_sans",
            fontSize=12,
            leading=15,
        )
    )
    styles.add(
        ParagraphStyle(
            name="regular",
            alignment=TA_JUSTIFY,
            fontName="liberation_sans",
            fontSize=10,
            spaceBefore=3,
            spaceAfter=3,
            leading=15,
            firstLineIndent=30,
        )
    )

    styles.add(
        ParagraphStyle(
            name="regular3",
            alignment=TA_JUSTIFY,
            fontName="liberation_sans",
            fontSize=10,
            spaceBefore=3,
            spaceAfter=3,
            leading=15,
            firstLineIndent=64,
        )
    )

    styles.add(
        ParagraphStyle(
            name="regular2",
            alignment=TA_JUSTIFY,
            fontName="liberation_sans",
            fontSize=12,
            leading=15,
        )
    )

    assistant = Assistant.objects.get(slug=slug)
    assignments = assistant.assistantassignment_set.filter(
        sitting__exam__period=PERIOD
    ).order_by("sitting__exam__timetable__session__time")
    prev_date = None
    all_elems = []
    elements = []
    all_elems.append(
        Paragraph(
            f"{assistant.user.first_name} {assistant.user.last_name}",
            styles["centered1"],
        )
    )
    for assignment in assignments:
        course_title = " ".join(
            (
                assignment.sitting.exam.offering.course.code,
                assignment.sitting.exam.offering.course.name,
            )
        )
        instructor = assignment.sitting.exam.offering.instructor_in_charge.name
        department = assignment.sitting.exam.offering.department.code
        section = assignment.sitting.exam.offering.section
        classroom = assignment.sitting.classroom.name
        assistants = [
            f"{assistant.user.first_name} {assistant.user.last_name}"
            for assistant in assignment.sitting.assistants.all()
        ]
        assistants = ", ".join(assistants)
        time = timezone.localtime(
            assignment.sitting.exam.timetable.session.time
        )
        num_students = f"{assignment.sitting.layout_set.count()} öğrenci"
        cur_date = time.date()
        if cur_date != prev_date:
            if prev_date is not None:
                elements.pop()
                all_elems.append(KeepTogether(elements))
                elements = []
            elements.append(HRFlowable(width="100%"))

            elements.append(
                Paragraph(
                    cur_date.strftime("%d-%b-%y, %a"), styles["regular2"]
                )
            )
            elements.append(HRFlowable(width="100%"))
            elements.append(
                Paragraph(
                    " - ".join(
                        (
                            (
                                time.time().strftime("%H:%M"),
                                course_title,
                                instructor,
                            )
                        )
                    ),
                    styles["regular"],
                )
            )
            elements.append(
                Paragraph(
                    " - ".join(
                        (
                            classroom,
                            assistants,
                            department,
                            f"{section}. Şube",
                            num_students,
                        )
                    ),
                    styles["regular3"],
                )
            )
            elements.append(HRFlowable(width="90%", thickness=0.5))
            prev_date = cur_date
        else:
            elements.append(
                Paragraph(
                    " - ".join(
                        (
                            (
                                time.time().strftime("%H:%M"),
                                course_title,
                                instructor,
                            )
                        )
                    ),
                    styles["regular"],
                )
            )
            elements.append(
                Paragraph(
                    " - ".join(
                        (
                            classroom,
                            assistants,
                            department,
                            f"{section}. Şube",
                            num_students,
                        )
                    ),
                    styles["regular3"],
                )
            )
            elements.append(HRFlowable(width="90%", thickness=0.5))
    elements.pop()
    all_elems.append(KeepTogether(elements))
    all_elems.append(HRFlowable(width="100%"))
    doc.build(all_elems)
    return response
