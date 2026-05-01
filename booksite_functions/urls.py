from django.urls import path
from . import views
urlpatterns = [
    path("step1/", views.step1, name="step1"),
    path("step2/", views.step2, name="step2"),
    path("", views.home, name="home"),
]