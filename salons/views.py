import datetime
import json

from django.core import serializers
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Appointment, Customer, Provider, Salon, Service


def index(request):
    return JsonResponse({'status': 'OK'})


def format_json_response(results: list | dict):
    return {'status': 'OK',
            'data': results}


def queryset_as_json_response(queryset, fields: list):
    serialized_instances = serializers.serialize('json', queryset, fields=fields)
    results = [{'pk': instance['pk'], **instance['fields']} for instance in json.loads(serialized_instances)]
    response = format_json_response(results)

    return JsonResponse(response)


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


def all_salons(request):
    query = request.GET.dict()
    salons = Salon.objects.all()
    if 'provider_id' in query and query['provider_id']:
        salons = salons.filter(provider=query['provider_id']).distinct()
    return queryset_as_json_response(salons, ['name', 'address', 'time_open', 'time_close'])


def nearest_salons(request):
    query = request.GET.dict()
    salon_distances = Salon.objects.nearest(float(query['lat']), float(query['lon']))
    results = []
    for salon, distance in salon_distances.items():
        results.append({
            **model_to_dict(salon),
            'distance': distance
        })
    response = format_json_response(results)
    return JsonResponse(response)


def get_services_for_salon(request, salon_id):
    salon = get_object_or_404(Salon, pk=salon_id)
    services = salon.get_available_services()
    return queryset_as_json_response(services, ['name', 'price'])


def get_providers_for_salon(request, salon_id):
    query = request.GET.dict()
    salon = get_object_or_404(Salon, pk=salon_id)
    providers = Provider.objects.filter(works_at=salon).distinct()
    if 'service_id' in query and query['service_id']:
        providers = providers.filter(service=query['service_id'])
    return JsonResponse(format_json_response([str(provider) for provider in providers]))


def get_available_appointments_for_salon(request, salon_id):
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
    return JsonResponse(response)


def get_services(request):
    query = request.GET.dict()
    services = Service.objects.all()
    if 'provider_id' in query and query['provider_id']:
        services = services.filter(provided_by=query['provider_id'])
    return queryset_as_json_response(services, ['name', 'price'])


# TODO option: nearest
def get_salons_for_service(request, service_id):
    query = request.GET.dict()
    default_days = 14
    n_days = int(query['n_days']) if 'n_days' in query else default_days
    service = get_object_or_404(Service, pk=service_id)
    salons = service.get_available_appointments_by_salon(n_days).keys()
    result = []
    for salon in salons:
        result.append(str(salon))
    response = format_json_response(result)
    return JsonResponse(response)


def get_providers_by_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    providers = service.provided_by.all()
    return JsonResponse(format_json_response([str(provider) for provider in providers]))


def all_providers(request):
    return queryset_as_json_response(Provider.objects.all(), ['first_name', 'last_name'])


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
    return Response(format_json_response(
        serialize_customer(customer)
    ))


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
    return JsonResponse({'status': 'OK',
                         'data': serialize_appointment(appt)})


def get_past_appointments(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    appts = customer.get_past_appointments()
    results = []
    for appt in appts:
        results.append(serialize_appointment(appt))
    response = format_json_response(results)
    return JsonResponse(response)


def get_future_appointments(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    appts = customer.get_future_appointments()
    results = []
    for appt in appts:
        results.append(serialize_appointment(appt))
    response = format_json_response(results)
    return JsonResponse(response)

# TODO search salons, services, providers
