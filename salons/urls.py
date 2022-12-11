from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('nearest', views.nearest_salons)
]
