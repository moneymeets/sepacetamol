from django.urls import path

from .views import datev, sepa

urlpatterns = [
    path("", sepa.index, name="index"),
    path("generate/", sepa.generate, name="generate"),
    path("personio-datev/", datev.index, name="personio-datev"),
]
