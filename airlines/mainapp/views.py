import csv
from .forms import AddFileForm
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
from .models import Users, Roles, Schedules, Airports
import json
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.db.models import F, ExpressionWrapper, fields

import csv
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse



def user_session(request, email):
    cursor = connection.cursor()
    # cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`, `status`) VALUES (NULL,1,NOW(),'Connection lost.',0)")
    # cursor.execute("UPDATE `mainapp_sessions` SET `last_confirmation`= '04041900' JOIN mainapp_users ON mainapp_users.id = mainapp_sessions.user_id  WHERE mainapp_users.Email = `j.doe@amonic.com`  and  mainapp_sessions.status = `0`')")
    if request.method == 'GET':
        # cursor.execute("UPDATE `mainapp_sessions` SET `last_confirmation`= NOW() JOIN mainapp_users ON mainapp_users.id = mainapp_sessions.user_id  WHERE mainapp_users.Email = `j.doe@amonic.com`  and  mainapp_sessions.status = `0`')")
        cursor = connection.cursor()
        # cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`, `status`) VALUES (NULL,1,NOW(),%s,0)",[email])
        cursor.execute(
            "UPDATE mainapp_sessions SET status='1' WHERE status='0' and TIMESTAMPDIFF(SECOND,last_confirmation,NOW()) > 120")
        cursor.execute(
            "UPDATE mainapp_sessions SET last_confirmation=NOW() WHERE mainapp_sessions.status='0' and (SELECT id FROM mainapp_users WHERE email = %s) = user_id",
            [email])


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = CustomAuthenticationForm()

    # для логина
    # if  cursor.execute("SELECT * FROM `mainapp_sessions` WHERE user_id = %s",[user.id])
    #     cursor.execute("UPDATE `mainapp_sessions` SET `status`= `1` WHERE user_id = %s and  status = `0`')",[user.id]) #закрываваем сессию с ошибкой.
    # cursor.execute("INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`, `status`) VALUES (NULL,%s,NOW(),'Connection lost.',0)",[user.id] #начинаем новую сессию

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
    print(user)

    # Сброс блокировки для данного пользователя(неудачных попыток)
    reset(username=user)
    cursor = connection.cursor()
    if cursor.execute("SELECT * FROM `mainapp_sessions` WHERE user_id = %s and status='0'",
                      [request.user.id]) != "NULL":
        cursor.execute("UPDATE mainapp_sessions SET last_confirmation=NOW() WHERE user_id = %s", [request.user.id])
    cursor.execute(
        "UPDATE mainapp_sessions SET last_confirmation=NOW() WHERE TIMESTAMPDIFF(SECOND,last_confirmation,NOW()) > 120 and status='0'")
    cursor.execute(
        "INSERT INTO `mainapp_sessions`(`id`, `user_id`, `session_start`, `error_status`, `status`) VALUES (NULL,%s,NOW(),'Connection lost.',0)",
        [request.user.id])

    if request.user.RoleID.Title == "Administrator":
        return redirect('home_admin')
    else:
        return redirect('home_user')
    

# INSERT INTO `mainapp_files`(`Title`) VALUES (%s)

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
    # Логика для главной страницы обычных пользователей
    info = Sessions.objects.filter(user=request.user.id).annotate(
        time_difference=ExpressionWrapper(
            F('last_confirmation') - F('session_start'),
            output_field=fields.DurationField()
        )
        ,
    ).values('last_confirmation', 'session_start', 'time_difference', 'error_status')
    time = datetime.timedelta()
    crashes = 0
    for obj in info:
        try:
            obj['date'] = obj['last_confirmation'].date()
            obj['last_confirmation'] = obj['last_confirmation'].time()
        except AttributeError:
            obj['date'] = obj['session_start'].date()
            obj['last_confirmation'] = '-'
        obj['session_start'] = obj['session_start'].time()
        try:
            time += obj['time_difference']
        except TypeError:
            time += datetime.timedelta()
        if obj['error_status'] is not None:
            crashes += 1

    return render(request, 'home_user.html',
                  context={'data': info, 'time': time, 'crashes': crashes})


