import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

EXACT_HOURS_TEXT = _('Only exact hours with 00 minutes are allowed, e.g. 11:00, 14:00')


class Weekday(models.IntegerChoices):
    MONDAY = 0, _("Monday")
    TUESDAY = 1, _("Tuesday")
    WEDNESDAY = 2, _("Wednesday")
    THURSDAY = 3, _("Thursday")
    FRIDAY = 4, _("Friday")
    SATURDAY = 5, _("Saturday")
    SUNDAY = 6, _("Sunday")


def extract_working_hours(day_schedule: dict):
    return {
        'weekday': day_schedule['weekday'],
        'hours': list(range(day_schedule['time_from__hour'], day_schedule['time_till__hour']))
    }


class Salon(models.Model):
    name = models.CharField("название",  max_length=200)
    city = models.CharField("город", max_length=50, default="Москва")
    address = models.CharField("адрес", max_length=200)
    latitude = models.DecimalField("широта", max_digits=6, decimal_places=3)
    longitude = models.DecimalField("долгота", max_digits=6, decimal_places=3)
    time_open = models.TimeField("время открытия",
                                 help_text=EXACT_HOURS_TEXT)
    time_close = models.TimeField("время закрытия",
                                  help_text=EXACT_HOURS_TEXT)

    def __str__(self):
        return f'Салон {self.name}'

    def get_available_appointments_by_provider(self, n_days):
        available_appts = {}
        available_providers = set()
        if n_days >= 7:
            weekdays = Weekday
        else:
            weekdays = []
            for offset in range(n_days):
                date = datetime.date.today() + datetime.timedelta(days=offset)
                weekdays.append(date.weekday())
        provider_schedules = self.provider_schedules.filter(weekday__in=weekdays).prefetch_related('provider')
        for schedule in provider_schedules:
            available_providers.add(schedule.provider)
        for provider in available_providers:
            available_appts.update({provider: provider.get_available_hours(n_days)})
        return available_appts

    # TODO get nearest


class Provider(models.Model):
    first_name = models.CharField("имя", max_length=50)
    last_name = models.CharField("фамилия", max_length=50)
    photo = models.ImageField("фото", upload_to='providers',
                              null=True, blank=True)
    works_at = models.ManyToManyField(Salon, verbose_name="где работает",
                                      related_name='providers', related_query_name='provider',
                                      through='ProviderSchedule')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def get_available_hours(self, n_days):
        working_timeslots = self.working_timeslots.all()
        working_hours = list(map(
            extract_working_hours,
            working_timeslots.values('weekday', 'time_from__hour', 'time_till__hour')
        ))
        available_times = []
        for offset in range(n_days):
            date = datetime.date.today() + datetime.timedelta(days=offset)
            todays_schedule = working_timeslots.filter(weekday=date.weekday())
            if todays_schedule.exists():
                todays_hours = next(filter(
                    lambda schedule: schedule['weekday'] == date.weekday(),
                    working_hours)
                )['hours']
                todays_appointments = self.appointments.filter(date=date)
                if todays_appointments.exists():
                    appt_hours = list(todays_appointments.values_list('time__hour', flat=True))
                available_hours = list(filter(lambda hour: hour not in appt_hours, todays_hours))
                available_times.append({'weekday': date.weekday(), 'available_hours': available_hours})
        return available_times


class ProviderSchedule(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE,
                                 verbose_name="мастер",
                                 related_name='working_timeslots')
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE,
                              verbose_name="салон",
                              related_name='provider_schedules')
    weekday = models.IntegerField("день недели", choices=Weekday.choices)
    time_from = models.TimeField("начало работы",
                                 help_text=EXACT_HOURS_TEXT)
    time_till = models.TimeField("конец работы",
                                 help_text=EXACT_HOURS_TEXT)

    # TODO better unique constraint - work in multiple salons on the same day, have breaks
    class Meta:
        unique_together = ['provider', 'weekday']

    def __str__(self):
        return f'{self.provider} {self.get_weekday_display()} c {self.time_from} по {self.time_till} в {self.salon}'


class Service(models.Model):
    name = models.CharField("название",  max_length=200)
    price = models.DecimalField("цена", max_digits=8, decimal_places=2)
    provided_by = models.ManyToManyField(Provider, verbose_name="предоставляют мастера",
                                         related_name='services', related_query_name='service')

    def __str__(self):
        return f'{self.name}'

    def get_available_appointments_by_salon(self, n_days):
        providers = self.provided_by.prefetch_related('works_at')
        salons = set()
        available_appts = {}
        for provider in providers:
            salons.update(provider.works_at.all())
        for salon in salons:
            available_appts.update({salon: salon.get_available_appointments_by_provider(n_days)})
        return available_appts


class Customer(models.Model):
    telegram_id = models.IntegerField()
    first_name = models.CharField("имя", max_length=50)
    last_name = models.CharField("фамилия", max_length=50)
    phone_number = PhoneNumberField("телефон")

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    # TODO get past & future appointments


class Appointment(models.Model):
    date = models.DateField("дата")
    time = models.TimeField("время")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,
                                 verbose_name="клиент",
                                 related_name='appointments')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE,
                                 verbose_name="мастер",
                                 related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.CASCADE,
                                verbose_name="услуга")

    class Meta:
        unique_together = ['provider', 'date', 'time']

    @property
    def salon(self):
        matching_schedule = ProviderSchedule.objects.get(
            provider=self.provider,
            weekday=self.date.weekday(),
            time_from__lte=self.time,
            time_till__gt=self.time,
        )
        return matching_schedule.salon

    def __str__(self):
        return f'Запись {self.customer} к {self.provider} в {self.salon}, {self.date} {self.time}'
