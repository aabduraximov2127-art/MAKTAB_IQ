from celery import shared_task

from common.realtime import push_notification_to_user
from common.telegram import send_telegram_message

from .models import Notification, NotificationType


def _deliver(user, title, message, notif_type):
    notification = Notification.objects.create(user=user, title=title, message=message, type=notif_type)
    push_notification_to_user(
        user.id,
        {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "created_at": notification.created_at.isoformat(),
        },
    )
    if user.telegram_chat_id:
        send_telegram_message_task.delay(user.telegram_chat_id, f"{title}\n\n{message}")
    return notification


@shared_task
def send_telegram_message_task(chat_id, text):
    return send_telegram_message(chat_id, text)


@shared_task
def notify_student_absence(attendance_id):
    from apps.attendance.models import Attendance

    try:
        attendance = Attendance.objects.select_related("student__user").get(pk=attendance_id)
    except Attendance.DoesNotExist:
        return

    student = attendance.student
    title = "Farzandingiz maktabda yo'q"
    message = f"{student.user.get_full_name()} {attendance.date} kuni darsga kelmadi."

    for link in student.parent_links.select_related("parent__user"):
        _deliver(link.parent.user, title, message, NotificationType.ABSENT)


@shared_task
def notify_teacher_absence(attendance_id):
    from apps.attendance.models import TeacherAttendance

    try:
        attendance = TeacherAttendance.objects.select_related("teacher__user").get(pk=attendance_id)
    except TeacherAttendance.DoesNotExist:
        return

    title = "Davomat: kelmagansiz"
    message = f"Nega bugun ({attendance.date}) ishda emassiz? Iltimos, ma'muriyat bilan bog'laning."
    _deliver(attendance.teacher.user, title, message, NotificationType.ABSENT)


@shared_task
def notify_new_grade(grade_id):
    from apps.grades.models import Grade

    try:
        grade = Grade.objects.select_related("student__user", "subject").get(pk=grade_id)
    except Grade.DoesNotExist:
        return

    title = "Yangi baho"
    message = f"{grade.subject.name} fanidan {grade.value} baho qo'yildi."
    _deliver(grade.student.user, title, message, NotificationType.GRADE)
    for link in grade.student.parent_links.select_related("parent__user"):
        _deliver(link.parent.user, title, message, NotificationType.GRADE)


@shared_task
def notify_homework_created(assignment_id):
    from apps.assignments.models import Assignment

    try:
        assignment = Assignment.objects.select_related("lesson__class_room").get(pk=assignment_id)
    except Assignment.DoesNotExist:
        return

    title = "Yangi uy vazifa"
    message = f"{assignment.title} — muddat: {assignment.deadline}"
    for student in assignment.lesson.class_room.students.select_related("user"):
        _deliver(student.user, title, message, NotificationType.HOMEWORK)


@shared_task
def broadcast_announcement(announcement_id):
    from apps.notifications.models import Announcement

    try:
        announcement = Announcement.objects.get(pk=announcement_id)
    except Announcement.DoesNotExist:
        return

    from apps.users.models import User

    qs = User.objects.filter(is_active=True)
    if announcement.target == Announcement.Target.TEACHERS:
        qs = qs.filter(role=User.Role.TEACHER)
    elif announcement.target == Announcement.Target.STUDENTS:
        qs = qs.filter(role=User.Role.STUDENT)
    elif announcement.target == Announcement.Target.PARENTS:
        qs = qs.filter(role=User.Role.PARENT)
    elif announcement.target == Announcement.Target.CLASS and announcement.target_class_id:
        qs = qs.filter(student_profile__class_room_id=announcement.target_class_id)

    for user in qs:
        _deliver(user, announcement.title, announcement.content, NotificationType.ANNOUNCEMENT)


@shared_task
def broadcast_emergency(emergency_id):
    from apps.notifications.models import EmergencyAnnouncement
    from apps.users.models import User

    try:
        emergency = EmergencyAnnouncement.objects.get(pk=emergency_id)
    except EmergencyAnnouncement.DoesNotExist:
        return

    for user in User.objects.filter(is_active=True):
        _deliver(user, emergency.title, emergency.content, NotificationType.EMERGENCY)


