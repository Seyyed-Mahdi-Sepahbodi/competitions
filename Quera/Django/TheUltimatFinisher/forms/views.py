from django.utils import timezone
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

import io
import json
from datetime import timedelta

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer

from forms.models import Form, Field, Response, ResponseData, FormView
from forms.forms import FormCreationForm, FieldCreationForm, DynamicForm


class FormListView(LoginRequiredMixin, ListView):
    
    model = Form
    template_name = 'forms/form_list.html'
    context_object_name = 'forms'
    paginate_by = 10
    
    def get_queryset(self):
        return Form.objects.filter(created_by=self.request.user).annotate(
            response_count=Count('responses')
        )


class FormCreateView(LoginRequiredMixin, CreateView):
    
    model = Form
    form_class = FormCreationForm
    template_name = 'forms/form_create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        messages.success(self.request, 'Form created successfully!')
        return reverse('form_builder', kwargs={'pk': self.object.pk})


class FormUpdateView(LoginRequiredMixin, UpdateView):
    
    model = Form
    form_class = FormCreationForm
    template_name = 'forms/form_edit.html'
    
    def get_queryset(self):
        return Form.objects.filter(created_by=self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        messages.success(self.request, 'Form updated successfully!')
        return reverse('form_detail', kwargs={'pk': self.object.pk})


class FormDeleteView(LoginRequiredMixin, DeleteView):
    
    model = Form
    template_name = 'forms/form_delete.html'
    success_url = reverse_lazy('form_list')
    
    def get_queryset(self):
        return Form.objects.filter(created_by=self.request.user)


    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Form deleted successfully!')
        return super().delete(request, *args, **kwargs)


class FormDetailView(DetailView):
    
    model = Form
    template_name = 'forms/form_detail.html'
    context_object_name = 'form'

    def get_object(self, queryset = ...):
        form = get_object_or_404(Form, pk=self.kwargs['pk'])
        referrer = self.request.META.get('HTTP_REFERER', '')

        
        if self.request.user.is_authenticated:
            
            FormView.objects.get_or_create(
                form=form,
                viewed_by=self.request.user,
                defaults={
                    "referrer": referrer,
                }
            )
        else:
            
            if not self.request.session.session_key:
                self.request.session.create()
            session_key = self.request.session.session_key

            
            FormView.objects.get_or_create(
                form=form,
                session_key=session_key,
                defaults={
                    "referrer": referrer,
                }
            )

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dynamic_form'] = DynamicForm(self.object)
        return context


class FormBuilderView(LoginRequiredMixin, DetailView):
    
    model = Form
    template_name = 'forms/form_builder.html'
    context_object_name = 'form'
    
    def get_queryset(self):
        return Form.objects.filter(created_by=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = self.object.fields.all().order_by('order')
        return context


class FieldCreateView(LoginRequiredMixin, CreateView):
    
    model = Field
    form_class = FieldCreationForm
    template_name = 'forms/field_create.html'

    def dispatch(self, request, *args, **kwargs):
        self.form_instance = get_object_or_404(
            Form, 
            pk=kwargs['form_id'], 
            created_by=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['form_instance'] = self.form_instance
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_instance'] = self.form_instance
        return context
    
    def get_success_url(self):
        messages.success(self.request, 'Field added successfully!')
        return reverse('form_builder', kwargs={'pk': self.form_instance.pk})


class FieldUpdateView(LoginRequiredMixin, UpdateView):
    
    model = Field
    form_class = FieldCreationForm
    template_name = 'forms/field_edit.html'
    
    def get_queryset(self):
        return Field.objects.filter(form__created_by=self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['form_instance'] = self.object.form
        return kwargs
    
    def get_success_url(self):
        messages.success(self.request, 'Field updated successfully!')
        return reverse('form_builder', kwargs={'pk': self.object.form.pk})


class FieldDeleteView(LoginRequiredMixin, DeleteView):
    
    model = Field
    template_name = 'forms/field_delete.html'
    
    def get_queryset(self):
        return Field.objects.filter(form__created_by=self.request.user)
    
    def get_success_url(self):
        messages.success(self.request, 'Field deleted successfully!')
        return reverse('form_builder', kwargs={'pk': self.object.form.pk})


class FormSubmissionView(DetailView):
    
    model = Form
    template_name = 'forms/form_detail.html'
    
    def post(self, request, *args, **kwargs):
        pass

class FormSuccessView(DetailView):
    
    model = Form
    template_name = 'forms/form_success.html'
    context_object_name = 'form'


class FormResponsesView(LoginRequiredMixin, ListView):
    
    model = Response
    template_name = 'forms/form_responses.html'
    context_object_name = 'responses'
    paginate_by = 12
    
    def dispatch(self, request, *args, **kwargs):
        self.form_instance = get_object_or_404(
            Form, 
            pk=kwargs['pk'], 
            created_by=request.user
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Response.objects.filter(form=self.form_instance).select_related(
            'submitted_by'
        ).prefetch_related('data__field')
        
        
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')
        
        if date_from:
            queryset = queryset.filter(submitted_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(submitted_at__date__lte=date_to)
        
        if search:
            
            queryset = queryset.filter(
                data__value__icontains=search
            ).distinct()
        
        return queryset.order_by('-submitted_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_instance
        return context


class ResponseDetailView(LoginRequiredMixin, DetailView):
    
    model = Response
    template_name = 'forms/response_detail.html'
    context_object_name = 'response'
    
    def get_queryset(self):
        return Response.objects.filter(
            form__created_by=self.request.user
        ).select_related('form', 'submitted_by').prefetch_related('data__field')


class ResponseDeleteView(LoginRequiredMixin, DeleteView):
    
    model = Response
    template_name = 'forms/response_delete.html'
        
    def get_success_url(self):
        messages.success(self.request, 'Response deleted successfully!')
        return reverse('form_responses', kwargs={'pk': self.object.form.pk})


class FormAnalyticsView(LoginRequiredMixin, DetailView):
    
    model = Form
    template_name = 'forms/form_analytics.html'
    context_object_name = 'form'
    
    def get_queryset(self):
        return Form.objects.filter(created_by=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.object
        
        
        responses = form.responses.all()
        context['total_responses'] = responses.count()
        context['total_views'] = form.views.count()
        
        context['registered_users_count'] = responses.filter(submitted_by__isnull=False).count()
        context['anonymous_users_count'] = responses.filter(submitted_by__isnull=True).count()
        
        
        if responses.exists():
            context['completion_rate'] = form.get_completion_rate()
            context['avg_response_time'] = self.calculate_avg_response_time(responses)
            context['responses_by_day'] = self.get_responses_by_day(responses)
            context['field_analytics'] = self.get_field_analytics(form)
        
        now = timezone.now()

        
        
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())  
        month_start = today_start.replace(day=1)

        
        responses_today = responses.filter(submitted_at__gte=today_start).count()
        responses_week = responses.filter(submitted_at__gte=week_start).count()
        responses_month = responses.filter(submitted_at__gte=month_start).count()

        
        
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_start - timedelta(seconds=1)
        last_week_start = week_start - timedelta(days=7)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)

        responses_yesterday = responses.filter(
            submitted_at__gte=yesterday_start,
            submitted_at__lte=yesterday_end
        ).count()
        responses_last_week = responses.filter(
            submitted_at__gte=last_week_start,
            submitted_at__lt=week_start
        ).count()
        responses_last_month = responses.filter(
            submitted_at__gte=last_month_start,
            submitted_at__lt=month_start
        ).count()

        
        def growth(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round((current - previous) / previous * 100, 1)

        context.update({
            "responses_today": responses_today,
            "responses_week": responses_week,
            "responses_month": responses_month,
            "growth_today": growth(responses_today, responses_yesterday),
            "growth_week": growth(responses_week, responses_last_week),
            "growth_month": growth(responses_month, responses_last_month),
        })

        return context
    
    def calculate_avg_response_time(self, responses):
        
        responses_with_time = responses.filter(completion_time__isnull=False)
        
        if not responses_with_time.exists():
            return "N/A"
        
        total_seconds = sum(
            response.completion_time.total_seconds() 
            for response in responses_with_time
        )
        avg_seconds = total_seconds / responses_with_time.count()
        
        
        if avg_seconds < 60:
            return f"{int(avg_seconds)}s"
        elif avg_seconds < 3600:
            minutes = int(avg_seconds // 60)
            seconds = int(avg_seconds % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(avg_seconds // 3600)
            minutes = int((avg_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def get_responses_by_day(self, responses):
        
        from django.utils import timezone
        from datetime import timedelta
        import json
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        
        daily_responses = {}
        for response in responses.filter(submitted_at__date__gte=start_date):
            date_str = response.submitted_at.strftime('%Y-%m-%d')
            daily_responses[date_str] = daily_responses.get(date_str, 0) + 1
        
        return json.dumps(daily_responses)
    
    def get_field_analytics(self, form):
        
        field_stats = []
        
        for field in form.fields.all():
            responses = ResponseData.objects.filter(field=field)
            total_responses = responses.count()
            
            stats = {
                'field': field,
                'total_responses': total_responses,
                'response_rate': (total_responses / form.get_response_count() * 100) if form.get_response_count() > 0 else 0,
            }
            
            
            if field.field_type in ['select', 'radio', 'checkbox']:
                
                choice_counts = {}
                for response in responses:
                    if field.field_type == 'checkbox':
                        try:
                            choices = json.loads(response.value)
                            if isinstance(choices, list):
                                for choice in choices:
                                    choice_counts[choice] = choice_counts.get(choice, 0) + 1
                        except (json.JSONDecodeError, TypeError):
                            choice_counts[response.value] = choice_counts.get(response.value, 0) + 1
                    else:
                        choice_counts[response.value] = choice_counts.get(response.value, 0) + 1
                
                stats['choice_distribution'] = choice_counts
            
            elif field.field_type == 'number':
                
                values = [float(r.value) for r in responses if r.value.replace('.', '').replace('-', '').isdigit()]
                if values:
                    stats['avg_value'] = sum(values) / len(values)
                    stats['min_value'] = min(values)
                    stats['max_value'] = max(values)
            
            field_stats.append(stats)
        
        return field_stats



@login_required
def export_responses(request, pk, format_type):
    
    form = get_object_or_404(Form, pk=pk, created_by=request.user)
    
    
    responses = form.responses.all()
    
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if date_from:
        responses = responses.filter(submitted_at__date__gte=date_from)
    if date_to:
        responses = responses.filter(submitted_at__date__lte=date_to)
    if search:
        responses = responses.filter(data__value__icontains=search).distinct()
    
    
    from .utils import FormExporter
    exporter = FormExporter(form)
    
    if format_type == 'csv':
        return exporter.export_responses_csv(responses)
    elif format_type == 'excel':
        return exporter.export_responses_excel(responses)
    elif format_type == 'pdf':
        return exporter.export_responses_pdf(responses)
    else:
        messages.error(request, 'Invalid export format.')
        return redirect('form_responses', pk=pk)


@login_required
def export_analytics(request, pk, format_type):
    
    form = get_object_or_404(Form, pk=pk, created_by=request.user)
    
    from .utils import FormExporter
    import io
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    if format_type == 'csv':
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        
        writer.writerow(['Form Analytics Report'])
        writer.writerow(['Form Title', form.title])
        writer.writerow(['Generated At', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])
        
        
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Views', form.views.count()])
        writer.writerow(['Total Responses', form.responses.count()])
        writer.writerow(['Completion Rate', f"{form.get_completion_rate():.1f}%"])
        writer.writerow([])
        
        
        writer.writerow(['Field Analytics'])
        writer.writerow(['Field Name', 'Field Type', 'Response Count', 'Response Rate'])
        
        for field in form.fields.all():
            response_count = field.responses.count()
            response_rate = (response_count / form.responses.count() * 100) if form.responses.count() > 0 else 0
            writer.writerow([
                field.label,
                field.get_field_type_display(),
                response_count,
                f"{response_rate:.1f}%"
            ])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{form.title}_analytics.csv"'
        return response
    
    elif format_type == 'excel':
        
        import xlsxwriter
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Analytics')
        
        
        title_format = workbook.add_format({'bold': True, 'font_size': 16})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white'})
        
        
        row = 0
        worksheet.write(row, 0, f'Analytics Report: {form.title}', title_format)
        row += 2
        
        
        worksheet.write(row, 0, 'Metric', header_format)
        worksheet.write(row, 1, 'Value', header_format)
        row += 1
        
        stats = [
            ('Total Views', form.views.count()),
            ('Total Responses', form.responses.count()),
            ('Completion Rate', f"{form.get_completion_rate():.1f}%"),
        ]
        
        for metric, value in stats:
            worksheet.write(row, 0, metric)
            worksheet.write(row, 1, value)
            row += 1
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{form.title}_analytics.xlsx"'
        return response
    
    elif format_type == 'pdf':
        
        exporter = FormExporter(form)
        return exporter.export_responses_pdf(form.responses.all())
    
    else:
        messages.error(request, 'Invalid export format.')
        return redirect('form_analytics', pk=pk)


@login_required
def export_single_response(request, pk, format_type):
    
    response_obj = get_object_or_404(
        Response, 
        pk=pk, 
        form__created_by=request.user
    )
    
    if format_type == 'pdf':
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        
        story.append(Paragraph(f"Response Details - {response_obj.form.title}", styles['Title']))
        story.append(Spacer(1, 12))
        
        
        story.append(Paragraph(f"<b>Response ID:</b> {response_obj.id}", styles['Normal']))
        story.append(Paragraph(f"<b>Submitted:</b> {response_obj.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"<b>User:</b> {response_obj.submitted_by.username if response_obj.submitted_by else 'Anonymous'}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        
        story.append(Paragraph("Response Data", styles['Heading2']))
        
        for data in response_obj.data.all():
            story.append(Paragraph(f"<b>{data.field.label}:</b>", styles['Normal']))
            story.append(Paragraph(f"{data.value}", styles['Normal']))
            story.append(Spacer(1, 6))
        
        doc.build(story)
        output.seek(0)
        
        response = HttpResponse(output.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="response_{response_obj.id}.pdf"'
        return response
    
    else:
        messages.error(request, 'Invalid export format.')
        return redirect('response_detail', pk=pk)



@login_required
def get_field_options(request):
    
    field_id = request.GET.get('field_id')
    if field_id:
        try:
            field = Field.objects.get(id=field_id)
            return JsonResponse({'options': field.options})
        except Field.DoesNotExist:
            pass
    return JsonResponse({'options': []})


@login_required
def reorder_fields(request):
    
    if request.method == 'POST':
        field_ids = request.POST.getlist('field_ids[]')
        for index, field_id in enumerate(field_ids):
            try:
                field = Field.objects.get(
                    id=field_id,
                    form__created_by=request.user
                )
                field.order = index + 1
                field.save()
            except Field.DoesNotExist:
                continue
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
