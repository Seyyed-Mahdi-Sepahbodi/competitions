from django.urls import path

from forms import views

urlpatterns = [
    # Form management URLs
    path('', views.FormListView.as_view(), name='form_list'),
    path('create/', views.FormCreateView.as_view(), name='form_create'),
    path('form/<int:pk>/', views.FormDetailView.as_view(), name='form_detail'),
    path('form/<int:pk>/edit/', views.FormUpdateView.as_view(), name='form_edit'),
    path('form/<int:pk>/delete/', views.FormDeleteView.as_view(), name='form_delete'),
    
    # Form builder URLs
    path('form/<int:pk>/builder/', views.FormBuilderView.as_view(), name='form_builder'),
    path('form/<int:form_id>/field/add/', views.FieldCreateView.as_view(), name='field_create'),
    path('field/<int:pk>/edit/', views.FieldUpdateView.as_view(), name='field_edit'),
    path('field/<int:pk>/delete/', views.FieldDeleteView.as_view(), name='field_delete'),
    
    # Form submission URLs
    path('form/<int:pk>/submit/', views.FormSubmissionView.as_view(), name='form_submit'),
    path('form/<int:pk>/success/', views.FormSuccessView.as_view(), name='form_success'),
    
    # Analytics URLs
    path('form/<int:pk>/analytics/', views.FormAnalyticsView.as_view(), name='form_analytics'),
    path('form/<int:pk>/responses/', views.FormResponsesView.as_view(), name='form_responses'),
    path('response/<int:pk>/', views.ResponseDetailView.as_view(), name='response_detail'),
    path('response/<int:pk>/delete/', views.ResponseDeleteView.as_view(), name='response_delete'),
    
    # Export URLs
    path('form/<int:pk>/export/responses/<str:format_type>/', views.export_responses, name='export_responses'),
    path('form/<int:pk>/export/analytics/<str:format_type>/', views.export_analytics, name='export_analytics'),
    path('response/<int:pk>/export/<str:format_type>/', views.export_single_response, name='export_single_response'),
    
    # AJAX URLs
    path('ajax/field-options/', views.get_field_options, name='ajax_field_options'),
    path('ajax/reorder-fields/', views.reorder_fields, name='ajax_reorder_fields'),
]
