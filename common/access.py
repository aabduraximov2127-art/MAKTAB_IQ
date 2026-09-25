"""Object-level access rules built on top of ``common/rbac.py``.

A *permission* says what **kind** of access a user has (``view_own_grades``,
``view_all_grades``, ``view_assigned_grades`` ...). The helpers here say to **which
objects** it applies, following the project's existing relations::

    Student -> Class, Student -> Parent (ParentStudent), Student -> Grade / Attendance /
    Submission, Teacher -> Subject (TeacherProfile.subjects), Teacher -> Class (curator /
    lessons), Class -> Students / Teachers, Lesson -> (Class, Subject, Teacher) ...

Every list endpoint filters its queryset through one of the ``*_scope`` functions, and every
detail/write check goes through the matching ``can_*`` function, so "what you may list" and
"what you may open" can never drift apart.

Scoping levels, from widest to narrowest:

* **global**  — SUPERADMIN only (``rbac.is_global``): no filter at all.
* **school**  — Admin / Director / Deputy director with a ``view_all_*`` permission: their own
  school only (a school-bound user with *no* school sees only rows that have no school).
* **own / child / assigned / class** — the relation-based permissions, combined with OR
  when a user holds several roles (Teacher + Parent sees both their pupils and their child).
"""

from __future__ import annotations

from django.db.models import Q

from . import rbac
from .rbac import (
    CREATE_GRADE,
    MANAGE_CLASS_ATTENDANCE,
    MANAGE_CLASS_HOMEWORK,
    MANAGE_CLASS_PARENTS,
    MANAGE_CLASS_STUDENTS,
    MANAGE_STUDENTS,
    TRANSFER_STUDENTS,
    UPDATE_ATTENDANCE,
    UPDATE_CHILD_PROFILE,
    UPDATE_OWN_PROFILE,
    VIEW_ALL_ANNOUNCEMENTS,
    VIEW_ALL_ATTENDANCE,
    VIEW_ALL_CLASSES,
    VIEW_ALL_GRADES,
    VIEW_ALL_HOMEWORK,
    VIEW_ALL_PARENTS,
    VIEW_ALL_QUIZZES,
    VIEW_ALL_SCHEDULE,
    VIEW_ALL_STUDENTS,
    VIEW_ALL_SUBJECTS,
    VIEW_ALL_TEACHERS,
    VIEW_ASSIGNED_ATTENDANCE,
    VIEW_ASSIGNED_CLASSES,
    VIEW_ASSIGNED_GRADES,
    VIEW_ASSIGNED_HOMEWORK,
    VIEW_ASSIGNED_QUIZZES,
    VIEW_ASSIGNED_STUDENTS,
    VIEW_CHILD_ATTENDANCE,
    VIEW_CHILD_CLASS,
    VIEW_CHILD_GRADES,
    VIEW_CHILD_HOMEWORK,
    VIEW_CHILD_PROFILE,
    VIEW_CHILD_QUIZZES,
    VIEW_CHILD_SCHEDULE,
    VIEW_CHILD_TEACHERS,
    VIEW_CLASS_REPORTS,
    VIEW_CLASS_STUDENTS,
    VIEW_CLASS_TEACHERS,
    VIEW_CLASSMATES,
    VIEW_OWN_ATTENDANCE,
    VIEW_OWN_CLASS,
    VIEW_OWN_GRADES,
    VIEW_OWN_HOMEWORK,
    VIEW_OWN_PROFILE,
    VIEW_OWN_QUIZZES,
    VIEW_OWN_SCHEDULE,
    VIEW_OWN_SUBJECTS,
    VIEW_OWN_TEACHER_ATTENDANCE,
    VIEW_OWN_TEACHERS,
    VIEW_SENSITIVE_STUDENT_DATA,
)

# ---------------------------------------------------------------------------
# Small relation helpers
# ---------------------------------------------------------------------------


def student_profile_of(user):
    return getattr(user, "student_profile", None)


def teacher_profile_of(user):
    return getattr(user, "teacher_profile", None)


def own_class_id(user):
    return getattr(student_profile_of(user), "class_room_id", None)