@admin_required  # кастомный декоратор
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
    cursor.execute(
        "UPDATE mainapp_sessions SET session_end=NOW(),status='1',error_status=NULL WHERE mainapp_sessions.status='0' and user_id = %s",
        [request.user.id])
    logout(request)
    return redirect('home')


@login_required
def manage_flights(request):
    if request.method == 'POST':
        id = request.POST.get('selectedId')
        date = datetime.datetime.strptime(request.POST.get('dateInput'), '%Y-%m-%d').date()
        time = datetime.datetime.strptime(request.POST.get('timeInput'), '%H:%M').time()
        economy_money = request.POST.get('numberInput')

        flight = Schedules.objects.get(ID=id)
        flight.Date = date
        flight.Time = time
        flight.EconomyPrice = economy_money
        flight.save()
        # Обработка полученных значений checkbox_values

        # return JsonResponse({'status': 'success'})  # Ответ в формате JSON

    selected_departure = request.GET.get('departure')
    selected_arrival = request.GET.get('arrival')
    selected_date = request.GET.get('date')
    selected_flight_number = request.GET.get('flightnumber')
    selected_sort = request.GET.get('sort')
    

    schedules = Schedules.objects.all()

    if selected_departure and selected_departure != '0':
        schedules = schedules.filter(RouteID__DepartureAirportID__ID=selected_departure)

    if selected_arrival and selected_arrival != '0':
        schedules = schedules.filter(RouteID__ArrivalAirportID__ID=selected_arrival)

    if selected_date and selected_date != '0':
        schedules = schedules.filter(Date=selected_date)

    if selected_flight_number and selected_flight_number != '0':
        schedules = schedules.filter(FlightNumber=selected_flight_number)
	

    #сортировка
    
    if selected_sort and selected_sort == '1':
        schedules = schedules.order_by("EconomyPrice")
    if selected_sort and selected_sort == '2':
        schedules = schedules.order_by("Confirmed")
    else:
        schedules = schedules.order_by("-Date", "Time")

    airports = Airports.objects.all()

    context = {'schedules': schedules, 'airports':airports}
    return render(request, 'manage-flights.html', context) 



@csrf_exempt
def process_checkbox_values(request):
    if request.method == 'POST':
        checkbox_values = request.POST.getlist('checkbox_values')

        # Обработка полученных значений checkbox_values

        return JsonResponse({'status': 'success'})  # Ответ в формате JSON

    return JsonResponse({'status': 'error'}, status=400)


