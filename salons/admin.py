from django.contrib import admin
from .models import Salon, Provider, ProviderSchedule, Service, Customer, Appointment


@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    # TODO display schedule, services?
    pass


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    # TODO display services, schedule
    pass


@admin.register(ProviderSchedule)
class ProviderScheduleAdmin(admin.ModelAdmin):
    pass


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    # TODO display providers
    pass


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    pass


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    pass