def curates(user, class_room) -> bool:
    """Is ``user`` the class teacher (curator) of ``class_room``?"""
    if class_room is None or not class_room.curator_id:
        return False
    return class_room.curator.user_id == user.id


def teaches_in(user, class_room) -> bool:
    """Does ``user`` have at least one lesson in ``class_room``?"""
    if class_room is None:
        return False
    return class_room.lessons.filter(teacher__user_id=user.id).exists()


def assigned_to_class(user, class_room) -> bool:
    """Teacher is *assigned* to a class when they curate it or teach a lesson in it."""
    return curates(user, class_room) or teaches_in(user, class_room)


def teaches_subject(user, subject) -> bool:
    """A teacher is assigned to a subject via ``TeacherProfile.subjects`` or a lesson."""
    profile = teacher_profile_of(user)
    if profile is None or subject is None:
        return False
    return profile.subjects.filter(pk=subject.pk).exists() or profile.lessons.filter(subject=subject).exists()


def same_school(user, school_id) -> bool:
    """Global users pass; school-bound users only for their own (non-null) school."""
    if rbac.is_global(user):
        return True
    return bool(user.school_id) and user.school_id == school_id


# ---------------------------------------------------------------------------
# The scoping engine
# ---------------------------------------------------------------------------


def scoped(qs, user, *, all_perm, school_field, parts):
    """Filter ``qs`` down to what ``user`` may see.

    ``all_perm`` — permission that lifts the filter to the whole school (or everything for a
    global user). ``school_field`` — ORM path to the row's school (``None`` when the model
    has no school, e.g. Subject). ``parts`` — ``[(permission, Q | callable -> Q | None)]``:
    the user sees the union of the parts whose permission they hold.
    """
    if all_perm and rbac.has_perm(user, all_perm):
        if rbac.is_global(user) or school_field is None:
            return qs
        # A school-bound user sees their own school's rows. One with no school assigned sees
        # only rows that belong to no school either (``school IS NULL`` — the long-standing
        # behaviour), never another school's data.
        return qs.filter(**{school_field: user.school_id if user.school_id else None})

    combined = None
    for perm, cond in parts:
        if not rbac.has_perm(user, perm):
            continue
        q = cond() if callable(cond) else cond
        if q is None:
            continue
        combined = q if combined is None else (combined | q)
    return qs.none() if combined is None else qs.filter(combined).distinct()


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------


def students_scope(user, qs):
    def classmates():
        cid = own_class_id(user)
        return Q(class_room_id=cid) if cid else None

    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_STUDENTS,
        school_field="school",
        parts=[
            (VIEW_OWN_PROFILE, Q(user=user)),
            (VIEW_CLASSMATES, classmates),
            (VIEW_CHILD_PROFILE, Q(parent_links__parent__user=user)),
            (
                VIEW_ASSIGNED_STUDENTS,
                Q(class_room__lessons__teacher__user=user) | Q(class_room__curator__user=user),
            ),
            (VIEW_CLASS_STUDENTS, Q(class_room__curator__user=user)),
        ],
    )


def can_view_student(user, student) -> bool:
    """Retrieve-level access to one student profile. Stricter than the list: a student sees
    classmates in the list (for chat) but may only *open* their own profile."""
    if rbac.has_perm(user, VIEW_ALL_STUDENTS) and same_school(user, student.school_id):
        return True
    if rbac.has_perm(user, VIEW_OWN_PROFILE) and student.user_id == user.id:
        return True
    if rbac.has_perm(user, VIEW_CHILD_PROFILE) and student.parent_links.filter(parent__user=user).exists():
        return True
    room = student.class_room
    if room is not None:
        if rbac.has_perm(user, VIEW_ASSIGNED_STUDENTS) and assigned_to_class(user, room):
            return True
        if rbac.has_perm(user, VIEW_CLASS_STUDENTS) and curates(user, room):
            return True
    return False


