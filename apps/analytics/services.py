from django.db.models import Avg

from apps.assignments.models import Assignment, AssignmentSubmission
from apps.attendance.models import Attendance, AttendanceStatus
from apps.grades.models import Grade
from apps.quizzes.models import QuizAttempt


def compute_student_progress(student, academic_year=None):
    grades_qs = Grade.objects.filter(student=student)
    if academic_year is not None:
        grades_qs = grades_qs.filter(academic_year=academic_year)
    average_grade = grades_qs.aggregate(avg=Avg("value"))["avg"] or 0

    attendance_qs = Attendance.objects.filter(student=student)
    total_attendance = attendance_qs.count()
    present_count = attendance_qs.filter(
        status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE]
    ).count()
    attendance_percentage = (present_count / total_attendance * 100) if total_attendance else 0

    class_room = student.class_room
    if class_room is not None:
        total_assignments = Assignment.objects.filter(lesson__class_room=class_room).count()
    else:
        total_assignments = 0
    submitted_count = AssignmentSubmission.objects.filter(student=student).count()
    homework_completion = (submitted_count / total_assignments * 100) if total_assignments else 0

    quiz_attempts = QuizAttempt.objects.filter(student=student)
    quiz_average = 0
    if quiz_attempts.exists():
        percentages = [
            (a.score / a.max_score * 100) if a.max_score else 0 for a in quiz_attempts
        ]
        quiz_average = sum(percentages) / len(percentages)

    return {
        "average_grade": round(average_grade, 2),
        "attendance_percentage": round(attendance_percentage, 2),
        "homework_completion": round(homework_completion, 2),
        "quiz_average": round(quiz_average, 2),
    }


def compute_admin_analytics(school=None):
    from apps.attendance.models import TeacherAttendance
    from apps.classes.models import ClassRoom
    from apps.users.models import StudentProfile, TeacherProfile, User

    students = StudentProfile.objects.all()
    teachers = TeacherProfile.objects.all()
    classes = ClassRoom.objects.all()
    if school is not None:
        students = students.filter(school=school)
        teachers = teachers.filter(school=school)
        classes = classes.filter(school=school)

    attendance_qs = Attendance.objects.filter(student__in=students)
    total_attendance = attendance_qs.count()
    present_count = attendance_qs.filter(
        status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE]
    ).count()
    attendance_percentage = (present_count / total_attendance * 100) if total_attendance else 0

    average_grades = Grade.objects.filter(student__in=students).aggregate(avg=Avg("value"))["avg"] or 0

    total_assignments = Assignment.objects.filter(lesson__class_room__in=classes).count()
    total_submissions = AssignmentSubmission.objects.filter(student__in=students).count()
    homework_completion = (total_submissions / total_assignments * 100) if total_assignments else 0

    quiz_average = QuizAttempt.objects.filter(student__in=students).aggregate(
        avg=Avg("score")
    )["avg"] or 0

    active_users = User.objects.filter(is_active=True).count()
    absent_today = attendance_qs.filter(status=AttendanceStatus.ABSENT).count()

    teacher_attendance_qs = TeacherAttendance.objects.filter(teacher__in=teachers)
    teacher_attendance_percentage = 0
    if teacher_attendance_qs.exists():
        present_teachers = teacher_attendance_qs.filter(
            status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE]
        ).count()
        teacher_attendance_percentage = present_teachers / teacher_attendance_qs.count() * 100

    return {
        "total_students": students.count(),
        "total_teachers": teachers.count(),
        "total_classes": classes.count(),
        "attendance_percentage": round(attendance_percentage, 2),
        "average_grades": round(average_grades, 2),
        "homework_completion": round(homework_completion, 2),
        "quiz_average": round(quiz_average, 2),
        "active_users": active_users,
        "absent_students": absent_today,
        "teacher_attendance_percentage": round(teacher_attendance_percentage, 2),
    }
