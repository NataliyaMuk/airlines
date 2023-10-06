from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from .forms import CustomAuthenticationForm
from .forms import AddFileForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.views import View
import datetime
from .models import Sessions
from django.db import connection, transaction
from .decorators import admin_required
from .models import Users, Roles
import json
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
import csv


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
from axes.utils import reset

@login_required
def login_redirect(request):

    # user = authenticate(request, username=username, password=password)
    user = request.user.Email

    # Сброс блокировки для данного пользователя(неудачных попыток)
    reset(username=user)


    cursor = connection.cursor()       
    if cursor.execute("SELECT * FROM `mainapp_sessions` WHERE user_id = %s and status='0'",[request.user.id]) != "NULL":
        cursor.execute("UPDATE mainapp_sessions SET last_confirmation=NOW() WHERE user_id = %s",[request.user.id])
    cursor.execute("UPDATE mainapp_sessions SET last_confirmation=NOW() WHERE TIMESTAMPDIFF(SECOND,last_confirmation,NOW()) > 120 and status='0'")
    cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`, `status`) VALUES (NULL,%s,NOW(),'Connection lost.',0)",[request.user.id])

    if request.user.RoleID.Title == "Administrator":  
        return redirect('home_admin')
    else:
        return redirect('home_user')

@admin_required
def add_file_form(request):
    if request.method == "POST":
        form = AddFileForm(request.POST,request.FILES)
        File = request.FILES["file"]
        a = []
        results = []

        reader = csv.reader(File)
        for row in File:
        #     row[2] = str(row[2]) +":00"
        #     if row[0] == 'ADD':
        #         cursor.execute("INSERT INTO `schedules`(`ID`, `Date`, `Time`, `AircraftID`, `RouteID`, `EconomyPrice`, `Confirmed`, `FlightNumber`) VALUES (NULL,%s,%s,%s,(SELECT id FROM routes WHERE DepartureAirportID = (SELECT id FROM airports WHERE IATACode = %s) and ArrivalAirportID = (SELECT id FROM airports WHERE IATACode  = %s)),%s,%s,%s)",[row[1],row[2],row[6],row[4],row[5],row[7],row[8],row[3]])
        #     if row[0] == 'EDIT':
        #         cursor.execute("UPDATE `schedules` SET `Confirmed`=0 WHERE (SELECT id FROM routes WHERE DepartureAirportID = (SELECT id FROM airports WHERE IATACode = %s) and ArrivalAirportID = (SELECT id FROM airports WHERE IATACode = %s)) and FlightNumber = %s AND Date = $s AND Time = %s",[row[4],row[5],row[3],row[1],row[2]])
        # return redirect('home_admin')
            words = str(row).split(',')
            words[0] = words[0][2:]
            words[2] = str(words[2]) +":00"
            words[7] = words[7][:3]
            words[-1] = 'OK'
            results.append(words)
            a.append(row)
        context = {'files': results , 'readers': [request.FILES["file"]]} 
        return render(request, 'error_page.html', context) 
    else:
        form = AddFileForm()
        return render(request, 'add_file_form.html',{'form':form})

# @csrf_exempt
# def upload_file(request):
#     File = request.FILES['inp_file']
#     # with open("C:\\Users\\Vlad\\Desktop\\python\\airlines\\Schedules_V12.csv", newline='') as File: 
#     reader = csv.reader(File)
#     cursor = connection.cursor()
#     if not(reader):
#         return redirect('home_admin')
#     for row in reader:
#         row[2] = row[2] +":00"
#         if row[0] == 'ADD':
#             cursor.execute("INSERT INTO `schedules`(`ID`, `Date`, `Time`, `AircraftID`, `RouteID`, `EconomyPrice`, `Confirmed`, `FlightNumber`) VALUES (NULL,%s,%s,%s,(SELECT id FROM routes WHERE DepartureAirportID = (SELECT id FROM airports WHERE IATACode = %s) and ArrivalAirportID = (SELECT id FROM airports WHERE IATACode  = %s)),%s,%s,%s)",[row[1],row[2],row[6],row[4],row[5],row[7],row[8],row[3]])
#         if row[0] == 'EDIT':
#             cursor.execute("UPDATE `schedules` SET `Confirmed`=0 WHERE (SELECT id FROM routes WHERE DepartureAirportID = (SELECT id FROM airports WHERE IATACode = %s) and ArrivalAirportID = (SELECT id FROM airports WHERE IATACode = %s)) and FlightNumber = %s AND Date = $s AND Time = %s",[row[4],row[5],row[3],row[1],row[2]])
#     context = {'files': [File], 'readers': [reader]}
#     return render(request, 'error_page.html', context)
 
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

# добавление новых пользователей
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save() 
    else:
        form = CustomUserCreationForm()

    context = {'users': users, 'form': form}

    return render(request, 'home_admin.html', context)


def update_active(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle_role_apply':
            
            valueOfRole = request.POST.get('editRole')
            role = Roles.objects.get(Title=valueOfRole)

            user_id = request.POST.get('userID')
            user_id = int(user_id)
            user = Users.objects.get(pk=user_id)
            print(user_id)

            user.RoleID = role
            print(request.POST)
            user.save()


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