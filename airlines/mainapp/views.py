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
import datetime
import time 

import csv
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse



def user_session(request, email):
    cursor = connection.cursor()
    if request.method == 'GET':
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE mainapp_sessions SET status='1' WHERE status='0' and TIMESTAMPDIFF(SECOND,last_confirmation,NOW()) > 120")
        cursor.execute(
            "UPDATE mainapp_sessions SET last_confirmation=NOW() WHERE mainapp_sessions.status='0' and (SELECT id FROM mainapp_users WHERE email = %s) = user_id",
            [email])


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = CustomAuthenticationForm()


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


def search_path(request,end,start):

    # Этапы разработки:
    # 1)Сделать функцию для записи в древо(НУЖНО КАК-ТО ПОНЯТЬ КУДА ЗАПИСЫВАТЬ(КООРДИНАТЫ))
    # 2)Сделать функцию самого построения древа, которая на данные будет вызывать функцию заполнения
    # 3)Сделать функцию парса древа, которая будет понимать,что ветка тупиковая.
    # 


    if request.method == 'POST':
        end_point = [end] #временная задана так переменная, потом получать из формы поста.
        start_point = [start] 
    else:
        end_point = [6] #временная задана так переменная, потом получать из формы поста.
        start_point = [4] 
    global routes_tree
    routes_tree = []

    class flight_route: 
        def __init__(self,sql,points):
            self.sql = sql #сам маршрут расписание
            self.points = points #массив из объектов flight_route маршрутов из которых можно прилететь в данный маршрут

    cursor = connection.cursor()
    # "SELECT * FROM `schedules` WHERE RouteID IN (SELECT id FROM routes WHERE ArrivalAirportID = (SELECT id FROM airports WHERE IATACode = 'DOH'));"
    cursor.execute("SELECT * FROM `schedules` WHERE RouteID IN (SELECT id FROM routes WHERE ArrivalAirportID = %s);",[end_point[0]]) #получение всех вылетов до нужной точки
    
    results = cursor.fetchall() #получаю запрос
    # print("results",len(results))
    # здесь написать функцию для записи в древо!(не забыть ее вызвать первый раз вне функции построения древа)
    #ААААААААААААААААААААААААА!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!минус мозг!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #Приблизительный образ это объект flight_route,хранящий sql и массив такихже объектов, из которых в него можно прилететь
    all_flights = [] #все полеты

    def build_routes_tree(flight_obj,all_points): #функция должна вернуть древо всех потенциальных маршрутов(придумать как удалить тупиковые ветви(или сделать это в функции парса))
        all_ways=[] #тут я собираю массив всех маршрутов до точки
        # routes_tree.append(flight_route())
        cursor.execute("SELECT DepartureAirportID FROM routes WHERE id = %s",[flight_obj[4]])
        points_list = cursor.fetchall() #я получил все аэропорты из которых можно прилетить в исходный и это массив массивов из одного элемента
        points = []
        for point_list in points_list:
            points.append(point_list[0])
        # print("points",points,all_points)
        if not(points):
            return [flight_route([False,"er1"],[False])]
        # print("points",points,all_points)
        for point in points: #проверяю наличие таких аэропортов в точке вылета и что это не конечный аэропорт и заполняю аэропорты отправления
            if point == start_point[0]:
                return [flight_route([True],[True])]
            # print("AFTER START POINT")
            if point in all_points:
                points.remove(point)#если уже есть точка в списке , то мы ее удаляем и переходим к следующей точке
                if points == []:
                    # all_points.append(point)
                    return [flight_route([False,"er3"],[False])]
                continue
            # return (point,all_points,all_points.append(flight_obj.sql[0]),points)
            all_points.append(point)
            cursor.execute("SELECT * FROM `schedules` WHERE RouteID IN (SELECT id FROM routes WHERE ArrivalAirportID = %s) and `Date` <= %s and IF(`Date` = %s,SEC_TO_TIME(HOUR(Time)*3600+MINUTE(Time)*60+SEC_TO_TIME((SELECT FlightTime FROM routes WHERE id = 11)*60)) <= %s,1)",[point,flight_obj[1],flight_obj[1],flight_obj[2]]) #Получаем все расписания , с учетом, что рейс прилетает в аэропорт раньше, чем отлетает до нужного
            # ("SELECT * FROM `schedules` WHERE RouteID IN (SELECT id FROM routes WHERE ArrivalAirportID = (SELECT DepartureAirportID FROM routes WHERE id = %s)) and Date <= %s and IF(Date = %s,SEC_TO_TIME(HOUR(Time)*3600+MINUTE(Time)*60+SEC_TO_TIME((SELECT FlightTime FROM routes WHERE id = 11)*60)) <= %s,1)",[result[4],result[1],result[1],]) сохранить на всякий
            ways = cursor.fetchall() #получаю все маршруты из данного аэропорта
            if ways == ():
                return [flight_route([False,"er4"],[False])]
            # return [point,"TTTT",flight_obj.sql]

            # print("////////////////////////")
            # print(ways)
            # print("\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\")

            for way in ways: #перебераю все пути отправления , загоняю в объекты , а потом запихиваю в массив
                flight_obj2 = flight_route(way,[])
                # print(flight_obj,way)
                flight_obj2.points = build_routes_tree(flight_obj2.sql,all_points) #вызываем рекрсивно функцию для заполения массивов
                all_ways.append(flight_obj2) #собираем все пути, которые потом будут лежать в объекте.
        # print("all_ways",all_ways)
        return all_ways

    for result in results: #перебираю все стартовые расписания
        flight_obj = flight_route(result,[]) #иничу базовые объекты расписания
        flight_obj.points = build_routes_tree(flight_obj.sql,[])
        all_flights.append(flight_obj) #заполняю полеты, вызывая рекурсивную функцию (.points[0].points)
    # print("all_flights",len(all_flights))

    def parse_tree(flight,schedules1):
        # print("points",flight.points)
        # print("AAAAAAA")
        # print("MDA",flight.sql,flight.points)
        # if flight.points == []:
        #     return [False]
       
        schedules1=[]
        for point in flight.points:
            schedules2 = []
            # print("error point",point)
            if point == False:
                # print("ФОЛСА!",[flight.points])
                return [[flight.sql[0]]]
        # print("flight.points[0]",flight.points[0].points)
            if point == True:
                # print("ИСТИННО ТРУШНО")
                # print(flight.sql)
                return [[True]] #schedules1
            schedules2.extend(parse_tree(point,[]))
            # print("schedules2",schedules2)
            # print("ПОШЕЛ СЛЕДУЮЩИЙ!")
            # print(schedules2)
            # print("schedules2",schedules2)
            for schedule2 in schedules2:
                # print("schedule2",schedule2)
                schedule2=list(schedule2)

                # print("schedule2",schedule2)
                schedule2.append(point.sql)
                # print("schedule2_append",schedule2)
                # print("append",schedule2)
                schedules1.append(schedule2) #extend
            # print("schedules1FFFF",schedules1)
        # print("schedules1")
        # print(schedules1)
        return schedules1
     
    # Парсинг древа возвращает массив массивов все доступных вариантов.
    shedules = []
    # print("EEEEEE!")
    for flight in all_flights:
        # print("flight.sql",flight.sql)
        # print("PARSING!")
        res = parse_tree(flight,[])
        # print("res",res)
        if res == None:
            continue
        res = list(res)
        for i in range(len(res)-1):
            # print("flight.sql",flight.sql)
            res[i].append(flight.sql)
        shedules.extend(res)
        # print("shedules",shedules)
    # print("shedules",shedules)
            
    # all_flights
    # all_flights[0].points
    # all_flights[0].points[0].points
    # [all_flights[0].points[0].points[0]]
    # [all_flights[1].points[0].points[0].points]
    if request.method == 'POST':
        return shedules
    else:
        context = {'files': [shedules] , 'readers':["readers"] } 
        return render(request, 'error_page.html', context) 

