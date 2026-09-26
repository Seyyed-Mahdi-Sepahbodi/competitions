from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

import re
import json


class Form(models.Model):
    pass


class Field(models.Model):
    pass


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
