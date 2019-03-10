# Examination Scheduler
## Dokuz Eylul University Faculty of Business

### Setup

The scheduler interacts with the database through django's ORM. The corresponding tables are in the `exams` app's `models.py` file.

Before each semester, a new `AcademicYear` object should be generated. For each `AcademicYear` there are three periods available: `midterm`, `final`, and `resit`. One of these should be set to active as well. The website displays data from active `AcademicYear` and `Period`.

Associated with each `AcademicYear` are the `Offering` objects which are defined by the course, the department offering the course, and the section. The `Exam` objects related to the `Offering`s are defined for each period. Each `Exam` has a one-to-one relationship with a `Timetable` object which stores the exam time through the `TimeCode` object.

The scheduler uses `TimeCode` objects to assign exams to time slots. The associated properties of these objects are

- `short_code`: A sequence from 0 to N-1 where N is the total number of time slots.
- `long_code`: A  three digit integer of the form WDS where W is the week (1 or 2), D is the day of that week (1, 2, 3, 4, 5) and S is the session in each day (1, 2, 3, 4 for midterms/finals, 1, 2, 3, 4, 5 for resit exams)
- `time`: Time of the exam. This field is *not* automatically populated but should be generated manually based on the exam dates. A helper function is available in `/exams/management/commands/_dategen.py`.

For courses that don't have midterm/final or resit exams, a `NoExam` object should be created for the corresponding period. This is important for the scheduler to be able to produce a good (or even in some cases a *feasible*) timetable.

### Loading Data

The data is loaded from an Excel file whose required columns are specified in the `REQUIRED_COLS` dictionary under the `_constants.py` file. The syntax for loading data is

    $ python manage.py load_data --filepath "/path/to/excel_file"

This script populates the database tables (`Student`, `Department`, `Instructor`, `Exam` etc.) by using the mappings in the `_constants.py` file. If the script raises an error this means either the file doesn't have one of the required columns or is not compatible with the mappings (a change in a department's name, for example). The version of the Excel file produced by the University's information system is very old. This file shouldn't be edited by Office programs as they mess up the encoding of the file.

Important: This script populates the database tables for the active `AcademicYear` and its `Period`s. If it runs multiple times, it first deletes all the data associated with the current `AcademicYear` (`Offering`s, `Exam`s, and so on). So it shouldn't be run after the schedule is generated and it should be run with an up to date Excel file.

### Scheduling Exams

After loading the data for the current semester, the exams can be scheduled with the following command:

    $ python manage.py schedule_exams

This script deletes previously written timetables for the entire semester. It should be run only once in each semester. It generates a timetable for midterm, final and resit exams.

The scheduler needs a few hours to produce a good timetable.

### Assigning Classrooms

After the timetable is produced, the classrooms for the midterm and final exams can be assigned with the following command:

    $ python manage.py assign_classrooms --period "midterm"
    $ python manage.py assign_classrooms --period "final"

It cannot produce feasible assignment for the resit exams assuming all students will take those exams. In order to run it for the resit exams, first the resit `Enrollment` records for the students who successfully passed their courses should be deleted.

### Assigning Assistants

The assistants are assigned to classrooms directly so this step should be done after assigning the classrooms.

    $ python manage.py assign_assistants --period "midterm"
    $ python manage.py assign_assistants --period "final"

Assistant list is obtained by filtering the active `User`s of the `Assistant`s. If an assistant is not available for a period, their user should be deactivated. Similarly, in order to add a new assistant, a new user should be added first and should be added to the `assistants` group. Then, an assistant can be created for this user.

### SECRET_KEY and DB_PASSWORD
The project reads the secret key and the database password from environment variables:

    $ export SECRET_KEY="SECRET KEY"
    $ export DB_PASSWORD="DB PASSWORD"
