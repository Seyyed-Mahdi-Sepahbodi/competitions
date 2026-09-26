from datetime import timedelta, date
import json
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from forms.models import Form, Field, Response, ResponseData
from forms.forms import DynamicForm

@override_settings(MEDIA_ROOT="/tmp/test_media_dynamicform")
class DynamicFormCleanAndSaveTestSample(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.form = Form.objects.create(title="Test Form", created_by=self.user)

        # Representative field set
        self.text_field = Field.objects.create(
            form=self.form, label="Name", field_type="text", is_required=True, min_length=3, max_length=10
        )
        self.email_field = Field.objects.create(
            form=self.form, label="Email", field_type="email", is_required=True
        )
        self.checkbox_field = Field.objects.create(
            form=self.form, label="Choices", field_type="checkbox", options=["A", "B", "C"]
        )
        self.file_field = Field.objects.create(
            form=self.form, label="Upload", field_type="file", is_required=False
        )
        self.number_field = Field.objects.create(
            form=self.form, label="Age", field_type="number", min_value=18, max_value=99
        )
        self.url_field = Field.objects.create(
            form=self.form, label="Website", field_type="url"
        )
        self.phone_field = Field.objects.create(
            form=self.form, label="Phone", field_type="phone"
        )
        self.date_field = Field.objects.create(
            form=self.form, label="DOB", field_type="date"
        )

    def test_forms_1(self):
        data = {
            f'field_{self.text_field.id}': "Johnny",
            f'field_{self.email_field.id}': "john@example.com",
            f'field_{self.checkbox_field.id}': ["A", "C"],
            f'field_{self.number_field.id}': "28",
            f'field_{self.url_field.id}': "https://example.com",
            f'field_{self.phone_field.id}': "+12345678901",
            f'field_{self.date_field.id}': date.today().isoformat(),
        }
        form = DynamicForm(self.form, data)
        self.assertTrue(form.is_valid())
        cleaned = form.clean()
        # spot-check a few cleaned keys exist
        for fid in (self.text_field.id, self.email_field.id, self.checkbox_field.id):
            self.assertIn(f'field_{fid}', cleaned)

    def test_forms_2(self):
        data = {
            f'field_{self.text_field.id}': "Jo",  # too short
            f'field_{self.email_field.id}': "not-an-email",
            f'field_{self.checkbox_field.id}': ["Z"],  # invalid option
            f'field_{self.number_field.id}': "10",     # too small
            f'field_{self.url_field.id}': "not-a-url",
            f'field_{self.phone_field.id}': "123",
        }
        form = DynamicForm(self.form, data)
        self.assertFalse(form.is_valid())
        errors = form.errors
        for fid in (self.text_field.id, self.email_field.id, self.checkbox_field.id,
                    self.number_field.id, self.url_field.id, self.phone_field.id):
            self.assertIn(f'field_{fid}', errors)
