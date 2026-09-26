from django.test import TestCase
from django.contrib.auth.models import User
from forms.models import Form, Field

class FieldModelTestSample(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='tester')
        self.form = Form.objects.create(title='Test Form', created_by=self.user)

    def test_model_field_1(self):
        for field_type, _ in Field.FIELD_TYPES:
            field = Field.objects.create(form=self.form, label=f'{field_type} field', field_type=field_type)
            self.assertEqual(field.field_type, field_type)
            self.assertEqual(str(field), f"{self.form.title} - {field.label}")

    def test_model_field_2(self):
        for field_type in ['select', 'radio', 'checkbox']:
            field = Field(form=self.form, label='Choice', field_type=field_type, options=[])
            with self.assertRaises(Exception):
                field.clean()
            field.options = ['A', 'B']
            field.clean()  # no raise

    def test_model_field_3(self):
        field = Field(form=self.form, label='Number', field_type='number', min_value=10, max_value=5)
        with self.assertRaises(Exception): field.clean()
        field.min_value, field.max_value = 5, 10
        field.clean()

        field = Field(form=self.form, label='Text', field_type='text', min_length=10, max_length=5)
        with self.assertRaises(Exception): field.clean()
        field.min_length, field.max_length = 5, 10
        field.clean()
