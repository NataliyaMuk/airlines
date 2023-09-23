from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from .forms import CustomAuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.views import View
import datetime
from .models import Sessions


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Логиним пользователя после успешной регистрации
            
            login(request, user)

            # инициируем сессию пользователя
            Sessions.objects.raw("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`) VALUES (NULL,1,NOW(),'Connection lost.')")
            # cursor.execute("INSERT INTO `sessions`(`id`, `user_id`, `session_start`, `error_status`) VALUES (NULL,%s,NOW(),'Connection lost.')", [user.id])
            # cursor.execute("INSERT INTO `sessions`(`id`, `user_id`, `session_start`, `error_status`) VALUES (NULL,1,NOW(),'Connection lost.')")
            return redirect('home')  # Замените 'home' на URL, куда перенаправлять после регистрации
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_session(request):
    if request.method == 'POST':
        status = request.POST['status']
        if status == 1 :
            now = datetime.datetime.now()


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'  # Создайте шаблон login.html
    authentication_form = CustomAuthenticationForm()