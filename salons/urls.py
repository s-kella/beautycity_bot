from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('nearest', views.nearest_salons),
    path('salons', views.all_salons),
    path('services', views.get_services),
    path('providers', views.all_providers),

    path('register_customer', views.register_customer),
    path('customer/<int:customer_id>/past', views.get_past_appointments),
    path('customer/<int:customer_id>/future', views.get_future_appointments),
    path('make_appointment', views.make_appointment),

    path('salon/<int:salon_id>/available_appointments', views.get_available_appointments_for_salon),
    path('salon/<int:salon_id>/providers', views.get_providers_for_salon),
    path('salon/<int:salon_id>/services', views.get_services_for_salon),

    path('service/<int:service_id>/providers', views.get_providers_by_service),
    path('service/<int:service_id>/salons', views.get_salons_for_service)


]
