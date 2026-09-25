import datetime
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.assignments.models import Assignment, AssignmentSubmission
from apps.attendance.models import Attendance, AttendanceStatus, TeacherAttendance
from apps.classes.models import AcademicYear, ClassRoom, Quarter
from apps.grades.models import Grade
from apps.helpdesk.models import HelpDeskTicket
from apps.lessons.models import Lesson
from apps.library.models import LibraryMaterial
from apps.notifications.models import Announcement
from apps.quizzes.models import Question, Quiz, QuizAttempt
from apps.schools.models import School
from apps.subjects.models import Subject
from apps.users.models import ParentProfile, ParentStudent, StudentProfile, TeacherProfile, User

DEMO_PASSWORD = "Demo12345!"

SUBJECT_NAMES = [
    ("Matematika", "📐"),
    ("Fizika", "⚛️"),
    ("Informatika", "💻"),
    ("Ingliz tili", "🇬🇧"),
    ("Ona tili", "📖"),
    ("Tarix", "🏛️"),
    ("Biologiya", "🧬"),
]

STUDENT_NAMES = [
    ("Aziz", "Karimov"),
    ("Azizbek", "Abduraximov"),
    ("Aziza", "Yusupova"),
    ("Malika", "Nazarova"),
    ("Bekzod", "Tursunov"),
    ("Sardor", "Ergashev"),
    ("Nodira", "Xolmatova"),
    ("Javlon", "Rashidov"),
    ("Dilnoza", "Saidova"),
]


