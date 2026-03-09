from __future__ import annotations

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.notifications.context_processors import topbar_notifications
from apps.notifications.models import Notification


class NotificationViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username="notif_student",
            email="notif_student@cbt.test",
            password="StudentPass123!",
            role="student",
            is_active=True,
        )
        cls.other_user = User.objects.create_user(
            username="notif_other",
            email="notif_other@cbt.test",
            password="OtherPass123!",
            role="student",
            is_active=True,
        )

        cls.unread_notification = Notification.objects.create(
            user=cls.student,
            title="Notif 1",
            message="Pesan notif belum dibaca",
            notification_type=Notification.Type.INFO,
            is_read=False,
        )
        cls.read_notification = Notification.objects.create(
            user=cls.student,
            title="Notif 2",
            message="Pesan notif sudah dibaca",
            notification_type=Notification.Type.SUCCESS,
            is_read=True,
            read_at=timezone.now(),
        )
        cls.other_notification = Notification.objects.create(
            user=cls.other_user,
            title="Notif user lain",
            message="Tidak boleh tampil",
            notification_type=Notification.Type.WARNING,
            is_read=False,
        )

    def test_notification_list_requires_login(self):
        response = self.client.get(reverse("notification_list"))
        self.assertEqual(response.status_code, 302)

    def test_notification_list_shows_only_current_user(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("notification_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notif 1")
        self.assertContains(response, "Notif 2")
        self.assertNotContains(response, "Notif user lain")

    def test_notification_list_unread_filter(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("notification_list"), {"status": "unread"})
        self.assertEqual(response.status_code, 200)
        objects = list(response.context["notifications"])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].id, self.unread_notification.id)

    def test_mark_all_read_marks_only_current_user_notifications(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("notification_mark_all_read"),
            {"next": reverse("notification_list")},
        )
        self.assertEqual(response.status_code, 302)

        self.unread_notification.refresh_from_db()
        self.other_notification.refresh_from_db()
        self.assertTrue(self.unread_notification.is_read)
        self.assertIsNotNone(self.unread_notification.read_at)
        self.assertFalse(self.other_notification.is_read)

    def test_mark_single_read_marks_owned_notification(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("notification_mark_read", kwargs={"notification_id": self.unread_notification.id}),
            {"next": reverse("notification_list")},
        )
        self.assertEqual(response.status_code, 302)
        self.unread_notification.refresh_from_db()
        self.assertTrue(self.unread_notification.is_read)
        self.assertIsNotNone(self.unread_notification.read_at)

    def test_mark_single_read_does_not_touch_other_user_notification(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("notification_mark_read", kwargs={"notification_id": self.other_notification.id}),
            {"next": reverse("notification_list")},
        )
        self.assertEqual(response.status_code, 302)
        self.other_notification.refresh_from_db()
        self.assertFalse(self.other_notification.is_read)


class TopbarNotificationsContextProcessorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="notif_cp_user",
            email="notif_cp_user@cbt.test",
            password="NotifPass123!",
            role="teacher",
            is_active=True,
        )
        for idx in range(8):
            Notification.objects.create(
                user=cls.user,
                title=f"Notif CP {idx}",
                message="Pesan context processor",
                notification_type=Notification.Type.INFO,
                is_read=idx >= 3,
                read_at=timezone.now() if idx >= 3 else None,
            )

    def test_context_processor_returns_limited_recent_notifications(self):
        request = RequestFactory().get("/")
        request.user = self.user

        payload = topbar_notifications(request)
        self.assertEqual(payload["topbar_notification_unread_count"], 3)
        self.assertEqual(len(payload["topbar_notifications"]), 6)

    def test_context_processor_handles_anonymous_user(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        payload = topbar_notifications(request)
        self.assertEqual(payload["topbar_notification_unread_count"], 0)
        self.assertEqual(payload["topbar_notifications"], [])
