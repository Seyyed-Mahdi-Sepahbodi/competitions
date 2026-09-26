from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from forms.models import Form, Field, Response

class FormSubmissionViewTestSample(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.form = Form.objects.create(title="Test Form", created_by=self.user, allow_multiple_submissions=False)
        self.field = Field.objects.create(form=self.form, label="Name", field_type="text", is_required=True, min_length=2, max_length=10)
        self.detail_url = reverse('form_detail', kwargs={'pk': self.form.pk})
        self.url = reverse('form_submit', kwargs={'pk': self.form.pk})

    def test_views_1(self):
        self.form.is_active = False; self.form.save()
        response = self.client.post(self.url, {})
        self.assertRedirects(response, self.detail_url)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('no longer accepting submissions' in str(m).lower() for m in messages))

    def test_views_2(self):
        self.form.submission_limit = 1; self.form.save()
        Response.objects.create(form=self.form)
        response = self.client.post(self.url, {})
        self.assertRedirects(response, self.detail_url)

    def test_views_3(self):
        self.client.login(username='testuser', password='pass')
        Response.objects.create(form=self.form, submitted_by=self.user)
        response = self.client.post(self.url, {})
        self.assertRedirects(response, self.detail_url)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('already submitted' in str(m).lower() for m in messages))
