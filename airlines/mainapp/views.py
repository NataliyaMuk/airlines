from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from .forms import CustomAuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.views import View
import datetime
from .models import Sessions
from django.db import connection, transaction
from .decorators import admin_required
from .models import Users



# def register(request):
#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             # Логиним пользователя после успешной регистрации
            
#             login(request, user)

#             # инициируем сессию пользователя
#             # Sessions.objects.raw("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`) VALUES (NULL,1,NOW(),'Connection lost.')")
#             # cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`) VALUES (NULL,%s,NOW(),'Connection lost.')", [user.id])
#             cursor = connection.cursor()
            
#             cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`, `status`) VALUES (NULL,%s,NOW(),'Connection lost.',0)",[user.id])
#             return redirect('home')  
#     else:
#         form = CustomUserCreationForm()
#     return render(request, 'registration/register.html', {'form': form})


def user_session(request):
    if request.method == 'POST':
        status = request.POST['status']
        email = request.POST['email']
        if status == 1 :
            cursor = connection.cursor()
            cursor.execute("UPDATE `mainapp_sessions` SET `last_confirmation`= NOW() JOIN mainapp_users ON mainapp_users.id = mainapp_sessions.user_id  WHERE mainapp_users.Email = %s and  mainapp_sessions.status = `0`')",[email])


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = CustomAuthenticationForm()


    # для логина
    # if  cursor.execute("SELECT * FROM `mainapp_sessions` WHERE user_id = %s",[user.id])
    #     cursor.execute("UPDATE `mainapp_sessions` SET `status`= `1` WHERE user_id = %s and  status = `0`')",[user.id]) #закрываваем сессию с ошибкой.
    #cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`, `status`) VALUES (NULL,%s,NOW(),'Connection lost.',0)",[user.id] #начинаем новую сессию

    # для разлогирования
    # cursor.execute("UPDATE `mainapp_sessions` SET `status`= `1`,`error_status`=NULL,`session_end`= NOW() WHERE user_id = %s and status = `0`')",[user.id])

    # для вывода сессий по пользователею
    # сursor.execute("SELECT * FROM `mainapp_sessions` WHERE user_id = %s",[user.id])

from django.contrib.auth.decorators import login_required

@login_required
def login_redirect(request):
    if request.user.RoleID.Title == "Administrator":  
        return redirect('home_admin')
    else:
        return redirect('home_user')


def user_home(request):
    # Логика для главной страницы обычных пользователей
    return render(request, 'home_user.html')


@admin_required #кастомный декоратор
def admin_home(request):

    selected_office = request.GET.get('office')
    if selected_office and selected_office != '0':
        users = Users.objects.filter(OfficeID=selected_office)
    else:
        users = Users.objects.all()

# ЛОГИКА РЕГИСТРАЦИИ ТЕПЕРЬ ТУТ!!!! ТОЛЬКО АДМИН МОЖЕТ ДОБАВЛЯТЬ НОВЫХ ЮЗЕРОВ
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()

            # СЕССИЯ ПОСЛЕ ДОБАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯ НЕ НУЖНА ТЕПЕРЬ!!!!!!!!!!!!!!!!!

            # инициируем сессию пользователя
            # Sessions.objects.raw("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`) VALUES (NULL,1,NOW(),'Connection lost.')")
            # cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`) VALUES (NULL,%s,NOW(),'Connection lost.')", [user.id])
            # cursor = connection.cursor()
            
            # cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`, `status`) VALUES (NULL,%s,NOW(),'Connection lost.',0)",[user.id])
            # return redirect('home')  
    else:
        form = CustomUserCreationForm()

    context = {'users': users, 'form': form}

    return render(request, 'home_admin.html', context)


def update_active(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle_role_apply':
            # user = Users.objects.get(pk=user_id)
            # user.RoleID = request.POST
            selected_users = request.POST.getlist('selected_users')
            print("Попадание в функцию")
            print(request.POST)
            print(selected_users)
            # Попадание в функцию
            # <QueryDict: {'csrfmiddlewaretoken': ['GFIEa33cLtVd9JKjWlltQ9ygHTxTnMVyg7ICMBFiAx1fSh8kZcAepkGmqMCUUzkP'],
            #  'editEmail': [''], 'editFirstName': [''], 'editLastName': [''],
            #  'editOffice': [''], 'editRole': ['Administrator'], 'action': ['toggle_role_apply']}>
            # user.save()

           
        elif action == 'enable_disable_login':
            selected_users = request.POST.getlist('selected_users')
            for user_id in selected_users:
                user = Users.objects.get(pk=user_id)
                user.Active = not user.Active  # Инвертируем значение Active (1 -> 0, 0 -> 1)
                user.save()
        
        return redirect('home_admin')  
    return render(request, 'home_admin.html') 