def can_edit_student(user, student, *, method: str = "PATCH") -> bool:
    """Write access to a student's basic profile. Class transfer and student_code never go
    through this (see ``can_transfer_student``)."""
    if method == "DELETE":
        return rbac.has_perm(user, MANAGE_STUDENTS) and can_view_student(user, student)
    if rbac.has_perm(user, MANAGE_STUDENTS) and can_view_student(user, student):
        return True
    if rbac.has_perm(user, MANAGE_CLASS_STUDENTS) and curates(user, student.class_room):
        return True
    if rbac.has_perm(user, UPDATE_CHILD_PROFILE) and student.parent_links.filter(parent__user=user).exists():
        return True
    if rbac.has_perm(user, UPDATE_OWN_PROFILE) and student.user_id == user.id:
        return True
    return False


def can_transfer_student(user, student, new_class) -> bool:
    """Moving a student to another class needs ``transfer_students`` *and* the right relation:
    school-wide roles (admin/director) inside their own school, a class teacher for a student
    of their own class, or any teacher who was explicitly granted the permission, for their
    own pupils. The destination must always be in the same school as the student."""
    if not rbac.has_perm(user, TRANSFER_STUDENTS):
        return False
    if rbac.is_global(user):
        return True
    if student.school_id is None or new_class.school_id != student.school_id:
        return False
    if rbac.has_perm(user, VIEW_ALL_STUDENTS) and user.school_id and user.school_id == student.school_id:
        return True
    room = student.class_room
    if room is None:
        return False
    if rbac.CLASS_TEACHER in rbac.effective_roles(user) and curates(user, room):
        return True
    if TRANSFER_STUDENTS in rbac.access_for(user).extra_permissions and assigned_to_class(user, room):
        return True
    return False


# ---------------------------------------------------------------------------
# Teachers / parents / classes / subjects
# ---------------------------------------------------------------------------


def teachers_scope(user, qs):
    def own_class_teachers():
        cid = own_class_id(user)
        if not cid:
            return None
        return Q(lessons__class_room_id=cid) | Q(curated_classes__id=cid)

    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_TEACHERS,
        school_field="school",
        parts=[
            (VIEW_OWN_PROFILE, Q(user=user)),
            (VIEW_OWN_TEACHERS, own_class_teachers),
            (
                VIEW_CHILD_TEACHERS,
                Q(lessons__class_room__students__parent_links__parent__user=user)
                | Q(curated_classes__students__parent_links__parent__user=user),
            ),
            (
                VIEW_CLASS_TEACHERS,
                Q(lessons__class_room__curator__user=user) | Q(curated_classes__curator__user=user),
            ),
        ],
    )


def parents_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_PARENTS,
        school_field="user__school",
        parts=[
            (VIEW_OWN_PROFILE, Q(user=user)),
            (MANAGE_CLASS_PARENTS, Q(children_links__student__class_room__curator__user=user)),
        ],
    )


def classes_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_CLASSES,
        school_field="school",
        parts=[
            (VIEW_ASSIGNED_CLASSES, Q(curator__user=user) | Q(lessons__teacher__user=user)),
            (VIEW_CLASS_STUDENTS, Q(curator__user=user)),
            (VIEW_OWN_CLASS, Q(students__user=user)),
            (VIEW_CHILD_CLASS, Q(students__parent_links__parent__user=user)),
        ],
    )


def subjects_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_SUBJECTS,
        school_field=None,  # Subject is a school-independent catalogue
        parts=[
            (
                VIEW_OWN_SUBJECTS,
                Q(lessons__class_room__students__user=user)
                | Q(grades__student__user=user)
                | Q(teachers__user=user)
                | Q(lessons__teacher__user=user),
            ),
            (
                VIEW_CHILD_CLASS,
                Q(lessons__class_room__students__parent_links__parent__user=user)
                | Q(grades__student__parent_links__parent__user=user),
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Schedule / grades / attendance / homework / quizzes
# ---------------------------------------------------------------------------


def lessons_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_SCHEDULE,
        school_field="class_room__school",
        parts=[
            (VIEW_OWN_SCHEDULE, Q(class_room__students__user=user) | Q(teacher__user=user)),
            (VIEW_CHILD_SCHEDULE, Q(class_room__students__parent_links__parent__user=user)),
            (VIEW_CLASS_REPORTS, Q(class_room__curator__user=user)),
        ],
    )


def grades_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_GRADES,
        school_field="student__school",
        parts=[
            (VIEW_OWN_GRADES, Q(student__user=user)),
            (VIEW_CHILD_GRADES, Q(student__parent_links__parent__user=user)),
            (VIEW_ASSIGNED_GRADES, Q(teacher__user=user)),
            (VIEW_CLASS_REPORTS, Q(student__class_room__curator__user=user)),
        ],
    )


