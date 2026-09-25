"""MaktabIQ role & permission system (RBAC).

Design — no new models, everything reuses what Django / the project already has:

* **Primary role**  -> ``User.role`` (existing field; SUPERADMIN, ADMIN, DIRECTOR,
  DEPUTY_DIRECTOR, TEACHER, STUDENT, PARENT).
* **Extra roles**   -> membership in a Django ``Group`` named exactly like the role code
  (``User.groups``, provided by ``AbstractUser``). A user may hold several roles at once
  (Teacher + Parent, Director + Teacher, Admin + Teacher ...); permissions are the *union*.
* **Class Teacher** -> *derived*, never stored: a user is a Class Teacher exactly when they
  are the ``curator`` of at least one ``ClassRoom`` (existing relation). The permissions of
  that role are always applied **per class** (object level), so being curator of 9-A gives
  nothing on 9-B.
* **Role -> permission defaults** live in this file (``ROLE_PERMISSIONS``), i.e. in code
  review, not in mutable rows.
* **Per-user grants**  -> ``User.user_permissions`` (Django's own M2M) is honoured on top of
  the role defaults, so an admin can hand one specific teacher e.g. ``transfer_students``
  without giving it to every teacher.

Permission codenames are stored as ordinary ``auth.Permission`` rows on the ``users.User``
content type (created on demand by :func:`get_permission_row`), so they also show up in the
Django admin.

Object-level rules (who may see *which* student/grade/...) are in ``common/access.py`` and
are built on :func:`has_perm` from here — a permission says *what kind* of access, the
scope helpers say *to which objects*.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
SUPERADMIN = "SUPERADMIN"
ADMIN = "ADMIN"
DIRECTOR = "DIRECTOR"
DEPUTY_DIRECTOR = "DEPUTY_DIRECTOR"
TEACHER = "TEACHER"
CLASS_TEACHER = "CLASS_TEACHER"  # derived from ClassRoom.curator, never stored
STUDENT = "STUDENT"
PARENT = "PARENT"

# Roles that can be stored on a user (as ``User.role`` or as a Group membership).
STORED_ROLES = (SUPERADMIN, ADMIN, DIRECTOR, DEPUTY_DIRECTOR, TEACHER, STUDENT, PARENT)
DERIVED_ROLES = (CLASS_TEACHER,)
ALL_ROLES = STORED_ROLES + DERIVED_ROLES

ROLE_LABELS = {
    SUPERADMIN: "Superadmin",
    ADMIN: "Admin",
    DIRECTOR: "Direktor",
    DEPUTY_DIRECTOR: "Direktor o'rinbosari",
    TEACHER: "O'qituvchi",
    CLASS_TEACHER: "Sinf rahbari",
    STUDENT: "O'quvchi",
    PARENT: "Ota-ona",
}

# ---------------------------------------------------------------------------
# Permission codenames
# ---------------------------------------------------------------------------
# -- own data (student, and every user's own profile) --
VIEW_OWN_PROFILE = "view_own_profile"
UPDATE_OWN_PROFILE = "update_own_profile"  # NOT a default of any role — grant per user
VIEW_OWN_CLASS = "view_own_class"
VIEW_OWN_TEACHERS = "view_own_teachers"
VIEW_OWN_SUBJECTS = "view_own_subjects"
VIEW_OWN_GRADES = "view_own_grades"
VIEW_OWN_ATTENDANCE = "view_own_attendance"
VIEW_OWN_HOMEWORK = "view_own_homework"
VIEW_OWN_QUIZZES = "view_own_quizzes"
VIEW_OWN_SCHEDULE = "view_own_schedule"
VIEW_CLASSMATES = "view_classmates"
SUBMIT_HOMEWORK = "submit_homework"
TAKE_QUIZ = "take_quiz"
USE_AI_ASSISTANT = "use_ai_assistant"
VIEW_ANNOUNCEMENTS = "view_announcements"
USE_CHAT = "use_chat"
CREATE_PRIVATE_CHAT = "create_private_chat"
VIEW_LIBRARY = "view_library"

# -- a parent's linked children --
VIEW_CHILD_PROFILE = "view_child_profile"
UPDATE_CHILD_PROFILE = "update_child_profile"
VIEW_CHILD_CLASS = "view_child_class"
VIEW_CHILD_TEACHERS = "view_child_teachers"
VIEW_CHILD_GRADES = "view_child_grades"
VIEW_CHILD_ATTENDANCE = "view_child_attendance"
VIEW_CHILD_HOMEWORK = "view_child_homework"
VIEW_CHILD_QUIZZES = "view_child_quizzes"
VIEW_CHILD_SCHEDULE = "view_child_schedule"
SUBMIT_ABSENCE_REASON = "submit_absence_reason"

# -- teacher: work inside the classes / subjects assigned to them --
VIEW_ASSIGNED_STUDENTS = "view_assigned_students"
VIEW_ASSIGNED_CLASSES = "view_assigned_classes"
VIEW_ASSIGNED_GRADES = "view_assigned_grades"
VIEW_ASSIGNED_ATTENDANCE = "view_assigned_attendance"
VIEW_ASSIGNED_HOMEWORK = "view_assigned_homework"
VIEW_ASSIGNED_QUIZZES = "view_assigned_quizzes"
VIEW_OWN_TEACHER_ATTENDANCE = "view_own_teacher_attendance"
CREATE_GRADE = "create_grade"
UPDATE_GRADE = "update_grade"
DELETE_GRADE = "delete_grade"
CREATE_HOMEWORK = "create_homework"
UPDATE_HOMEWORK = "update_homework"
DELETE_HOMEWORK = "delete_homework"
GRADE_SUBMISSIONS = "grade_submissions"
MARK_ATTENDANCE = "mark_attendance"
UPDATE_ATTENDANCE = "update_attendance"
MANAGE_QUIZZES = "manage_quizzes"
MANAGE_LIBRARY = "manage_library"
CREATE_CHAT_ROOMS = "create_chat_rooms"
TRANSFER_STUDENTS = "transfer_students"  # teachers only get it by explicit per-user grant

# -- class teacher (curator): every one of these applies to the curated class(es) only --
VIEW_CLASS_STUDENTS = "view_class_students"
VIEW_CLASS_TEACHERS = "view_class_teachers"
VIEW_CLASS_REPORTS = "view_class_reports"
MANAGE_CLASS_STUDENTS = "manage_class_students"
MANAGE_CLASS_ATTENDANCE = "manage_class_attendance"
MANAGE_CLASS_HOMEWORK = "manage_class_homework"
SEND_CLASS_ANNOUNCEMENT = "send_class_announcement"
MANAGE_CLASS_PARENTS = "manage_class_parents"  # optional: grant per user

# -- school-wide read access (deputy director, director, admin, superadmin) --
VIEW_ALL_STUDENTS = "view_all_students"
VIEW_ALL_TEACHERS = "view_all_teachers"
VIEW_ALL_PARENTS = "view_all_parents"
VIEW_ALL_CLASSES = "view_all_classes"
VIEW_ALL_SUBJECTS = "view_all_subjects"
VIEW_ALL_GRADES = "view_all_grades"
VIEW_ALL_ATTENDANCE = "view_all_attendance"
VIEW_ALL_HOMEWORK = "view_all_homework"
VIEW_ALL_QUIZZES = "view_all_quizzes"
VIEW_ALL_SCHEDULE = "view_all_schedule"
VIEW_ALL_ANNOUNCEMENTS = "view_all_announcements"
VIEW_REPORTS = "view_reports"
VIEW_SENSITIVE_STUDENT_DATA = "view_sensitive_student_data"

# -- management (admin / technical + a few academic ones) --
MANAGE_USERS = "manage_users"
MANAGE_ROLES = "manage_roles"
MANAGE_PERMISSIONS = "manage_permissions"
MANAGE_STUDENTS = "manage_students"
MANAGE_TEACHERS = "manage_teachers"
MANAGE_CLASSES = "manage_classes"
MANAGE_SUBJECTS = "manage_subjects"
MANAGE_SCHEDULE = "manage_schedule"
MANAGE_SCHOOL_SETTINGS = "manage_school_settings"
SEND_ANNOUNCEMENTS = "send_announcements"
MANAGE_HELPDESK = "manage_helpdesk"
MODERATE_CHAT = "moderate_chat"
MARK_TEACHER_ATTENDANCE = "mark_teacher_attendance"


@dataclass(frozen=True)
class PermissionInfo:
    codename: str
    category: str
    description: str


_CATALOG_ROWS = [
    # -- own --
    (VIEW_OWN_PROFILE, "own", "O'z profilini ko'rish"),
    (UPDATE_OWN_PROFILE, "own", "O'z profilini tahrirlash (faqat alohida ruxsat bilan)"),
    (VIEW_OWN_CLASS, "own", "O'z sinfini ko'rish"),
    (VIEW_OWN_TEACHERS, "own", "O'z o'qituvchilarini ko'rish"),
    (VIEW_OWN_SUBJECTS, "own", "O'z fanlarini ko'rish"),
    (VIEW_OWN_GRADES, "own", "O'z baholarini ko'rish"),
    (VIEW_OWN_ATTENDANCE, "own", "O'z davomatini ko'rish"),
    (VIEW_OWN_HOMEWORK, "own", "O'z uy vazifalarini ko'rish"),
    (VIEW_OWN_QUIZZES, "own", "O'z testlarini ko'rish"),
    (VIEW_OWN_SCHEDULE, "own", "O'z dars jadvalini ko'rish"),
    (VIEW_CLASSMATES, "own", "Sinfdoshlar ro'yxatini ko'rish"),
    (SUBMIT_HOMEWORK, "own", "Uy vazifasini topshirish"),
    (TAKE_QUIZ, "own", "Test topshirish"),
    (USE_AI_ASSISTANT, "own", "AI yordamchidan foydalanish"),
    (VIEW_ANNOUNCEMENTS, "own", "E'lonlarni ko'rish"),
    (USE_CHAT, "own", "Chatdan foydalanish"),
    (CREATE_PRIVATE_CHAT, "own", "Shaxsiy chat ochish"),
    (VIEW_LIBRARY, "own", "Kutubxonani ko'rish"),
    # -- child --
    (VIEW_CHILD_PROFILE, "child", "Farzand profilini ko'rish"),
    (UPDATE_CHILD_PROFILE, "child", "Farzand asosiy ma'lumotlarini tahrirlash"),
    (VIEW_CHILD_CLASS, "child", "Farzand sinfini ko'rish"),
    (VIEW_CHILD_TEACHERS, "child", "Farzand o'qituvchilarini ko'rish"),
    (VIEW_CHILD_GRADES, "child", "Farzand baholarini ko'rish"),
    (VIEW_CHILD_ATTENDANCE, "child", "Farzand davomatini ko'rish"),
    (VIEW_CHILD_HOMEWORK, "child", "Farzand uy vazifalarini ko'rish"),
    (VIEW_CHILD_QUIZZES, "child", "Farzand testlarini ko'rish"),
    (VIEW_CHILD_SCHEDULE, "child", "Farzand dars jadvalini ko'rish"),
    (SUBMIT_ABSENCE_REASON, "child", "Farzand kelmagan sababini yuborish"),
    # -- teacher --
    (VIEW_ASSIGNED_STUDENTS, "teacher", "O'ziga biriktirilgan o'quvchilarni ko'rish"),
    (VIEW_ASSIGNED_CLASSES, "teacher", "O'ziga biriktirilgan sinflarni ko'rish"),
    (VIEW_ASSIGNED_GRADES, "teacher", "O'zi qo'ygan baholarni ko'rish"),
    (VIEW_ASSIGNED_ATTENDANCE, "teacher", "O'zi belgilagan davomatni ko'rish"),
    (VIEW_ASSIGNED_HOMEWORK, "teacher", "O'zi bergan uy vazifalarini ko'rish"),
    (VIEW_ASSIGNED_QUIZZES, "teacher", "O'zi yaratgan testlarni ko'rish"),
    (VIEW_OWN_TEACHER_ATTENDANCE, "teacher", "O'z ish davomatini ko'rish"),
    (CREATE_GRADE, "teacher", "Baho qo'yish"),
    (UPDATE_GRADE, "teacher", "Baho tahrirlash"),
    (DELETE_GRADE, "teacher", "Baho o'chirish"),
    (CREATE_HOMEWORK, "teacher", "Uy vazifasi yaratish"),
    (UPDATE_HOMEWORK, "teacher", "Uy vazifasini tahrirlash"),
    (DELETE_HOMEWORK, "teacher", "Uy vazifasini o'chirish"),
    (GRADE_SUBMISSIONS, "teacher", "Topshirilgan vazifalarni baholash"),
    (MARK_ATTENDANCE, "teacher", "Davomat belgilash"),
    (UPDATE_ATTENDANCE, "teacher", "Davomatni tahrirlash"),
    (MANAGE_QUIZZES, "teacher", "Testlarni boshqarish"),
    (MANAGE_LIBRARY, "teacher", "Kutubxona materiallarini boshqarish"),
    (CREATE_CHAT_ROOMS, "teacher", "Chat xonalari yaratish"),
    (TRANSFER_STUDENTS, "teacher", "O'quvchini boshqa sinfga o'tkazish"),
    # -- class teacher --
    (VIEW_CLASS_STUDENTS, "class_teacher", "O'z sinfi o'quvchilarini ko'rish"),
    (VIEW_CLASS_TEACHERS, "class_teacher", "O'z sinfi o'qituvchilarini ko'rish"),
    (VIEW_CLASS_REPORTS, "class_teacher", "O'z sinfi hisobotlarini ko'rish"),
    (MANAGE_CLASS_STUDENTS, "class_teacher", "O'z sinfi o'quvchilari ma'lumotlarini tahrirlash"),
    (MANAGE_CLASS_ATTENDANCE, "class_teacher", "O'z sinfi davomatini boshqarish"),
    (MANAGE_CLASS_HOMEWORK, "class_teacher", "O'z sinfi uy vazifalarini boshqarish"),
    (SEND_CLASS_ANNOUNCEMENT, "class_teacher", "O'z sinfiga e'lon yuborish"),
    (MANAGE_CLASS_PARENTS, "class_teacher", "O'z sinfi ota-ona bog'lanishlarini boshqarish"),
    # -- school-wide --
    (VIEW_ALL_STUDENTS, "school", "Barcha o'quvchilarni ko'rish"),
    (VIEW_ALL_TEACHERS, "school", "Barcha o'qituvchilarni ko'rish"),
    (VIEW_ALL_PARENTS, "school", "Barcha ota-onalarni ko'rish"),
    (VIEW_ALL_CLASSES, "school", "Barcha sinflarni ko'rish"),
    (VIEW_ALL_SUBJECTS, "school", "Barcha fanlarni ko'rish"),
    (VIEW_ALL_GRADES, "school", "Barcha baholarni ko'rish"),
    (VIEW_ALL_ATTENDANCE, "school", "Barcha davomatni ko'rish"),
    (VIEW_ALL_HOMEWORK, "school", "Barcha uy vazifalarini ko'rish"),
    (VIEW_ALL_QUIZZES, "school", "Barcha testlarni ko'rish"),
    (VIEW_ALL_SCHEDULE, "school", "Butun maktab dars jadvalini ko'rish"),
    (VIEW_ALL_ANNOUNCEMENTS, "school", "Barcha e'lonlarni ko'rish"),
    (VIEW_REPORTS, "school", "O'quv hisobotlarini ko'rish"),
    (VIEW_SENSITIVE_STUDENT_DATA, "school", "Maxfiy o'quvchi ma'lumotlarini (pasport, sog'liq) ko'rish"),
    # -- management --
    (MANAGE_USERS, "management", "Foydalanuvchilarni boshqarish"),
    (MANAGE_ROLES, "management", "Rollarni berish va olib tashlash"),
    (MANAGE_PERMISSIONS, "management", "Ruxsatlarni boshqarish"),
    (MANAGE_STUDENTS, "management", "O'quvchilarni yaratish, tahrirlash, o'chirish"),
    (MANAGE_TEACHERS, "management", "O'qituvchilarni boshqarish"),
    (MANAGE_CLASSES, "management", "Sinflarni boshqarish"),
    (MANAGE_SUBJECTS, "management", "Fanlarni boshqarish"),
    (MANAGE_SCHEDULE, "management", "Dars jadvalini boshqarish"),
    (MANAGE_SCHOOL_SETTINGS, "management", "Maktab sozlamalarini boshqarish"),
    (SEND_ANNOUNCEMENTS, "management", "Butun maktabga e'lon yuborish"),
    (MANAGE_HELPDESK, "management", "Yordam murojaatlarini boshqarish"),
    (MODERATE_CHAT, "management", "Chatlarni nazorat qilish"),
    (MARK_TEACHER_ATTENDANCE, "management", "O'qituvchilar ish davomatini belgilash"),
]

PERMISSIONS: dict[str, PermissionInfo] = {
    code: PermissionInfo(code, category, description) for code, category, description in _CATALOG_ROWS
}

# ---------------------------------------------------------------------------
# Role -> default permissions
# ---------------------------------------------------------------------------
_EVERYONE = {VIEW_OWN_PROFILE, VIEW_ANNOUNCEMENTS, USE_CHAT, VIEW_LIBRARY}

_STUDENT = _EVERYONE | {
    VIEW_OWN_CLASS,
    VIEW_OWN_TEACHERS,
    VIEW_OWN_SUBJECTS,
    VIEW_OWN_GRADES,
    VIEW_OWN_ATTENDANCE,
    VIEW_OWN_HOMEWORK,
    VIEW_OWN_QUIZZES,
    VIEW_OWN_SCHEDULE,
    VIEW_CLASSMATES,
    SUBMIT_HOMEWORK,
    TAKE_QUIZ,
    USE_AI_ASSISTANT,
    CREATE_PRIVATE_CHAT,
}

_PARENT = _EVERYONE | {
    VIEW_CHILD_PROFILE,
    UPDATE_CHILD_PROFILE,
    VIEW_CHILD_CLASS,
    VIEW_CHILD_TEACHERS,
    VIEW_CHILD_GRADES,
    VIEW_CHILD_ATTENDANCE,
    VIEW_CHILD_HOMEWORK,
    VIEW_CHILD_QUIZZES,
    VIEW_CHILD_SCHEDULE,
    SUBMIT_ABSENCE_REASON,
}

_TEACHER = _EVERYONE | {
    VIEW_ASSIGNED_STUDENTS,
    VIEW_ASSIGNED_CLASSES,
    VIEW_ASSIGNED_GRADES,
    VIEW_ASSIGNED_ATTENDANCE,
    VIEW_ASSIGNED_HOMEWORK,
    VIEW_ASSIGNED_QUIZZES,
    VIEW_OWN_SUBJECTS,
    VIEW_OWN_SCHEDULE,
    VIEW_OWN_TEACHER_ATTENDANCE,
    VIEW_ALL_SUBJECTS,  # the subject catalogue is a lookup table teachers need for forms
    CREATE_GRADE,
    UPDATE_GRADE,
    DELETE_GRADE,
    CREATE_HOMEWORK,
    UPDATE_HOMEWORK,
    DELETE_HOMEWORK,
    GRADE_SUBMISSIONS,
    MARK_ATTENDANCE,
    UPDATE_ATTENDANCE,
    MANAGE_QUIZZES,
    MANAGE_LIBRARY,
    CREATE_CHAT_ROOMS,
}

_CLASS_TEACHER = {
    VIEW_CLASS_STUDENTS,
    VIEW_CLASS_TEACHERS,
    VIEW_CLASS_REPORTS,
    MANAGE_CLASS_STUDENTS,
    MANAGE_CLASS_ATTENDANCE,
    MANAGE_CLASS_HOMEWORK,
    SEND_CLASS_ANNOUNCEMENT,
    TRANSFER_STUDENTS,
}

# Deputy director and director supervise the whole school: read everything academic,
# work with the timetable — but hold *no* technical/user/role/permission management.
_SUPERVISION = _EVERYONE | {
    VIEW_ALL_STUDENTS,
    VIEW_ALL_TEACHERS,
    VIEW_ALL_CLASSES,
    VIEW_ALL_SUBJECTS,
    VIEW_ALL_GRADES,
    VIEW_ALL_ATTENDANCE,
    VIEW_ALL_HOMEWORK,
    VIEW_ALL_QUIZZES,
    VIEW_ALL_SCHEDULE,
    VIEW_ALL_ANNOUNCEMENTS,
    VIEW_REPORTS,
    MANAGE_SCHEDULE,
}
_DEPUTY_DIRECTOR = _SUPERVISION
_DIRECTOR = _SUPERVISION | {TRANSFER_STUDENTS}

# Admin keeps everything it could already do before this permission system existed
# (grades / attendance / homework overrides inside its own school) plus user & role admin.
_ADMIN = (
    _SUPERVISION
    | {
        VIEW_ALL_PARENTS,
        VIEW_SENSITIVE_STUDENT_DATA,
        MANAGE_USERS,
        MANAGE_ROLES,
        MANAGE_PERMISSIONS,
        MANAGE_STUDENTS,
        MANAGE_TEACHERS,
        MANAGE_CLASSES,
        MANAGE_SUBJECTS,
        MANAGE_SCHOOL_SETTINGS,
        SEND_ANNOUNCEMENTS,
        MANAGE_HELPDESK,
        MODERATE_CHAT,
        MARK_TEACHER_ATTENDANCE,
        TRANSFER_STUDENTS,
        CREATE_CHAT_ROOMS,
        # inherited operational powers (school-scoped in access.py)
        CREATE_GRADE,
        UPDATE_GRADE,
        DELETE_GRADE,
        CREATE_HOMEWORK,
        UPDATE_HOMEWORK,
        DELETE_HOMEWORK,
        GRADE_SUBMISSIONS,
        MARK_ATTENDANCE,
        UPDATE_ATTENDANCE,
        MANAGE_QUIZZES,
        MANAGE_LIBRARY,
    }
)

# Superadmin is an *oversight* role, not an operational one: it administers the system
# across all schools and can read grades, but deliberately has no place in attendance,
# homework, quizzes or grade writing, and cannot upload library material.
_SUPERADMIN = (
    _EVERYONE
    | {
        VIEW_ALL_STUDENTS,
        VIEW_ALL_TEACHERS,
        VIEW_ALL_PARENTS,
        VIEW_ALL_CLASSES,
        VIEW_ALL_SUBJECTS,
        VIEW_ALL_GRADES,
        VIEW_ALL_SCHEDULE,
        VIEW_ALL_ANNOUNCEMENTS,
        VIEW_REPORTS,
        VIEW_SENSITIVE_STUDENT_DATA,
        MANAGE_USERS,
        MANAGE_ROLES,
        MANAGE_PERMISSIONS,
        MANAGE_STUDENTS,
        MANAGE_TEACHERS,
        MANAGE_CLASSES,
        MANAGE_SUBJECTS,
        MANAGE_SCHEDULE,
        MANAGE_SCHOOL_SETTINGS,
        SEND_ANNOUNCEMENTS,
        MANAGE_HELPDESK,
        MODERATE_CHAT,
        TRANSFER_STUDENTS,
        CREATE_CHAT_ROOMS,
    }
)
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    SUPERADMIN: frozenset(_SUPERADMIN),
    ADMIN: frozenset(_ADMIN),
    DIRECTOR: frozenset(_DIRECTOR),
    DEPUTY_DIRECTOR: frozenset(_DEPUTY_DIRECTOR),
    TEACHER: frozenset(_TEACHER),
    CLASS_TEACHER: frozenset(_CLASS_TEACHER),
    STUDENT: frozenset(_STUDENT),
    PARENT: frozenset(_PARENT),
}

_unknown = {p for perms in ROLE_PERMISSIONS.values() for p in perms} - set(PERMISSIONS)
assert not _unknown, f"role grants permissions missing from the catalogue: {sorted(_unknown)}"

# Roles whose data is confined to one school. SUPERADMIN alone is global.
GLOBAL_ROLES = frozenset({SUPERADMIN})


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------
_CACHE_ATTR = "_rbac_cache"


@dataclass(frozen=True)
class Access:
    """Everything the RBAC layer knows about one user, computed once per user instance."""

    roles: frozenset[str]
    permissions: frozenset[str]
    extra_permissions: frozenset[str]  # per-user grants only (subset of ``permissions``)


_ANONYMOUS = Access(frozenset(), frozenset(), frozenset())


def _is_authenticated(user) -> bool:
    return bool(user is not None and getattr(user, "is_authenticated", False))


def _compute_access(user) -> Access:
    from django.apps import apps

    roles: set[str] = set()
    primary = getattr(user, "role", None)
    if primary in STORED_ROLES:
        roles.add(primary)
    roles.update(user.groups.filter(name__in=STORED_ROLES).values_list("name", flat=True))

    # Class teacher is derived from the existing ClassRoom.curator relation.
    ClassRoom = apps.get_model("classes", "ClassRoom")
    if ClassRoom.objects.filter(curator__user_id=user.pk).exists():
        roles.add(CLASS_TEACHER)

    permissions: set[str] = set()
    for role in roles:
        permissions |= ROLE_PERMISSIONS[role]

    extra = set(
        user.user_permissions.filter(
            content_type__app_label="users", content_type__model="user", codename__in=PERMISSIONS
        ).values_list("codename", flat=True)
    )
    permissions |= extra
    return Access(frozenset(roles), frozenset(permissions), frozenset(extra))


def access_for(user) -> Access:
    """Roles + permissions of ``user`` (cached on the instance — a request builds a fresh
    user object per request, so this is effectively a per-request cache)."""
    if not _is_authenticated(user):
        return _ANONYMOUS
    cached = getattr(user, _CACHE_ATTR, None)
    if cached is None:
        cached = _compute_access(user)
        setattr(user, _CACHE_ATTR, cached)
    return cached


def invalidate(user) -> None:
    """Forget the cached access (call after changing a user's roles / permissions)."""
    if hasattr(user, _CACHE_ATTR):
        delattr(user, _CACHE_ATTR)


def effective_roles(user) -> frozenset[str]:
    return access_for(user).roles


def user_permissions(user) -> frozenset[str]:
    return access_for(user).permissions


def has_role(user, *roles: str) -> bool:
    return bool(access_for(user).roles.intersection(roles))


def has_perm(user, codename: str) -> bool:
    return codename in access_for(user).permissions


def has_any_perm(user, *codenames: str) -> bool:
    perms = access_for(user).permissions
    return any(code in perms for code in codenames)


def has_all_perms(user, *codenames: str) -> bool:
    perms = access_for(user).permissions
    return all(code in perms for code in codenames)


def is_global(user) -> bool:
    """True only for roles that are not confined to a single school (SUPERADMIN)."""
    return bool(access_for(user).roles & GLOBAL_ROLES)


def get_permission_row(codename: str):
    """The ``auth.Permission`` row for ``codename`` (created on first use)."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    from apps.users.models import User

    info = PERMISSIONS[codename]
    content_type = ContentType.objects.get_for_model(User)
    permission, _created = Permission.objects.get_or_create(
        content_type=content_type, codename=codename, defaults={"name": info.description[:255]}
    )
    return permission


def get_role_group(role: str):
    """The ``Group`` that stores membership of ``role`` (created on first use)."""
    from django.contrib.auth.models import Group

    group, _created = Group.objects.get_or_create(name=role)
    return group