@shared_task
def send_weekly_parent_reports():
    from apps.users.models import ParentStudent

    for link in ParentStudent.objects.select_related("parent__user", "student__user"):
        from apps.analytics.services import compute_student_progress

        progress = compute_student_progress(link.student)
        title = f"Haftalik hisobot: {link.student.user.get_full_name()}"
        message = (
            f"Davomat: {progress['attendance_percentage']}%\n"
            f"O'rtacha baho: {progress['average_grade']}\n"
            f"Uy vazifa: {progress['homework_completion']}"
        )
        _deliver(link.parent.user, title, message, NotificationType.ANNOUNCEMENT)


ROLE_LABELS_UZ = {
    "SUPERADMIN": "Superadmin",
    "ADMIN": "Admin",
    "TEACHER": "O'qituvchi",
    "STUDENT": "O'quvchi",
    "PARENT": "Ota-ona",
}


def _class_of(user):
    profile = getattr(user, "student_profile", None)
    return getattr(profile, "class_room", None)


def _moderation_recipients(incident):
    """Teachers (and, as a fallback, school admins) who must hear about a flagged message.

    - the class curator of the offending student (and of any student they wrote to),
    - every teacher who is a member of that chat room,
    - school admins when the sender is not a student, or nobody else could be found.
    """
    from apps.users.models import User

    sender = incident.sender
    members = [m.user for m in incident.chat_room.members.select_related("user")]
    others = [u for u in members if u.id != sender.id]

    recipients = {}

    def add(user):
        if user is not None and user.id != sender.id and user.is_active:
            recipients[user.id] = user

    sender_class = _class_of(sender)
    if sender_class and sender_class.curator_id:
        add(sender_class.curator.user)
    for other in others:
        if other.role == User.Role.TEACHER:
            add(other)
        elif other.role == User.Role.STUDENT:
            other_class = _class_of(other)
            if other_class and other_class.curator_id:
                add(other_class.curator.user)

    if sender.role != User.Role.STUDENT or not recipients:
        admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
        if sender.school_id:
            admins = admins.filter(school_id=sender.school_id)
        for admin in admins:
            add(admin)
    return list(recipients.values())


def _describe_targets(incident):
    from apps.chat.models import ChatRoom

    room = incident.chat_room
    if room.room_type == ChatRoom.RoomType.CLASS_GENERAL:
        return f"Sinf chati ({room.name or room.class_room})"
    names = [
        m.user.get_full_name() or m.user.username
        for m in room.members.select_related("user")
        if m.user_id != incident.sender_id
    ]
    return ", ".join(names[:5]) or (room.name or "Shaxsiy chat")


@shared_task
def notify_profanity_incident(incident_id):
    from django.utils import timezone

    from apps.chat.models import ModerationIncident

    try:
        incident = ModerationIncident.objects.select_related("sender", "chat_room", "message").get(pk=incident_id)
    except ModerationIncident.DoesNotExist:
        return
    sender = incident.sender
    if sender is None:
        return

    sender_class = _class_of(sender)
    who = sender.get_full_name() or sender.username
    who_extra = ROLE_LABELS_UZ.get(sender.role, sender.role)
    if sender_class:
        who_extra = f"{sender_class.name}, {who_extra}"

    when = timezone.localtime(incident.created_at).strftime("%d.%m.%Y %H:%M")
    text = incident.message.text
    if len(text) > 500:
        text = text[:500] + "…"

    title = "⚠️ Chatda so'kinish / haqorat aniqlandi"
    body = (
        f"Kim yozdi: {who} ({who_extra})\n"
        f"Kimga: {_describe_targets(incident)}\n"
        f"Xabar: «{text}»\n"
        f"Vaqt: {when}"
    )

    recipients = _moderation_recipients(incident)
    for user in recipients:
        _deliver(user, title, body, NotificationType.CHAT_MESSAGE)
    incident.notified.set(recipients)
