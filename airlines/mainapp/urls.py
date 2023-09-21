from django.urls import path, include
from .views import *
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name="home.html"), name='home'),
]
