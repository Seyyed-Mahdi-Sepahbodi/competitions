from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

import re
import json


class Form(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    success_message = models.TextField(default="Thank you for your submission!")
    allow_multiple_submissions = models.BooleanField(default=False)
    submission_limit = models.PositiveIntegerField()
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_forms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_submission_limit_reached(self):
        if self.submission_limit:
            return self.get_response_count() >= self.submission_limit
        return False

    @property
    def can_accept_submissions(self):
        return self.is_active and not self.is_expired and not self.is_submission_limit_reached

    def get_response_count(self):
        if hasattr(self, "responses"):
            return self.responses.count()
        return self.response_set.count()

    def get_completion_rate(self):
        return self.get_response_count() /self.views.count() if self.views.count() > 0 else 0


class Field(models.Model):
    FIELD_TYPES = [
        ('text', 'Text'),
        ('email', 'Email'),
        ('number', 'Number'),
        ('textarea', 'Textarea'),
        ('select', 'Select'),
        ('radio', 'Radio'),
        ('checkbox', 'Checkbox'),
        ('file', 'File Upload'),
        ('date', 'Date'),
        ('url', 'URL'),
        ('phone', 'Phone'),
    ]

    CHOICE_TYPES = {'select', 'radio', 'checkbox'}

    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="fields")
    label = models.CharField(max_length=200)
    field_type = models.CharField(choices=FIELD_TYPES)
    help_text = models.TextField(null=True, blank=True)
    placeholder = models.CharField(null=True, blank=True)
    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    options = models.JSONField(default=list, null=True, blank=True)
    min_length = models.PositiveIntegerField(null=True, blank=True)
    max_length = models.PositiveIntegerField(null=True, blank=True)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    regex_pattern = models.CharField(null=True, blank=True)
    custom_error_message = models.CharField(null=True, blank=True)

    def __str__(self):
        return f"{self.form.title} - {self.label}"

    def clean(self):

        if self.field_type in self.CHOICE_TYPES:
            if not self.options or self.options == []:
                raise ValidationError("Choice fields must have at least one option.")
    
        if self.min_value and self.max_value:
            if self.min_value > self.max_value:
                raise ValidationError("Minimum value cannot be greater than maximum value.")

        if self.min_length and self.max_length:
            if self.min_length > self.max_length:
                raise ValidationError("Minimum length cannot be greater than maximum length.")

        if self.regex_pattern:
            try:
                re.compile(self.regex_pattern)
            except re.error:
                raise ValidationError("Invalid regex pattern.")

        super().clean()

    def validate_value(self, value):
        errors = []

        is_empty = value is None or value == "" or value == []

        if self.is_required and is_empty:
            return [f"{self.label} is required."]

        if (not self.is_required) and is_empty:
            return []

        if self.field_type == "email":
            pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.fullmatch(pattern, str(value)):
                errors.append("Please enter a valid email address.")

        elif self.field_type == "number":
            try:
                num = float(value)
            except (ValueError, TypeError):
                return ["Please enter a valid number."]

            if self.min_value is not None and num < self.min_value:
                return [f"Value must be at least {self.min_value}."]

            if self.max_value and self.max_value < num:
                return [f"Value must be at most {self.max_value}."]

        elif self.field_type == "url":
            pattern = r"^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$"
            if not re.fullmatch(pattern, str(value)):
                errors.append("Please enter a valid URL.")

        elif self.field_type == "phone":
            pattern = r"^\+?[1-9][0-9]{7,14}$"
            if not re.fullmatch(pattern, str(value)):
                errors.append("Please enter a valid phone number.")
        
        elif self.field_type in ("select", "radio"):
            opts = self.options or []
            if str(value) not in [str(opt) for opt in opts]:
                errors.append("Please select valid options.")

        elif self.field_type == "checkbox":
            if not isinstance(value, list):
                errors.append("Please select valid options.")   
            else:
                opts = {str(opt) for opt in (self.options or [])}
                for item in value:
                    if str(item) not in opts:
                        errors.append("Please select valid options.")
                        break

        if self.min_length and len(str(value)) < self.min_length:
            errors.append(f"Must be at least {self.min_length} characters long.")
        elif self.max_length and len(str(value)) > self.max_length:
            errors.append(f"Must be at most {self.max_length} characters long.")

        if self.regex_pattern:
            if not re.fullmatch(self.regex_pattern, str(value)):
                if self.custom_error_message:
                    errors.append(self.custom_error_message)
                else:
                    errors.append("Invalid format.")

        return errors


class Response(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='responses')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    completion_time = models.DurationField(null=True, blank=True, help_text="Time taken to complete the form")
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Response to {self.form.title} at {self.submitted_at}"

    def get_data_dict(self):
        
        data = {}
        for response_data in self.data.all():
            data[response_data.field.label] = response_data.value
        return data

    def get_completion_time_display(self):
        
        if not self.completion_time:
            return "Untracked"

        total_seconds = int(self.completion_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


class ResponseData(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='data')
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    value = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='uploads/', blank=True, null=True)
    
    class Meta:
        unique_together = ['response', 'field']
    
    def __str__(self):
        return f"{self.field.label}: {self.value[:50]}"

    def get_display_value(self):
        
        if self.field.field_type == 'checkbox':
            try:
                values = json.loads(self.value)
                return ', '.join(values) if isinstance(values, list) else self.value
            except (json.JSONDecodeError, TypeError):
                return self.value
        return self.value


class FormView(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='views')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    viewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    referrer = models.URLField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"View of {self.form.title} at {self.viewed_at}"