class Command(BaseCommand):
    help = "MaktabIQ uchun demo namuna ma'lumotlar (barcha rollar) yaratadi. Qayta ishga tushirish xavfsiz."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("MaktabIQ demo ma'lumotlar yaratilmoqda..."))

        school = self.seed_school()
        academic_year, quarters = self.seed_academic_year()
        subjects = self.seed_subjects()
        superadmin = self.seed_user("superadmin", "Sardor", "Rahimov", User.Role.SUPERADMIN, school, is_superuser=True)
        admin = self.seed_user("admin", "Gulnora", "Yoqubova", User.Role.ADMIN, school, is_staff=True)
        self.seed_user("director", "Akmal", "Nurmatov", User.Role.DIRECTOR, school)
        self.seed_user("deputy", "Malika", "Tursunova", User.Role.DEPUTY_DIRECTOR, school)

        classes = self.seed_classes(school, academic_year)
        teachers = self.seed_teachers(school, subjects)
        self.assign_curators(classes, teachers)

        students = self.seed_students(school, classes)
        parents = self.seed_parents(students)

        lessons = self.seed_lessons(classes, subjects, teachers)
        self.seed_grades(students, subjects, teachers, academic_year, quarters)
        self.seed_attendance(students, teachers)
        assignments = self.seed_assignments(lessons, teachers, students)
        self.seed_quiz(classes, subjects, teachers, students)
        self.seed_library(subjects, admin)
        self.seed_announcements(admin, classes)
        self.seed_helpdesk(students)

        self.print_summary(superadmin, admin, teachers, students, parents)

    # ------------------------------------------------------------------ #

    def seed_school(self):
        school, _ = School.objects.get_or_create(
            name="MaktabIQ Namuna Maktabi",
            defaults={"address": "Toshkent sh., Chilonzor tumani", "phone": "+998901234567", "email": "info@maktabiq.uz"},
        )
        return school

    def seed_academic_year(self):
        year, _ = AcademicYear.objects.get_or_create(
            name="2026-2027",
            defaults={"start_date": "2026-09-01", "end_date": "2027-05-31", "is_active": True},
        )
        quarter_dates = [
            (1, "2026-09-01", "2026-10-30"),
            (2, "2026-11-09", "2026-12-28"),
            (3, "2027-01-11", "2027-03-19"),
            (4, "2027-03-29", "2027-05-25"),
        ]
        quarters = {}
        for number, start, end in quarter_dates:
            q, _ = Quarter.objects.get_or_create(academic_year=year, number=number, defaults={"start_date": start, "end_date": end})
            quarters[number] = q
        return year, quarters

    def seed_subjects(self):
        subjects = {}
        for name, icon in SUBJECT_NAMES:
            subj, _ = Subject.objects.get_or_create(name=name, defaults={"icon": icon})
            subjects[name] = subj
        return subjects

    def seed_user(self, username, first_name, last_name, role, school, **extra):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{username}@maktabiq.uz",
                "role": role,
                "school": school,
                **extra,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user

    def seed_classes(self, school, academic_year):
        classes = {}
        for name, grade in [("9-A", 9), ("9-B", 9), ("10-A", 10)]:
            c, _ = ClassRoom.objects.get_or_create(
                school=school, name=name, academic_year=academic_year, defaults={"grade": grade}
            )
            classes[name] = c
        return classes

    def seed_teachers(self, school, subjects):
        teacher_data = [
            ("teacher_math", "Olim", "Sattorov", ["Matematika", "Fizika"], 12),
            ("teacher_eng", "Feruza", "Ismoilova", ["Ingliz tili"], 8),
            ("teacher_it", "Jasur", "Nematov", ["Informatika"], 6),
            ("teacher_hist", "Zulfiya", "Qodirova", ["Tarix", "Ona tili"], 15),
        ]
        teachers = {}
        for i, (username, first, last, subj_names, exp) in enumerate(teacher_data, start=1):
            user = self.seed_user(username, first, last, User.Role.TEACHER, school, phone=f"+99890000000{i}")
            profile, _ = TeacherProfile.objects.get_or_create(
                user=user, defaults={"school": school, "teacher_id": f"T-{i:04d}", "experience_years": exp}
            )
            profile.subjects.set([subjects[n] for n in subj_names])
            teachers[username] = profile
        return teachers

    def assign_curators(self, classes, teachers):
        pairs = [("9-A", "teacher_math"), ("9-B", "teacher_eng"), ("10-A", "teacher_hist")]
        for class_name, teacher_key in pairs:
            classes[class_name].curator = teachers[teacher_key]
            classes[class_name].save(update_fields=["curator"])

    def seed_students(self, school, classes):
        students = []
        class_cycle = ["9-A", "9-A", "9-A", "9-B", "9-B", "9-B", "10-A", "10-A", "10-A"]
        for i, ((first, last), class_name) in enumerate(zip(STUDENT_NAMES, class_cycle), start=1):
            username = f"student{i}"
            user = self.seed_user(username, first, last, User.Role.STUDENT, school, phone=f"+99891111{i:04d}")
            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    "school": school,
                    "class_room": classes[class_name],
                    "age": 15 if class_name.startswith("9") else 16,
                    "student_code": f"S-{i:04d}",
                },
            )
            students.append(profile)
        return students

    def seed_parents(self, students):
        parents = []
        # parent1 -> student1 (single child); parent2 -> student2 & student3 (siblings)
        groups = [("parent1", [students[0]]), ("parent2", [students[1], students[2]]), ("parent3", [students[3]])]
        for i, (username, children) in enumerate(groups, start=1):
            last_name = f"{children[0].user.first_name}ning ota-onasi"
            user = self.seed_user(username, "Ota-ona", last_name, User.Role.PARENT, children[0].school, phone=f"+99892222{i:04d}")
            profile, _ = ParentProfile.objects.get_or_create(user=user)
            for child in children:
                ParentStudent.objects.get_or_create(parent=profile, student=child, defaults={"relation": ParentStudent.Relation.GUARDIAN})
            parents.append(profile)
        return parents

    def seed_lessons(self, classes, subjects, teachers):
        today = timezone.localdate()
        # 4 time slots x 3 classes, each teacher appears at most once per slot (no
        # teacher/room double-booking) so every class gets >= 4 lessons a day.
        schedule = [
            # slot 1 — 9:00
            ("9-A", "Matematika", "teacher_math", "9:00", "9:45", "101"),
            ("9-B", "Ingliz tili", "teacher_eng", "9:00", "9:45", "102"),
            ("10-A", "Informatika", "teacher_it", "9:00", "9:45", "201"),
            # slot 2 — 10:00
            ("9-A", "Ingliz tili", "teacher_eng", "10:00", "10:45", "102"),
            ("9-B", "Informatika", "teacher_it", "10:00", "10:45", "201"),
            ("10-A", "Tarix", "teacher_hist", "10:00", "10:45", "103"),
            # slot 3 — 11:00
            ("9-A", "Informatika", "teacher_it", "11:00", "11:45", "201"),
            ("9-B", "Ona tili", "teacher_hist", "11:00", "11:45", "103"),
            ("10-A", "Fizika", "teacher_math", "11:00", "11:45", "101"),
            # slot 4 — 12:00
            ("9-A", "Tarix", "teacher_hist", "12:00", "12:45", "103"),
            ("9-B", "Matematika", "teacher_math", "12:00", "12:45", "101"),
            ("10-A", "Ingliz tili", "teacher_eng", "12:00", "12:45", "102"),
        ]
        lessons = []
        for day_offset in range(-3, 4):
            day = today + datetime.timedelta(days=day_offset)
            if day.weekday() == 6:  # Sunday off
                continue
            for class_name, subj_name, teacher_key, start, end, room in schedule:
                lesson, _ = Lesson.objects.get_or_create(
                    class_room=classes[class_name],
                    subject=subjects[subj_name],
                    teacher=teachers[teacher_key],
                    date=day,
                    start_time=start,
                    defaults={"end_time": end, "room": room},
                )
                lessons.append(lesson)
        return lessons

    def seed_grades(self, students, subjects, teachers, academic_year, quarters):
        teacher_by_subject = {
            "Matematika": teachers["teacher_math"],
            "Fizika": teachers["teacher_math"],
            "Informatika": teachers["teacher_it"],
            "Ingliz tili": teachers["teacher_eng"],
            "Ona tili": teachers["teacher_hist"],
            "Tarix": teachers["teacher_hist"],
            "Biologiya": teachers["teacher_hist"],
        }
        # Always regenerate from scratch so re-running the seeder after a grading-scale
        # change (or just to get fresh random values) never leaves stale out-of-range rows.
        Grade.objects.filter(student__in=students).delete()
        rng = random.Random(42)
        for student in students:
            for subj_name in ["Matematika", "Ingliz tili", "Informatika", "Tarix"]:
                for q_number in [1, 2, 3, 4]:
                    if q_number > 2 and rng.random() < 0.4:
                        continue  # leave some quarters ungraded for realism
                    Grade.objects.get_or_create(
                        student=student,
                        subject=subjects[subj_name],
                        quarter=quarters[q_number],
                        grade_type=Grade.GradeType.QUARTER,
                        defaults={
                            "teacher": teacher_by_subject[subj_name],
                            "academic_year": academic_year,
                            "value": rng.randint(6, 10),
                            "comment": "",
                        },
                    )
            # a few extra daily/homework grades for the current quarter
            for subj_name in ["Matematika", "Ingliz tili"]:
                Grade.objects.get_or_create(
                    student=student,
                    subject=subjects[subj_name],
                    quarter=quarters[1],
                    grade_type=Grade.GradeType.DAILY,
                    defaults={
                        "teacher": teacher_by_subject[subj_name],
                        "academic_year": academic_year,
                        "value": rng.randint(5, 10),
                    },
                )

    def seed_attendance(self, students, teachers):
        today = timezone.localdate()
        rng = random.Random(7)
        for student in students:
            for day_offset in range(1, 21):
                day = today - datetime.timedelta(days=day_offset)
                if day.weekday() == 6:
                    continue
                roll = rng.random()
                status = AttendanceStatus.PRESENT
                if roll < 0.08:
                    status = AttendanceStatus.ABSENT
                elif roll < 0.14:
                    status = AttendanceStatus.LATE
                Attendance.objects.get_or_create(
                    student=student,
                    date=day,
                    subject=None,
                    defaults={"class_room": student.class_room, "status": status, "marked_by": teachers["teacher_math"]},
                )
        for teacher in teachers.values():
            for day_offset in range(1, 8):
                day = today - datetime.timedelta(days=day_offset)
                if day.weekday() == 6:
                    continue
                TeacherAttendance.objects.get_or_create(teacher=teacher, date=day, defaults={"status": AttendanceStatus.PRESENT})

    def seed_assignments(self, lessons, teachers, students):
        deadline = timezone.now() + datetime.timedelta(days=5)
        assignments = []
        by_class = {}
        for lesson in lessons:
            by_class.setdefault((lesson.class_room_id, lesson.subject_id), lesson)
        picked = list(by_class.values())[:3]
        for i, lesson in enumerate(picked, start=1):
            assignment, _ = Assignment.objects.get_or_create(
                lesson=lesson,
                title=f"{lesson.subject.name} — {i}-uy vazifa",
                defaults={
                    "teacher": lesson.teacher,
                    "description": "Darslikdagi mos mavzu bo'yicha mashqlarni bajaring.",
                    "deadline": deadline,
                },
            )
            assignments.append(assignment)

        class_students = [s for s in students if s.class_room_id == picked[0].class_room_id] if picked else []
        if assignments and class_students:
            AssignmentSubmission.objects.get_or_create(
                assignment=assignments[0],
                student=class_students[0],
                defaults={"answer": "Vazifa bajarildi, biriktirilgan javoblarga qarang.", "status": AssignmentSubmission.Status.SUBMITTED},
            )
        return assignments

    def seed_quiz(self, classes, subjects, teachers, students):
        quiz, _ = Quiz.objects.get_or_create(
            title="Matematika — 1-chorak yakuniy test",
            subject=subjects["Matematika"],
            class_room=classes["9-A"],
            teacher=teachers["teacher_math"],
            defaults={"deadline": timezone.now() + datetime.timedelta(days=7), "time_limit_minutes": 20},
        )
        questions_data = [
            ("2 + 2 x 2 nechaga teng?", ["6", "8", "4"], 0, 2),
            ("Kvadratning yuzi qanday hisoblanadi?", ["a x b", "a x a", "2a"], 1, 2),
            ("To'g'ri to'rtburchakning burchaklari nechchi darajali?", ["90", "45", "180"], 0, 1),
        ]
        questions = []
        for question, options, correct, points in questions_data:
            q, _ = Question.objects.get_or_create(
                quiz=quiz, question=question, defaults={"options": options, "correct_answer": correct, "points": points}
            )
            questions.append(q)

        class_students = [s for s in students if s.class_room_id == classes["9-A"].id]
        if class_students:
            answers = {str(q.id): q.correct_answer for q in questions[:-1]}
            QuizAttempt.objects.get_or_create(
                quiz=quiz,
                student=class_students[0],
                defaults={"answers": answers, "score": sum(q.points for q in questions[:-1]), "max_score": sum(q.points for q in questions), "submitted_at": timezone.now()},
            )

    def seed_library(self, subjects, admin):
        materials = [
            ("Algebra 9-sinf darsligi", "BOOK", "Matematika", "Vazirlik"),
            ("Fizika laboratoriya qo'llanmasi", "PDF", "Fizika", "O.Sattorov"),
            ("Python asoslari — video kurs", "VIDEO", "Informatika", "J.Nematov"),
            ("Jahon tarixi xronologiyasi", "DOCUMENT", "Tarix", "Z.Qodirova"),
        ]
        for title, mtype, subj_name, author in materials:
            LibraryMaterial.objects.get_or_create(
                title=title, defaults={"material_type": mtype, "subject": subjects[subj_name], "author": author, "uploaded_by": admin}
            )

    def seed_announcements(self, admin, classes):
        Announcement.objects.get_or_create(
            title="1-chorak yakuni bo'yicha ota-onalar yig'ilishi",
            defaults={
                "content": "Hurmatli ota-onalar, 1-chorak yakunlariga bag'ishlangan yig'ilish shanba kuni soat 10:00 da bo'lib o'tadi.",
                "priority": Announcement.Priority.NORMAL,
                "target": Announcement.Target.PARENTS,
                "created_by": admin,
            },
        )
        Announcement.objects.get_or_create(
            title="Fan olimpiadasiga ro'yxatdan o'tish boshlandi",
            defaults={
                "content": "Matematika va fizika fanlari bo'yicha maktab ichki olimpiadasiga ro'yxatdan o'tish boshlandi.",
                "priority": Announcement.Priority.HIGH,
                "target": Announcement.Target.STUDENTS,
                "created_by": admin,
            },
        )

    def seed_helpdesk(self, students):
        HelpDeskTicket.objects.get_or_create(
            user=students[0].user,
            title="Elektron kutubxonaga kira olmayapman",
            defaults={"description": "Kutubxona bo'limini ochsam xatolik chiqmoqda.", "category": HelpDeskTicket.Category.TECHNICAL},
        )

    # ------------------------------------------------------------------ #

    def print_summary(self, superadmin, admin, teachers, students, parents):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo ma'lumotlar tayyor! Barcha hisoblar uchun parol:"))
        self.stdout.write(self.style.WARNING(f"  {DEMO_PASSWORD}"))
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Login qilish uchun hisoblar:"))
        rows = [
            ("SUPERADMIN", superadmin.username),
            ("ADMIN", admin.username),
            ("DIRECTOR", "director"),
            ("DEPUTY_DIRECTOR", "deputy"),
        ]
        rows += [("TEACHER", t.user.username) for t in teachers.values()]
        rows += [("STUDENT", s.user.username) for s in students[:3]]
        rows += [("PARENT", p.user.username) for p in parents]
        width = max(len(r[0]) for r in rows) + 2
        for role, username in rows:
            self.stdout.write(f"  {role.ljust(width)} {username}")
        self.stdout.write("")
        self.stdout.write(f"  (... jami {len(students)} student{'lar' if len(students) != 1 else ''}: student1..student{len(students)})")
