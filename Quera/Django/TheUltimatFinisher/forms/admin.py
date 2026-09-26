from django.urls import reverse
from django.contrib import admin
from django.utils.html import format_html

from forms.models import Form, Field, Response, ResponseData, FormView


class FieldInline(admin.TabularInline):
    model = Field
    extra = 1
    fields = ['label', 'field_type', 'is_required', 'order', 'help_text']
    ordering = ['order']


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'is_active', 'response_count', 'view_form_link']
    list_filter = ['is_active', 'created_at', 'created_by']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'response_count']
    inlines = [FieldInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'created_by', 'is_active')
        }),
        ('Submission Settings', {
            'fields': ('allow_multiple_submissions', 'submission_limit', 'expires_at', 'success_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def response_count(self, obj):
        return obj.get_response_count()
    response_count.short_description = 'Responses'

    def view_form_link(self, obj):
        url = reverse('form_detail', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">View Form</a>', url)
    view_form_link.short_description = 'Public Link'


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'form', 'field_type', 'is_required', 'order']
    list_filter = ['field_type', 'is_required', 'form']
    search_fields = ['label', 'form__title']
    ordering = ['form', 'order']

    fieldsets = (
        ('Basic Information', {
            'fields': ('form', 'label', 'field_type', 'help_text', 'placeholder', 'is_required', 'order')
        }),
        ('Options (for choice fields)', {
            'fields': ('options',),
            'classes': ('collapse',)
        }),
        ('Validation Rules', {
            'fields': ('min_length', 'max_length', 'min_value', 'max_value', 'regex_pattern', 'custom_error_message'),
            'classes': ('collapse',)
        }),
    )


class ResponseDataInline(admin.TabularInline):
    model = ResponseData
    extra = 0
    readonly_fields = ['field', 'value']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ['form', 'submitted_at', 'submitted_by']
    list_filter = ['form', 'submitted_at']
    search_fields = ['form__title', 'submitted_by__username']
    readonly_fields = ['form', 'submitted_by', 'submitted_at']
    inlines = [ResponseDataInline]

    def has_add_permission(self, request):
        return False


@admin.register(ResponseData)
class ResponseDataAdmin(admin.ModelAdmin):
    list_display = ['response', 'field', 'value_preview']
    list_filter = ['field__field_type', 'response__form']
    search_fields = ['field__label', 'value']
    readonly_fields = ['response', 'field', 'value']

    def value_preview(self, obj):
        return obj.value[:100] + '...' if len(obj.value) > 100 else obj.value
    value_preview.short_description = 'Value'

    def has_add_permission(self, request):
        return False


@admin.register(FormView)
class FormViewAdmin(admin.ModelAdmin):
    list_display = ['form', 'viewed_at']
    list_filter = ['form', 'viewed_at']
    readonly_fields = ['form', 'viewed_at', 'referrer']

    def has_add_permission(self, request):
        return False
