"""Create one demo account per role, so a fresh deploy has something to log in with.

Idempotent (get_or_create / update_or_create throughout) — safe to run on every deploy.
Usage: python manage.py seed_demo_users
"""

import datetime
import os

from django.core.management.base import BaseCommand
from django.db import transaction

# Set via the DEMO_USERS_PASSWORD env var in each environment — never hardcode a real
# password in source control. Local/dev falls back to a clearly-labelled placeholder.
DEMO_PASSWORD = os.environ.get("DEMO_USERS_PASSWORD", "change-me-dev-only")


class Command(BaseCommand):
    help = "Creates one demo user per role (SUPERADMIN, ADMIN, DIRECTOR, DEPUTY_DIRECTOR, TEACHER, STUDENT, PARENT)."

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.classes.models import AcademicYear, ClassRoom
        from apps.schools.models import School
        from apps.users.models import (
            ParentProfile,
            ParentStudent,
            StudentProfile,
            TeacherProfile,
            User,
        )

        school, _ = School.objects.get_or_create(
            name="MaktabIQ Demo maktabi",
            defaults={"address": "Toshkent", "phone": "+998900000000"},
        )
        academic_year, _ = AcademicYear.objects.get_or_create(
            name="2026-2027",
            defaults={
                "start_date": datetime.date(2026, 9, 1),
                "end_date": datetime.date(2027, 6, 1),
                "is_active": True,
            },
        )

        def make_user(username, role, first_name, last_name):
            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "role": role,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": f"{username}@maktabiq.demo",
                    "school": None if role == User.Role.SUPERADMIN else school,
                    "is_staff": role in (User.Role.SUPERADMIN, User.Role.ADMIN),
                    "is_superuser": role == User.Role.SUPERADMIN,
                },
            )
            user.set_password(DEMO_PASSWORD)
            user.save()
            return user

        make_user("superadmin", User.Role.SUPERADMIN, "Super", "Admin")
        make_user("admin", User.Role.ADMIN, "Maktab", "Admin")
        make_user("director", User.Role.DIRECTOR, "Maktab", "Direktori")
        make_user("deputy", User.Role.DEPUTY_DIRECTOR, "O'quv ishlari", "Direktor o'rinbosari")

        teacher_user = make_user("teacher", User.Role.TEACHER, "Aziz", "O'qituvchi")
        teacher_profile, created = TeacherProfile.objects.get_or_create(
            user=teacher_user,
            defaults={"school": school, "teacher_id": f"T-{teacher_user.id:05d}"},
        )
        if not created:
            teacher_profile.school = school
            teacher_profile.save(update_fields=["school"])

        class_room, _ = ClassRoom.objects.update_or_create(
            school=school,
            name="9-A",
            academic_year=academic_year,
            defaults={"grade": 9, "curator": teacher_profile},
        )

        student_user = make_user("student", User.Role.STUDENT, "Sardor", "O'quvchi")
        student_profile, created = StudentProfile.objects.get_or_create(
            user=student_user,
            defaults={
                "school": school,
                "class_room": class_room,
                "student_code": f"S-{student_user.id:05d}",
            },
        )
        if not created:
            student_profile.school = school
            student_profile.class_room = class_room
            student_profile.save(update_fields=["school", "class_room"])

        parent_user = make_user("parent", User.Role.PARENT, "Bahodir", "Ota-ona")
        parent_profile, _ = ParentProfile.objects.get_or_create(user=parent_user)
        ParentStudent.objects.get_or_create(
            parent=parent_profile,
            student=student_profile,
            defaults={"relation": ParentStudent.Relation.FATHER},
        )

        self.stdout.write(self.style.SUCCESS("Demo users ready (password from DEMO_USERS_PASSWORD)."))