def attendance_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_ATTENDANCE,
        school_field="class_room__school",
        parts=[
            (VIEW_OWN_ATTENDANCE, Q(student__user=user)),
            (VIEW_CHILD_ATTENDANCE, Q(student__parent_links__parent__user=user)),
            (VIEW_ASSIGNED_ATTENDANCE, Q(marked_by__user=user) | Q(class_room__curator__user=user)),
            (VIEW_CLASS_REPORTS, Q(class_room__curator__user=user)),
        ],
    )


def teacher_attendance_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_ATTENDANCE,
        school_field="teacher__school",
        parts=[(VIEW_OWN_TEACHER_ATTENDANCE, Q(teacher__user=user))],
    )


def assignments_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_HOMEWORK,
        school_field="lesson__class_room__school",
        parts=[
            (VIEW_OWN_HOMEWORK, Q(lesson__class_room__students__user=user)),
            (VIEW_CHILD_HOMEWORK, Q(lesson__class_room__students__parent_links__parent__user=user)),
            (VIEW_ASSIGNED_HOMEWORK, Q(teacher__user=user)),
            (VIEW_CLASS_REPORTS, Q(lesson__class_room__curator__user=user)),
        ],
    )


def submissions_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_HOMEWORK,
        school_field="assignment__lesson__class_room__school",
        parts=[
            (VIEW_OWN_HOMEWORK, Q(student__user=user)),
            (VIEW_CHILD_HOMEWORK, Q(student__parent_links__parent__user=user)),
            (VIEW_ASSIGNED_HOMEWORK, Q(assignment__teacher__user=user)),
            (VIEW_CLASS_REPORTS, Q(assignment__lesson__class_room__curator__user=user)),
        ],
    )


def quizzes_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_QUIZZES,
        school_field="class_room__school",
        parts=[
            (VIEW_OWN_QUIZZES, Q(class_room__students__user=user)),
            (VIEW_CHILD_QUIZZES, Q(class_room__students__parent_links__parent__user=user)),
            (VIEW_ASSIGNED_QUIZZES, Q(teacher__user=user)),
            (VIEW_CLASS_REPORTS, Q(class_room__curator__user=user)),
        ],
    )


def quiz_attempts_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=VIEW_ALL_QUIZZES,
        school_field="quiz__class_room__school",
        parts=[
            (VIEW_OWN_QUIZZES, Q(student__user=user)),
            (VIEW_CHILD_QUIZZES, Q(student__parent_links__parent__user=user)),
            (VIEW_ASSIGNED_QUIZZES, Q(quiz__teacher__user=user)),
            (VIEW_CLASS_REPORTS, Q(quiz__class_room__curator__user=user)),
        ],
    )


# ---------------------------------------------------------------------------
# Student documents / health records / transfer history
# ---------------------------------------------------------------------------


def student_documents_scope(user, qs):
    return scoped(
        qs,
        user,
        all_perm=MANAGE_STUDENTS,
        school_field="student__school",
        parts=[
            (VIEW_OWN_PROFILE, Q(student__user=user)),
            (VIEW_CHILD_PROFILE, Q(student__parent_links__parent__user=user)),
        ],
    )


def health_records_scope(user, qs):
    return scoped(qs, user, all_perm=VIEW_SENSITIVE_STUDENT_DATA, school_field="student__school", parts=[])


def transfer_history_scope(user, qs):
    """History rows of the students the user may open — staff only (never student/parent)."""
    from apps.users.models import StudentProfile

    staff = rbac.has_any_perm(user, VIEW_ALL_STUDENTS, VIEW_ASSIGNED_STUDENTS, VIEW_CLASS_STUDENTS)
    if not staff:
        return qs.none()
    visible = students_scope(user, StudentProfile.objects.all())
    return qs.filter(student__in=visible)


