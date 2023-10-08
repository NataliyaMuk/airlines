from django.urls import path, include
from .views import user_session, admin_home, user_home, login_redirect, update_active, logout_redirect, add_file_form, manage_flights
from django.views.generic import TemplateView
from airlines import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('add_file_form/', add_file_form, name='add_file_form'),
    # path('upload_file/', upload_file),
    path('logout_redirect/', logout_redirect),
    path('', TemplateView.as_view(template_name="home.html"), name='home'),
    # path('register/', register, name='register'),
    path('user-session/<str:email>', csrf_exempt(user_session), name='user-session/'),
    path('home_admin/', admin_home, name='home_admin'),
    path('home_user/', user_home, name='home_user'),
    path('login_redirect/', login_redirect, name='login_redirect'),
    path('update_active/', update_active, name='update_active'),
    path('manage-flights/', manage_flights, name='manage-flights'),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

