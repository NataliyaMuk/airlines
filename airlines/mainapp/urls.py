from django.urls import path, include
from .views import register,user_session, admin_home, user_home, login_redirect
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name="home.html"), name='home'),
    path('register/', register, name='register'),
    path('user-session/', user_session, name='user-session/'),
    path('home_admin/', admin_home, name='home_admin'),
    path('home_user/', user_home, name='home_user'),
    path('login_redirect/', login_redirect, name='login_redirect'),
]
