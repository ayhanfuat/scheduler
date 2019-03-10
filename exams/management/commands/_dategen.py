import pandas as pd
from exams.models import TimeCode
from exams.models import AcademicYear
from exams.models import Period


def dates(start_date, end=254):
    num_weeks = end // 100
    num_days = (num_weeks - 1) * 5 + (end - 100 * num_weeks) // 10
    print(num_days)
    lst = []
    start_date = pd.to_datetime(start_date)
    for day in range(num_days):
        week = day//5
        for session in range(4):
            exam_date = start_date + \
                pd.to_timedelta('{} days {} hour'.format(
                    day+2*week, session*2))
            time_code = (week+1)*100 + (day-5*week+1)*10 + session + 1
            lst.append((time_code, exam_date))
    df = pd.DataFrame(lst, columns=['time_code', 'exam_date'])
    df['exam_date'] = df['exam_date'].dt.tz_localize('Europe/Istanbul')
    return df


df = dates('20190310 09:00')
academic_year = AcademicYear.objects.get(active=True)
period = Period.objects.get(academic_year=academic_year, period='midterm')

for short_code, row in df.iterrows():
    long_code = row['time_code']
    time = row['exam_date']
    obj, created = TimeCode.objects.get_or_create(
        short_code=short_code,
        long_code=long_code,
        period=period
    )
    obj.time = time
    obj.save()
