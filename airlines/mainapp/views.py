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
import json
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login



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


def user_session(request,email):
    cursor = connection.cursor()
    # cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`, `status`) VALUES (NULL,1,NOW(),'Connection lost.',0)")
    # cursor.execute("UPDATE `mainapp_sessions` SET `last_confirmation`= '04041900' JOIN mainapp_users ON mainapp_users.id = mainapp_sessions.user_id  WHERE mainapp_users.Email = `j.doe@amonic.com`  and  mainapp_sessions.status = `0`')")
    if request.method == 'GET':
        # cursor.execute("UPDATE `mainapp_sessions` SET `last_confirmation`= NOW() JOIN mainapp_users ON mainapp_users.id = mainapp_sessions.user_id  WHERE mainapp_users.Email = `j.doe@amonic.com`  and  mainapp_sessions.status = `0`')")
        cursor = connection.cursor()
        # cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`, `status`) VALUES (NULL,1,NOW(),%s,0)",[email])
        cursor.execute("UPDATE mainapp_sessions SET status='1' WHERE status='0' and TIMESTAMPDIFF(SECOND,last_confirmation,NOW()) > 120")
        cursor.execute("UPDATE mainapp_sessions SET last_confirmation=NOW() WHERE mainapp_sessions.status='0' and (SELECT id FROM mainapp_users WHERE email = %s) = user_id",[email])

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

    cursor = connection.cursor()       
    if cursor.execute("SELECT * FROM `mainapp_sessions` WHERE user_id = %s and status='0'",[request.user.id]) != "NULL":
        cursor.execute("UPDATE mainapp_sessions SET last_confirmation=NOW() WHERE user_id = %s",[request.user.id])
    cursor.execute("UPDATE mainapp_sessions SET last_confirmation=NOW() WHERE TIMESTAMPDIFF(SECOND,last_confirmation,NOW()) > 120 and status='0'")
    cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`, `status`) VALUES (NULL,%s,NOW(),'Connection lost.',0)",[request.user.id])

    if request.user.RoleID.Title == "Administrator":  
        return redirect('home_admin')
    else:
        return redirect('home_user')


def user_home(request):
    # user = Users.objects.get(username="John")
    # user = authenticate(username="John")
    # login(request, user)
    # user.password = 123
    # user.save
    # Users.objects.create_user(password='123', is_superuser=1, id=1, Email="j.doe@amonic.com", FirstName="John", LastName="Doe", Birthdate="1983-01-13", Active=1, email="f")
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

def logout_redirect(request):
    cursor = connection.cursor()
    cursor.execute("UPDATE mainapp_sessions SET session_end=NOW(),status='1',error_status=NULL WHERE mainapp_sessions.status='0' and user_id = %s",[request.user.id])
    logout(request)
    return redirect('home')