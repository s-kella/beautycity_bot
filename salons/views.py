import datetime
import json
import urllib.parse

from django.core import serializers
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404, redirect, reverse
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from .models import Appointment, Customer, Provider, Salon, Service


def format_json_response(results: list | dict):
    return {'status': 'OK',
            'data': results}


def queryset_as_json_response(queryset, fields: list):
    serialized_instances = serializers.serialize('json', queryset, fields=fields)
    results = [{'pk': instance['pk'], **instance['fields']} for instance in json.loads(serialized_instances)]
    response = format_json_response(results)
    return Response(response)


def serialize_customer(customer):
    return {
        'pk': customer.pk,
        'first_name': customer.first_name,
        'last_name': customer.last_name,
        'telegram_id': customer.telegram_id,
        'phone_number': str(customer.phone_number),
    }


def serialize_appointment(appt):
    return {
        'pk': appt.pk,
        'datetime': appt.datetime,
        'provider': str(appt.provider),
        'service': str(appt.service),
        'salon': str(appt.salon),
    }


@api_view(['GET'])
def index(request):
    return Response({'status': 'OK'})


@api_view(['GET'])
def all_salons(request):
    query = request.GET.dict()
    salons = Salon.objects.all()
    if 'provider_id' in query and query['provider_id']:
        provider = get_object_or_404(Provider, pk=query['provider_id'])
        salons = salons.filter(provider=provider).distinct()
    if 'service_id' in query and query['service_id']:
        service = get_object_or_404(Service, pk=query['service_id'])
        salons = salons.filter(provider__service=service).distinct().order_by('pk')

    if 'lat' not in query:
        return queryset_as_json_response(salons, ['name', 'city', 'address', 'time_open', 'time_close'])

    salon_distances = salons.nearest(float(query['lat']), float(query['lon']))
    results = []
    for salon, distance in salon_distances.items():
        results.append({
            **model_to_dict(salon),
            'distance': distance
        })
    response = format_json_response(results)
    return Response(response)


@api_view(['GET'])
def all_services(request):
    query = request.GET.dict()
    services = Service.objects.all()
    if 'provider_id' in query and query['provider_id']:
        provider = get_object_or_404(Provider, pk=query['provider_id'])
        services = services.filter(provided_by=provider)
    if 'salon_id' in query and query['salon_id']:
        salon = get_object_or_404(Salon, pk=query['salon_id'])
        services = services.filter(provided_by__works_at=salon).distinct().order_by('pk')
    return queryset_as_json_response(services, ['name', 'price'])


@api_view(['GET'])
def all_providers(request):
    query = request.GET.dict()
    providers = Provider.objects.all()
    if 'salon_id' in query and query['salon_id']:
        salon = get_object_or_404(Salon, pk=query['salon_id'])
        providers = providers.filter(works_at=salon).distinct()
    if 'service_id' in query and query['service_id']:
        service = get_object_or_404(Service, pk=query['service_id'])
        providers = providers.filter(service=service)
    return queryset_as_json_response(providers, ['first_name', 'last_name'])


@api_view(['GET'])
def show_customer(request):
    query = request.GET.dict()
    if 'telegram_id' not in query:
        raise APIException
    customer = get_object_or_404(Customer, telegram_id=query['telegram_id'])
    return Response(format_json_response(serialize_customer(customer)))



@api_view(['GET'])
def available_appointments_for_salon(request, salon_id):
    query = request.GET.dict()
    default_days = 14
    n_days = int(query['n_days']) if 'n_days' in query else default_days
    salon = get_object_or_404(Salon, pk=salon_id)
    hours_by_provider = salon.get_available_appointments_by_provider(
        n_days,
        query['provider_id'] if 'provider_id' in query and query['provider_id'] else None
    )
    result = {}
    for provider, hours in hours_by_provider.items():
        result.update({str(provider): hours})
    response = format_json_response(result)
    return Response(response)


@api_view(['POST'])
def register_customer(request):
    name = request.data['name']
    *first_name, last_name = name.split(' ')
    first_name = ' '.join(first_name)
    customer = Customer.objects.create(
        telegram_id=request.data['telegram_id'],
        first_name=first_name,
        last_name=last_name,
        phone_number=request.data['phone_number'],
    )
    return Response({
        'status': 'created',
        'data': serialize_customer(customer)
    })


@api_view(['POST'])
def make_appointment(request):
    customer = get_object_or_404(Customer, pk=request.data['customer_id'])
    provider = get_object_or_404(Provider, pk=request.data['provider_id'])
    service = get_object_or_404(Service, pk=request.data['service_id'])

    time = datetime.time(int(request.data['hour']), 0)
    appt = Appointment.objects.create(
        datetime=datetime.datetime.combine(datetime.date.fromisoformat(request.data['date']), time),
        customer=customer,
        provider=provider,
        service=service,
    )
    return Response({'status': 'created',
                     'data': serialize_appointment(appt)})


@api_view(['GET'])
def past_appointments(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    appts = customer.get_past_appointments()
    results = []
    for appt in appts:
        results.append(serialize_appointment(appt))
    response = format_json_response(results)
    return Response(response)


@api_view(['GET'])
def future_appointments(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    appts = customer.get_future_appointments()
    results = []
    for appt in appts:
        results.append(serialize_appointment(appt))
    response = format_json_response(results)
    return Response(response)


# LEGACY
# vvvvvv

@api_view(['GET'])
def nearest_salons(request):
    return redirect(reverse('salons') + '?' + request.GET.urlencode())


@api_view(['GET'])
def services_for_salon(request, salon_id):
    return redirect(reverse('services') + '?' +
                    urllib.parse.urlencode({'salon_id': salon_id}))


@api_view(['GET'])
def providers_for_salon(request, salon_id):
    return redirect(reverse('providers') + '?' +
                    urllib.parse.urlencode({'salon_id': salon_id}))


@api_view(['GET'])
def all_salons_for_service(request, service_id):
    return redirect(reverse('salons') + '?' +
                    urllib.parse.urlencode({'service_id': service_id}))


@api_view(['GET'])
def providers_for_service(request, service_id):
    return redirect(reverse('providers') + '?' +
                    urllib.parse.urlencode({'service_id': service_id}))
