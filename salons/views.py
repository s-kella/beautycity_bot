from django.forms.models import model_to_dict
from django.http import JsonResponse
from .models import Appointment, Customer, Provider, Salon, Service


def index(request):
    return JsonResponse({'status': 'OK'})


def nearest_salons(request):
    query = request.GET.dict()
    salon_distances = Salon.objects.nearest(float(query['lat']), float(query['lon']))
    results = []
    for salon, distance in salon_distances.items():
        results.append({
            **model_to_dict(salon),
            'distance': distance
        })
    response = {'status': 'OK',
                'salons': results}
    return JsonResponse(response)


