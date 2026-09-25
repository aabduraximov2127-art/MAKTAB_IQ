"""Class-teacher attendance: an excused absence carries a reason category ("kasal", "oilaviy",
...), an unexcused one carries none, and correcting a mark to ABSENT notifies the parents."""

from unittest import mock

from apps.users.test_rbac import SchoolWorld

from .models import Attendance


class AbsenceReasonTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.t1_user)  # t1 is the curator of 9-A

    def mark(self, student, **extra):
        body = {"student": student.id, "class_room": self.class_a.id, "date": "2026-09-16", **extra}
        return self.client.post("/api/v1/attendance/", body)

    def test_excused_absence_stores_the_reason_category(self):
        response = self.mark(self.s1, status="EXCUSED", absence_reason="SICK")
        self.assertEqual(response.status_code, 201)
        self.assertEqual((response.data["status"], response.data["absence_reason"]), ("EXCUSED", "SICK"))

    def test_every_reason_category_is_accepted(self):
        for index, reason in enumerate(["SICK", "FAMILY", "COMPETITION", "OTHER"]):
            with self.subTest(reason=reason):
                body = {"student": self.s2.id, "class_room": self.class_a.id, "date": f"2026-10-0{index + 1}"}
                response = self.client.post("/api/v1/attendance/", dict(body, status="EXCUSED", absence_reason=reason))
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.data["absence_reason"], reason)

    def test_unexcused_absence_and_other_statuses_carry_no_reason(self):
        absent = self.mark(self.s1, status="ABSENT", absence_reason="SICK")  # "sababsiz" wins over a stray reason
        self.assertEqual(absent.data["absence_reason"], "")
        late = self.mark(self.s2, status="LATE", absence_reason="FAMILY")
        self.assertEqual(late.data["absence_reason"], "")

    def test_changing_an_excused_mark_to_present_clears_the_reason(self):
        created = self.mark(self.s1, status="EXCUSED", absence_reason="FAMILY").data
        fixed = self.client.patch(f"/api/v1/attendance/{created['id']}/", {"status": "PRESENT"})
        self.assertEqual(fixed.status_code, 200)
        self.assertEqual(Attendance.objects.get(pk=created["id"]).absence_reason, "")

    def test_one_daily_mark_per_pupil_per_day(self):
        self.assertEqual(self.mark(self.s1, status="PRESENT").status_code, 201)
        again = self.mark(self.s1, status="ABSENT")
        self.assertEqual(again.status_code, 400)
        self.assertEqual(Attendance.objects.filter(student=self.s1, date="2026-09-16").count(), 1)

    def test_invalid_reason_is_rejected(self):
        self.assertEqual(self.mark(self.s1, status="EXCUSED", absence_reason="BORED").status_code, 400)

    def test_parents_are_told_when_a_mark_is_corrected_to_absent(self):
        created = self.mark(self.s1, status="PRESENT").data
        with mock.patch("apps.notifications.tasks.notify_student_absence.delay") as notify:
            self.client.patch(f"/api/v1/attendance/{created['id']}/", {"status": "ABSENT"})
            self.client.patch(f"/api/v1/attendance/{created['id']}/", {"status": "ABSENT"})  # unchanged: no repeat
        notify.assert_called_once_with(created["id"])

    def test_a_class_teacher_cannot_mark_another_class(self):
        body = {"student": self.s3.id, "class_room": self.class_b.id, "date": "2026-09-16", "status": "ABSENT"}
        self.assertEqual(self.client.post("/api/v1/attendance/", body).status_code, 403)
        # ...nor pretend a pupil of 9-B sits in 9-A
        body = {"student": self.s3.id, "class_room": self.class_a.id, "date": "2026-09-16", "status": "ABSENT"}
        self.assertEqual(self.client.post("/api/v1/attendance/", body).status_code, 403)

    def test_a_class_teacher_only_reads_their_own_class_attendance(self):
        rows = self.client.get("/api/v1/attendance/").data["results"]
        self.assertEqual({row["class_room"] for row in rows}, {self.class_a.id})