# ---------------------------------------------------------------------------
# Write-side checks for teachers (assignment rules)
# ---------------------------------------------------------------------------


def can_grade(user, student, subject) -> bool:
    """May ``user`` put a grade for ``student`` in ``subject``?

    * school-wide writers (admin): inside their own school;
    * a teacher: the student's class must be one they are assigned to (curator or a lesson
      there) **and** the subject one they teach (``TeacherProfile.subjects`` or a lesson).
    """
    if not rbac.has_perm(user, CREATE_GRADE):
        return False
    if rbac.has_perm(user, VIEW_ALL_STUDENTS):
        return same_school(user, student.school_id)
    return assigned_to_class(user, student.class_room) and teaches_subject(user, subject)


def can_mark_attendance(user, class_room) -> bool:
    """Attendance may be marked for a class the user is assigned to (teacher), curates
    (class teacher) or administers (school-wide writer, own school)."""
    if rbac.has_perm(user, MANAGE_CLASS_ATTENDANCE) and curates(user, class_room):
        return True
    if rbac.has_perm(user, rbac.MARK_ATTENDANCE):
        if rbac.has_perm(user, VIEW_ALL_STUDENTS):
            return same_school(user, class_room.school_id)
        return assigned_to_class(user, class_room)
    return False


def can_write_attendance(user, attendance) -> bool:
    room = attendance.class_room
    if rbac.has_perm(user, MANAGE_CLASS_ATTENDANCE) and curates(user, room):
        return True
    if not rbac.has_perm(user, UPDATE_ATTENDANCE):
        return False
    if rbac.has_perm(user, VIEW_ALL_ATTENDANCE):
        return same_school(user, room.school_id)
    marked_by = attendance.marked_by
    return (marked_by is not None and marked_by.user_id == user.id) or curates(user, room)


def can_manage_lesson_homework(user, lesson) -> bool:
    """Homework belongs to a lesson: its own teacher, the class teacher of that class
    (``manage_class_homework``) or a school-wide writer of the same school."""
    if rbac.has_perm(user, MANAGE_CLASS_HOMEWORK) and curates(user, lesson.class_room):
        return True
    if not rbac.has_perm(user, rbac.CREATE_HOMEWORK):
        return False
    if rbac.has_perm(user, VIEW_ALL_HOMEWORK):
        return same_school(user, lesson.class_room.school_id)
    return lesson.teacher.user_id == user.id


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------


def announcements_scope(user, qs):
    """School-wide viewers see everything; everyone else sees announcements addressed to the
    whole school, to their audience (teachers / students / parents) or to their class."""
    from apps.notifications.models import Announcement

    if rbac.has_perm(user, VIEW_ALL_ANNOUNCEMENTS):
        return qs

    roles = rbac.effective_roles(user)
    q = Q(target=Announcement.Target.ALL)
    if roles & {rbac.TEACHER, rbac.CLASS_TEACHER}:
        q |= Q(target=Announcement.Target.TEACHERS)
    if rbac.STUDENT in roles:
        q |= Q(target=Announcement.Target.STUDENTS)
    if rbac.PARENT in roles:
        q |= Q(target=Announcement.Target.PARENTS)

    class_ids = set()
    if rbac.STUDENT in roles and own_class_id(user):
        class_ids.add(own_class_id(user))
    if rbac.PARENT in roles:
        from apps.users.models import StudentProfile

        class_ids |= set(
            StudentProfile.objects.filter(parent_links__parent__user=user, class_room__isnull=False).values_list(
                "class_room_id", flat=True
            )
        )
    if rbac.CLASS_TEACHER in roles:
        from apps.classes.models import ClassRoom

        class_ids |= set(ClassRoom.objects.filter(curator__user=user).values_list("id", flat=True))
    if class_ids:
        q |= Q(target=Announcement.Target.CLASS, target_class_id__in=class_ids)

    # a class teacher can always see (and manage) what they themselves sent
    q |= Q(created_by=user)
    return qs.filter(q).distinct()
