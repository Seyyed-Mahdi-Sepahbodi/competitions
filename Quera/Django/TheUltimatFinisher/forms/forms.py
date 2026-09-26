from django import forms
from django.db import models

import json
from datetime import timedelta

from forms.models import Form, Field, Response, ResponseData


class FormCreationForm(forms.ModelForm):    
    class Meta:
        model = Form
        fields = ['title', 'description', 'is_active', 'allow_multiple_submissions', 
                 'submission_limit', 'expires_at', 'success_message']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter form title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter form description (supports Markdown)'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'submission_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'success_message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        form = super().save(commit=False)
        if self.user:
            form.created_by = self.user
        if commit:
            form.save()
        return form


class FieldCreationForm(forms.ModelForm):
    
    options_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter options (one per line)'
        }),
        help_text='For select, radio, and checkbox fields. Enter one option per line.'
    )
    
    class Meta:
        model = Field
        fields = ['label', 'field_type', 'help_text', 'placeholder', 'is_required', 
                 'min_length', 'max_length', 'min_value', 'max_value', 
                 'regex_pattern', 'custom_error_message']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'field_type': forms.Select(attrs={'class': 'form-control'}),
            'help_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'placeholder': forms.TextInput(attrs={'class': 'form-control'}),
            'min_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'max_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'min_value': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'max_value': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'regex_pattern': forms.TextInput(attrs={'class': 'form-control'}),
            'custom_error_message': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.form_instance = kwargs.pop('form_instance', None)
        super().__init__(*args, **kwargs)
        
        if self.instance.pk and self.instance.options:
            self.fields['options_text'].initial = '\n'.join(self.instance.options)
    
    def clean_options_text(self):
        options = self.cleaned_data.get('options_text', '')
        if options:
            options = [opt.strip() for opt in options.split('\n') if opt.strip()]
            return options
        return []
    
    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')
        options_text = cleaned_data.get('options_text')
        
        if field_type in ['select', 'radio', 'checkbox']:
            if not options_text:
                self.add_error('options_text', "Choice fields must have at least one option.")
            else:
                self.instance.options = options_text
        
        return cleaned_data
    
    def save(self, commit=True):
        field = super().save(commit=False)
                
        if self.form_instance:
            field.form = self.form_instance
        
        if not field.order:
            max_order = Field.objects.filter(form=field.form).aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            field.order = max_order + 1
        
        if commit:
            field.save()

        return field


class DynamicForm(forms.Form):
    
    def __init__(self, form_instance, *args, **kwargs):
        self.form_instance = form_instance
        super().__init__(*args, **kwargs)
        
        for field in form_instance.fields.all():
            field_name = f'field_{field.id}'
            
            
            if field.field_type == 'text':
                form_field = forms.CharField(
                    max_length=field.max_length or 255,
                    min_length=field.min_length or None,
                    required=field.is_required
                )
            elif field.field_type == 'email':
                form_field = forms.EmailField(required=field.is_required)
            elif field.field_type == 'number':
                form_field = forms.FloatField(
                    min_value=field.min_value,
                    max_value=field.max_value,
                    required=field.is_required
                )
            elif field.field_type == 'textarea':
                form_field = forms.CharField(
                    widget=forms.Textarea(attrs={'rows': 4}),
                    max_length=field.max_length or 1000,
                    min_length=field.min_length or None,
                    required=field.is_required
                )
            elif field.field_type == 'select':
                choices = [(opt, opt) for opt in field.options]
                form_field = forms.ChoiceField(
                    choices=choices,
                    required=field.is_required
                )
            elif field.field_type == 'radio':
                choices = [(opt, opt) for opt in field.options]
                form_field = forms.ChoiceField(
                    choices=choices,
                    widget=forms.RadioSelect,
                    required=field.is_required
                )
            elif field.field_type == 'checkbox':
                choices = [(opt, opt) for opt in field.options]
                form_field = forms.MultipleChoiceField(
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple,
                    required=field.is_required
                )
            elif field.field_type == 'file':
                form_field = forms.FileField(required=field.is_required)

            elif field.field_type == 'date':
                form_field = forms.DateField(
                    widget=forms.DateInput(attrs={'type': 'date'}),
                    required=field.is_required
                )
            elif field.field_type == 'url':
                form_field = forms.URLField(required=field.is_required)

            elif field.field_type == 'phone':
                form_field = forms.CharField(
                    max_length=20,
                    required=field.is_required
                )
            else:
                form_field = forms.CharField(required=field.is_required)
            
            
            form_field.label = field.label
            form_field.help_text = field.help_text
            
            
            widget_attrs = {'class': 'form-control'}
            if field.placeholder:
                widget_attrs['placeholder'] = field.placeholder
            
            if hasattr(form_field.widget, 'attrs'):
                form_field.widget.attrs.update(widget_attrs)
            
            self.fields[field_name] = form_field
    
    def clean(self):
        pass

    def save(self, user=None, session_key=None, completion_time=None):
        pass