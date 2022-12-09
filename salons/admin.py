from django.contrib import admin
from .models import Salon, Provider, ProviderSchedule, Service, Customer, Appointment


class AppointmentInline(admin.TabularInline):
    model = Appointment


class ProviderScheduleInline(admin.TabularInline):
    model = ProviderSchedule


@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    inlines = [
        ProviderScheduleInline
    ]


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    inlines = [
        ProviderScheduleInline
    ]


@admin.register(ProviderSchedule)
class ProviderScheduleAdmin(admin.ModelAdmin):
    pass


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    pass


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    inlines = [
        AppointmentInline
    ]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    pass