def update_confirmation(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'cancel_flight':
            selected_flights = request.POST.getlist('selected_users')
            for flight_id in selected_flights:
                flight = Schedules.objects.get(pk=flight_id)
                flight.Confirmed = not flight.Confirmed  # Инвертируем значение Active (1 -> 0, 0 -> 1)
                flight.save()

        return redirect('manage-flights')
    return render(request, 'manage-flights.html') 


def search_flights(request):
    airports = Airports.objects.all()
    context = {'airports':airports}
    return render(request, 'search_flights.html', context) 


@admin_required
def add_file_form(request):
    if request.method == "POST":
        form = AddFileForm(request.POST, request.FILES)
        File = request.FILES["file"]
        results = []
        cursor = connection.cursor()

        reader = csv.reader(File)
        cursor.execute("SELECT `Title` FROM `mainapp_files` WHERE Title = %s", [str(File)])
        requestresult = cursor.fetchall()
        for (title) in requestresult:
            if str(File) == title[0]:
                return redirect('home_admin')
        for row in File:
            words = str(row).split(',')
            words[0] = words[0][2:]
            words[2] = str(words[2]) + ":00"
            words[7] = words[7][:3]
            words[6] = int(float(words[6]))
            if words[6] > 2:
                words[6] = 2

            if words[0] == 'ADD':
                words[-1] = 1
                cursor.execute("INSERT INTO `schedules`(`ID`, `Date`, `Time`, `AircraftID`, `RouteID`, `EconomyPrice`, `Confirmed`, `FlightNumber`) VALUES (NULL,%s,%s,%s,(SELECT id FROM routes WHERE DepartureAirportID = (SELECT id FROM airports WHERE IATACode = %s LIMIT 1) and ArrivalAirportID = (SELECT id FROM airports WHERE IATACode  = %s LIMIT 1) LIMIT 1),%s,%s,%s)",[words[1],words[2],int(float(words[6])),words[4],words[5],words[7],words[-1],words[3]])
            else:
                words[-1] = 0
                cursor.execute("UPDATE `schedules` SET `Confirmed`= 0 WHERE (SELECT id FROM routes WHERE DepartureAirportID = (SELECT id FROM airports WHERE IATACode = %s LIMIT 1) and ArrivalAirportID = (SELECT id FROM airports WHERE IATACode = %s LIMIT 1) LIMIT 1) and FlightNumber = %s AND Date = %s AND Time = %s",[words[4],words[5],words[3],words[1],words[2]])
            if words[0] == 'ADD':
                words[-1] = 1
            else:
                words[-1] = 0
            results.append(words)
        # results.append('//////aaaa/////')
        # results.append(cursor.execute("SELECT `Title` FROM `mainapp_files` WHERE Title = %s",['txt1']))
        cursor.execute("INSERT INTO `mainapp_files`(`Title`) VALUES (%s)", [str(File)])
        context = {'files': results, 'readers': [request.FILES["file"]]}
        return render(request, 'error_page.html', context)
    else:
        form = AddFileForm()
        return render(request, 'add_file_form.html', {'form': form})

def search_path(request):


    # Этапы разработки:
    # 1)Сделать функцию для записи в древо(НУЖНО КАК-ТО ПОНЯТЬ КУДА ЗАПИСЫВАТЬ(КООРДИНАТЫ))
    # 2)Сделать функцию самого построения древа, которая на данные будет вызывать функцию заполнения
    # 3)Сделать функцию парса древа, которая будет понимать,что ветка тупиковая.
    # 4)
    # 



    end_point = [6] #временная задана так переменная, потом получать из формы поста.
    start_point = [] 
    global all_points
    global routes_tree
    all_points = [end_point]
    cursor = connection.cursor()
    # "SELECT * FROM `schedules` WHERE RouteID IN (SELECT id FROM routes WHERE ArrivalAirportID = (SELECT id FROM airports WHERE IATACode = 'DOH'));"
    cursor.execute("SELECT * FROM `schedules` WHERE RouteID IN (SELECT id FROM routes WHERE ArrivalAirportID = %s);",[end_point]) #получение всех вылетов до нужной точки
    results = cursor.fetchall() #получаю запрос
    # здесь написать функцию для записи в древо!(не забыть ее вызвать первый раз вне функции построения древа)
    #ААААААААААААААААААААААААА!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!минус мозг!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #Приблизительный образ структуры древа {A:[SQL,{OBJ:[B:[SQL,{OBJ:[RES]],C:[SQL,OBJ:[D:[SQL,OBJ:[RES]],F:[SQL,OBJ:[0,0,0]]]]]}]} -только с {} НАКОСЯЧИЛ, НО ПРИМЕРНО ТАК
    def build_routes_tree(results,start_point): #функция должна вернуть древо всех потенциальных маршрутов(придумать как удалить тупиковые ветви(или сделать это в функции парса))
        for result in results:
            cursor.execute("SELECT DepartureAirportID FROM routes WHERE id = %s",[result[4]])
            points = cursor.fetchall() #я получил все аэропорты из которых можно прилетить в исходный и это массив массивов из одного элемента
            for point in points: #проверяю наличие таких аэропортов в точке вылета и что это не конечный аэропорт
                if point in all_points:
                    points.remove(point)
                if point = start_point:
                    #на этой строке запрос на получение всех расписаний, которые прилетают в этот аэропорт
                    #вызвать функцию build_routes_tree и передать в нее все расписания(учесть , что расписаний может и не быть)

                    #тут будет логика для если аэропорт является нужным нам точкой вылета
            if points != []: #проверка, что из этой точки вообще есть пути
                all_points.extend(points)

            else: #продумать логику, когда остается только точка вылета!!!!!!!!!!!!
                #логика закрытия ветки
                continue #если путей нет ветка зыкрывается
        return 
    
    #Тут дальше логика парса древа и построения цепочек полетов после вызова функции построения древа.


    context = {'files': results , 'readers':results2[0] } 
    return render(request, 'error_page.html', context) 
