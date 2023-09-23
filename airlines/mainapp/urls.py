from django.urls import path, include
from .views import register,user_session
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name="home.html"), name='home'),
    path('register/', register, name='register'),
    path('user-session/', user_session, name='user-session/'),
]
