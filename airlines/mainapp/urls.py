from django.urls import path, include

from .views import user_session, admin_home, user_home, login_redirect, update_active, logout_redirect, add_file_form, manage_flights, update_confirmation, search_flights, search_path, view_reports_summary, view_reports_detailed 

from django.views.generic import TemplateView
from airlines import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('add_file_form/', add_file_form, name='add_file_form'),
    path('search_path/', search_path, name='search_path'),#черновой путь для поиска и вывода всех непрямых маршрутов
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
    path('update_confirmation/', update_confirmation, name='update_confirmation'),
    path('search-flights/', search_flights, name='search-flights'),
    path('reports_summary/', view_reports_summary, name='reports_summary'),
    path('reports_detailed/', view_reports_detailed, name='reports_detailed')
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
