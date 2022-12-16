import datetime
from math import radians, cos, sin, asin, sqrt

from django.db import models
from django.db.models import F, Func
from django.utils import timezone
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


def haversine_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371
    # convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = earth_radius * c
    return round(km, 3)


class SalonManager(models.Manager):
    pass


# TODO add pre-filtering by city for larger DBs
class NearestQuerySet(models.QuerySet):
    def with_degree_diff_from_user(self, user_lat: float, user_lon: float):
        return self.annotate(
            degree_diff_lat=Func(F('latitude') - user_lat, function='ABS', output_field=models.FloatField()),
            degree_diff_lon=Func(F('longitude') - user_lon, function='ABS', output_field=models.FloatField()),
            degree_diff=(F('degree_diff_lat') + F('degree_diff_lon')),
        )

    # TODO lower limits
    def nearest(self, user_lat: float, user_lon: float, max_dist_km=10000, max_results=5) -> dict:
        """
        Query salons by distance from user.
        @return: dict in the format {salon, distance_in_km}
        """
        nearish_salons = (self.with_degree_diff_from_user(user_lat, user_lon)
                          .filter(degree_diff__lte=100))
        nearest_salons = []
        for salon in nearish_salons:
            distance = salon.get_distance_from_user(user_lat, user_lon)
            if distance < max_dist_km:
                nearest_salons.append(
                    (salon, distance)
                )
        salons_by_distance = sorted(nearest_salons, key=lambda x: x[1])[:max_results]
        return dict(salons_by_distance)


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

    objects = SalonManager.from_queryset(NearestQuerySet)()

    def __str__(self):
        return f'Салон {self.name}, {self.address}'

    def get_available_services(self):
        services = set()
        providers = self.providers.all().distinct()
        print(providers)
        for provider in providers:
            services.update(
                Service.objects.filter(provided_by=provider)
            )
        return services

    def get_available_appointments_by_provider(self, n_days, specific_provider=None) -> dict:
        available_providers = set()
        if n_days >= 7:
            weekdays = Weekday
        else:
            weekdays = []
            for offset in range(n_days):
                date = datetime.date.today() + datetime.timedelta(days=offset)
                weekdays.append(date.weekday())
        if specific_provider:
            provider_schedules = (self.provider_schedules
                                  .filter(weekday__in=weekdays, provider=specific_provider)
                                  .prefetch_related('provider'))
        else:
            provider_schedules = self.provider_schedules.filter(weekday__in=weekdays).prefetch_related('provider')
        for schedule in provider_schedules:
            available_providers.add(schedule.provider)
        available_appts = {}
        for provider in available_providers:
            available_appts.update({provider: provider.get_available_hours(n_days)})
        return available_appts

    def get_distance_from_user(self, user_lat, user_lon):
        return haversine_distance(self.latitude, self.longitude, user_lat, user_lon)


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

    def get_available_hours(self, n_days) -> list[dict]:
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
                todays_appointments = self.appointments.filter(datetime__date=date)
                appt_hours = []
                if todays_appointments.exists():
                    appt_hours = list(todays_appointments.values_list('datetime__time__hour', flat=True))
                available_hours = list(filter(lambda hour: hour not in appt_hours, todays_hours))
                available_times.append({
                    'date': date,
                    'weekday': Weekday(date.weekday()).label,
                    'available_hours': available_hours,
                })
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

    # TODO only last 6 months of appts
    def get_past_appointments(self, window_months=6):
        return Appointment.objects.filter(customer=self, datetime__lt=timezone.now())

    def get_future_appointments(self):
        return Appointment.objects.filter(customer=self, datetime__gte=timezone.now())


class Appointment(models.Model):
    datetime = models.DateTimeField("дата и время")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,
                                 verbose_name="клиент",
                                 related_name='appointments')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE,
                                 verbose_name="мастер",
                                 related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.CASCADE,
                                verbose_name="услуга")

    # TODO check that a matching provider schedule exists
    class Meta:
        unique_together = ['provider', 'datetime']

    @property
    def salon(self):
        matching_schedule = ProviderSchedule.objects.get(
            provider=self.provider,
            weekday=self.datetime.date().weekday(),
            time_from__lte=self.datetime.time(),
            time_till__gt=self.datetime.time(),
        )
        return matching_schedule.salon

    def __str__(self):
        return f'Запись {self.customer} в {self.salon} к {self.provider}, {self.datetime}'
