from django.urls import path

from .views import sepa

urlpatterns = [
    path("", sepa.index, name="index"),
    path("generate/", sepa.generate, name="generate"),
]