@csrf_exempt
def search_flights(request):
    main_cursor = connection.cursor()
    airports = Airports.objects.all()
    if request.method == "POST":
        # print("HOHOHO")
        print("request.POST[display_three_days_outbound_checkbox]",request.POST.get('display_three_days_return_checkbox'))
        all_ways = search_path(request,int(request.POST['arrival_airport']),int(request.POST['departure_airport']))
        delta = datetime.timedelta(weeks = 0, days = 3, hours = 0, seconds = 0)
        print("delta",type(delta))
        # print(all_ways)
        # print("LEN:",len(all_ways))

        # print("str(request.POST['outbound'])",str(request.POST['outbound']))
        # print(type(datetime.datetime.strptime(request.POST['outbound'], '%Y-%m-%d')))

        if str(request.POST.get('display_three_days_outbound_checkbox')) == "yes":
            delta = datetime.timedelta(weeks = 0, days = 3, hours = 0, seconds = 0)
            start_data_outbound = datetime.datetime.strptime(request.POST['outbound'], '%Y-%m-%d') - delta
            end_data_outbound = datetime.datetime.strptime(request.POST['outbound'], '%Y-%m-%d') + delta
        else:
            data_outbound = request.POST['outbound']
            print("data_outbound",data_outbound)
        
        if str(request.POST.get('display_three_days_return_checkbox')) == "yes":
            delta = datetime.timedelta(weeks = 0, days = 3, hours = 0, seconds = 0)
            start_data_return = datetime.datetime.strptime(request.POST['return'], '%Y-%m-%d') - delta
            end_data_return = datetime.datetime.strptime(request.POST['return'], '%Y-%m-%d') + delta
        else:
            data_return = request.POST['return']
            print("data_return",data_return)



        paths_return = []
        paths_outbound=[]


        for ways in all_ways:
            if ways[0] == True:
                # ways = list(ways)
                ways.pop(0)
                ways.pop(0)
                # print("ways[0][1] == data_outbound",str(ways[0][1]) == data_outbound,"ways[0][1]",ways[0][1],"data_outbound",data_outbound)
                # print("type(ways[0][1])",type(ways[0][1]))
                if str(request.POST.get('display_three_days_outbound_checkbox')) == "yes":
                    # print("end_data.date",end_data.date())
                    # print("ways[0][1] > end_data.date()",ways[0][1] > end_data.date())
                    if ways[0][1] <= end_data_outbound.date() and ways[0][1] >= start_data_outbound.date():
                        parsed_ways = [airports[int(request.POST['departure_airport'])-2],airports[int(request.POST['arrival_airport'])-2],ways[0][1],ways[0][2]]
                        parsed_way = [[],0,[]]
                        for way in ways:
                            parsed_way[0].append(way[0])
                            parsed_way[2].append(way[-1])
                            # print("int(request.POST['fly_class']",request.POST['fly_class'])
                            # print("int(request.POST['fly_class']",int(request.POST['fly_class']))
                            parsed_way[1] += way[5]*float(request.POST['fly_class'])
                            parsed_way[1] = round(parsed_way[1],1)
                            print("parsed_way[1]",parsed_way[1])
                        parsed_ways.extend(parsed_way)
                        parsed_ways.append(len(ways))
                        paths_outbound.append(parsed_ways)
                    continue
                if str(ways[0][1]) == data_outbound:
                    parsed_ways = [airports[int(request.POST['departure_airport'])-2],airports[int(request.POST['arrival_airport'])-2],ways[0][1],ways[0][2]]
                    parsed_way = [[],0,[]]
                    for way in ways:
                        parsed_way[0].append(way[0])
                        parsed_way[2].append(way[-1])
                        # print("int(request.POST['fly_class']",request.POST['fly_class'])
                        # print("int(request.POST['fly_class']",int(request.POST['fly_class']))
                        parsed_way[1] += way[5]*float(request.POST['fly_class'])
                    parsed_ways.extend(parsed_way)
                    parsed_ways.append(len(ways))
                    paths_outbound.append(parsed_ways)

            else:
                continue
        if paths_outbound == []:
            paths_outbound.append("Маршрутов, удовлетворяющим вашим условиям не найдено.")
        
        if request.POST['return']:
            all_ways = search_path(request,int(request.POST['departure_airport']),int(request.POST['arrival_airport']))
            for ways in all_ways:
                if ways[0] == True:
                    # ways = list(ways)
                    ways.pop(0)
                    ways.pop(0)
                    # print("type(ways[0][1])",type(ways[0][1]))
                    if str(request.POST.get('display_three_days_return_checkbox')) == "yes":
                        # print("display_three_days_return_checkbox")
                        # print("end_data.date",end_data.date())
                        # print("ways[0][1] > end_data.date()",ways[0][1] > end_data.date())
                        if ways[0][1] <= end_data_return.date() and ways[0][1] >= start_data_return.date():
                            parsed_ways = [airports[int(request.POST['departure_airport'])-2],airports[int(request.POST['arrival_airport'])-2],ways[0][1],ways[0][2]]
                            parsed_way = [[],0,[]]
                            for way in ways:
                                # print("way[0]",way[0])
                                print("way[0]",way[0])
                                parsed_way[0].append(way[0])
                                # print("way[-1]",way[7])
                                print("way[7]",way[-1])
                                parsed_way[2].append(way[7])
                                # print("int(request.POST['fly_class']",request.POST['fly_class'])
                                # print("int(request.POST['fly_class']",int(request.POST['fly_class']))
                                parsed_way[1] += way[5]*float(request.POST['fly_class'])
                            parsed_ways.extend(parsed_way)
                            # print("parsed_ways]",parsed_ways)
                            parsed_ways.append(len(ways))
                            paths_return.append(parsed_ways)
                        continue
                    if str(ways[0][1]) == data_return:
                        parsed_ways = [airports[int(request.POST['departure_airport'])-2],airports[int(request.POST['arrival_airport'])-2],ways[0][1],ways[0][2]]
                        parsed_way = [[],0,[]]
                        for way in ways:
                            parsed_way[0].append(way[0])
                            parsed_way[2].append(way[-1])
                            # print("int(request.POST['fly_class']",request.POST['fly_class'])
                            # print("int(request.POST['fly_class']",int(request.POST['fly_class']))
                            parsed_way[1] += way[5]*float(request.POST['fly_class'])
                        parsed_ways.extend(parsed_way)
                        parsed_ways.append(len(ways))
                        paths_return.append(parsed_ways)

                else:
                    continue
            if paths_return == []:
                paths_return.append("Маршрутов, удовлетворяющим вашим условиям не найдено.")
        
        
        # print("paths_return:",paths_return)
        # print("paths_outbound:",paths_outbound)
        context = {'airports':airports,'paths_outbound':paths_outbound,"paths_return":paths_return} #'outbound_flight ':outbound_flight ,'return_flight ':return_flight 
        return render(request, 'search_flights.html', context) 
    else:
        context = {'airports':airports}
        return render(request, 'search_flights.html', context) 

@admin_required
def booking_confirmation(request):

    context = {'files': [shedules] , 'readers':["readers"] } 
    return render(request, 'error_page.html', context) 

