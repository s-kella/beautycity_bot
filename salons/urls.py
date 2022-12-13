from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('nearest/', views.nearest_salons, name='nearest'),
    path('salons/', views.all_salons, name='salons'),
    path('services/', views.all_services, name='services'),
    path('providers/', views.all_providers, name='providers'),

    path('register_customer/', views.register_customer, name='register_customer'),
    path('customer/', views.show_customer, name='customer'),
    path('customer/<int:customer_id>/past/', views.past_appointments, name='past_appointments'),
    path('customer/<int:customer_id>/future/', views.future_appointments, name='future_appointments'),
    path('make_appointment/', views.make_appointment, name='future_appointments'),

    path('salon/<int:salon_id>/available_appointments/',
         views.available_appointments_for_salon, name='available_appointments'),
    path('salon/<int:salon_id>/providers/', views.providers_for_salon, name='providers_for_salon'),
    path('salon/<int:salon_id>/services/', views.services_for_salon, name='services_for_salon'),

    path('service/<int:service_id>/providers/', views.providers_for_service, name='providers_for_service'),
    path('service/<int:service_id>/salons/', views.all_salons_for_service, name='all_salons_for_service'),


]
