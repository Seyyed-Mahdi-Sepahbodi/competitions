from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from forms.models import Form, Response

class FormModelTestSample(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.form = Form.objects.create(
            title="Survey",
            description="A test survey",
            submission_limit=2,
            expires_at=timezone.now() + timedelta(days=1),
            created_by=self.user
        )

    def test_models_form_1(self):
        self.assertEqual(str(self.form), "Survey")
        self.assertTrue(self.form.is_active)

    def test_models_form_2(self):
        self.assertFalse(self.form.is_expired)
        self.form.expires_at = timezone.now() - timedelta(days=1)
        self.form.save()
        self.assertTrue(self.form.is_expired)

    def test_models_form_3(self):
        self.assertFalse(self.form.is_submission_limit_reached)
        for _ in range(2):
            Response.objects.create(form=self.form)
        self.assertTrue(self.form.is_submission_limit_reached)
