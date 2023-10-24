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
from .models import Users, Roles, Schedules, Airports, ReportMay, ReportJune, ReportJuly
import json
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.db.models import F, ExpressionWrapper, fields
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.conf import settings
import os
from django.db.models import Count

from mainapp import models



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




def view_reports_summary(request):
    count_male = ReportMay.objects.filter(gender="M").aggregate(count_male=Count("gender"))['count_male'] + ReportJune.objects.filter(gender="M").aggregate(count_male=Count("gender"))['count_male'] + ReportJuly.objects.filter(gender="M").aggregate(count_male=Count("gender"))['count_male']
    count_female = ReportMay.objects.filter(gender="F").aggregate(count_female=Count("gender"))['count_female'] + ReportJune.objects.filter(gender="F").aggregate(count_female=Count("gender"))['count_female'] + ReportJuly.objects.filter(gender="F").aggregate(count_female=Count("gender"))['count_female']
    count_age18_24 = ReportMay.objects.filter(age__gte=18, age__lte=24).aggregate(count_age18_24=Count('age'))['count_age18_24'] + ReportJune.objects.filter(age__gte=18, age__lte=24).aggregate(count_age18_24=Count('age'))['count_age18_24'] + ReportJuly.objects.filter(age__gte=18, age__lte=24).aggregate(count_age18_24=Count('age'))['count_age18_24']
    count_age25_39 = ReportMay.objects.filter(age__gte=25, age__lte=39).aggregate(count_age25_39=Count('age'))['count_age25_39'] + ReportJune.objects.filter(age__gte=25, age__lte=39).aggregate(count_age25_39=Count('age'))['count_age25_39'] + ReportJuly.objects.filter(age__gte=25, age__lte=39).aggregate(count_age25_39=Count('age'))['count_age25_39']
    count_age40_59 = ReportMay.objects.filter(age__gte=40, age__lte=59).aggregate(count_age40_59=Count('age'))['count_age40_59'] + ReportJune.objects.filter(age__gte=40, age__lte=59).aggregate(count_age40_59=Count('age'))['count_age40_59'] + ReportJuly.objects.filter(age__gte=40, age__lte=59).aggregate(count_age40_59=Count('age'))['count_age40_59']
    count_age60 = ReportMay.objects.filter(age__gte=60).aggregate(count_age60=Count('age'))['count_age60'] + ReportJune.objects.filter(age__gte=60).aggregate(count_age60=Count('age'))['count_age60'] + ReportJuly.objects.filter(age__gte=60).aggregate(count_age60=Count('age'))['count_age60']
    count_economy = ReportMay.objects.filter(cabintype="Economy").aggregate(count_economy=Count("cabintype"))['count_economy'] + ReportJune.objects.filter(cabintype="Economy").aggregate(count_economy=Count("cabintype"))['count_economy'] + ReportJuly.objects.filter(cabintype="Economy").aggregate(count_economy=Count("cabintype"))['count_economy']
    count_business = ReportMay.objects.filter(cabintype="Business").aggregate(count_business=Count("cabintype"))['count_business'] + ReportJune.objects.filter(cabintype="Business").aggregate(count_business=Count("cabintype"))['count_business'] + ReportJuly.objects.filter(cabintype="Business").aggregate(count_business=Count("cabintype"))['count_business']
    count_first = ReportMay.objects.filter(cabintype="First").aggregate(count_first=Count("cabintype"))['count_first'] + ReportJune.objects.filter(cabintype="First").aggregate(count_first=Count("cabintype"))['count_first'] + ReportJuly.objects.filter(cabintype="First").aggregate(count_first=Count("cabintype"))['count_first']
    count_auh = ReportMay.objects.filter(arrival="AUH").aggregate(count_auh=Count("arrival"))['count_auh'] + ReportJune.objects.filter(arrival="AUH").aggregate(count_auh=Count("arrival"))['count_auh'] + ReportJuly.objects.filter(arrival="AUH").aggregate(count_auh=Count("arrival"))['count_auh']
    count_bah = ReportMay.objects.filter(arrival="BAH").aggregate(count_bah=Count("arrival"))['count_bah'] + ReportJune.objects.filter(arrival="BAH").aggregate(count_bah=Count("arrival"))['count_bah'] + ReportJuly.objects.filter(arrival="BAH").aggregate(count_bah=Count("arrival"))['count_bah']
    count_doh = ReportMay.objects.filter(arrival="DOH").aggregate(count_doh=Count("arrival"))['count_doh'] + ReportJune.objects.filter(arrival="DOH").aggregate(count_doh=Count("arrival"))['count_doh'] + ReportJuly.objects.filter(arrival="DOH").aggregate(count_doh=Count("arrival"))['count_doh']
    count_ryu = ReportMay.objects.filter(arrival="RYU").aggregate(count_ryu=Count("arrival"))['count_ryu'] + ReportJune.objects.filter(arrival="RYU").aggregate(count_ryu=Count("arrival"))['count_ryu'] + ReportJuly.objects.filter(arrival="RYU").aggregate(count_ryu=Count("arrival"))['count_ryu']
    count_cai = ReportMay.objects.filter(arrival="CAI").aggregate(count_cai=Count("arrival"))['count_cai'] + ReportJune.objects.filter(arrival="CAI").aggregate(count_cai=Count("arrival"))['count_cai'] + ReportJuly.objects.filter(arrival="CAI").aggregate(count_cai=Count("arrival"))['count_cai']

    context = {'count_male':count_male, 'count_female':count_female,  'count_age18_24':count_age18_24, 'count_age25_39':count_age25_39, 'count_age40_59':count_age40_59, 'count_age60':count_age60, 'count_economy':count_economy, 'count_business':count_business, 'count_first':count_first, 'count_auh':count_auh, 'count_bah':count_bah, 'count_doh':count_doh, 'count_ryu':count_ryu, 'count_cai':count_cai}                                                        

    return render(request, 'reports_summary.html', context) 





def question_search_data(question, model_name, selected_age, selected_gender):
    dict_of_questions_data = {}


    for i in range(1, 8): #оценка от 1 до 7

        dict_of_answer = {}

        if (selected_age):
            if (selected_age == '18'):
                count_total = getattr(models, model_name).objects.filter(**{question: i}, age__gte=18, age__lte=24).aggregate(count_total=Count(question))['count_total']
            if (selected_age == '25'):
                count_total = getattr(models, model_name).objects.filter(**{question: i}, age__gte=25, age__lte=39).aggregate(count_total=Count(question))['count_total']
            if (selected_age == '40'):
                count_total = getattr(models, model_name).objects.filter(**{question: i}, age__gte=40, age__lte=59).aggregate(count_total=Count(question))['count_total']
            if (selected_age == '60'):  
                count_total = getattr(models, model_name).objects.filter(**{question: i}, age__gte=60).aggregate(count_total=Count(question))['count_total']

        elif (selected_gender):
            count_total = getattr(models, model_name).objects.filter(**{question: i}, gender=selected_gender).aggregate(count_total=Count(question))['count_total']
       
        elif (selected_gender and selected_age):
            print(selected_age)
            print(selected_gender)

            if (selected_age == '18'):
                count_total = getattr(models, model_name).objects.filter(**{question: i}, age__gte=18, age__lte=24, gender=selected_gender).aggregate(count_total=Count(question))['count_total']
            if (selected_age == '25'):
                count_total = getattr(models, model_name).objects.filter(**{question: i}, age__gte=25, age__lte=39, gender=selected_gender).aggregate(count_total=Count(question))['count_total']
            if (selected_age == '40'):
                count_total = getattr(models, model_name).objects.filter(**{question: i}, age__gte=40, age__lte=59, gender=selected_gender).aggregate(count_total=Count(question))['count_total']
            if (selected_age == '60'):  
                count_total = getattr(models, model_name).objects.filter(**{question: i}, age__gte=60, gender=selected_gender).aggregate(count_total=Count(question))['count_total']

        else: 
            count_total = getattr(models, model_name).objects.filter(**{question: i}).aggregate(count_total=Count(question))['count_total']
        # count_total = getattr(models, model_name).objects.filter(**{question: i}).aggregate(count_total=Count(question))['count_total']
       
        count_male = getattr(models, model_name).objects.filter(**{question: i}, gender="M").aggregate(count_male=Count("gender"))['count_male']
        count_female = getattr(models, model_name).objects.filter(**{question: i}, gender="F").aggregate(count_female=Count("gender"))['count_female']
        count_age18_24 = getattr(models, model_name).objects.filter(**{question: i}, age__gte=18, age__lte=24).aggregate(count_age18_24=Count('age'))['count_age18_24']
        count_age25_39 = getattr(models, model_name).objects.filter(**{question: i}, age__gte=25, age__lte=39).aggregate(count_age25_39=Count('age'))['count_age25_39']
        count_age40_59 = getattr(models, model_name).objects.filter(**{question: i}, age__gte=40, age__lte=59).aggregate(count_age40_59=Count('age'))['count_age40_59']
        count_age60 = getattr(models, model_name).objects.filter(**{question: i}, age__gte=60).aggregate(count_age60=Count('age'))['count_age60']
        count_economy = getattr(models, model_name).objects.filter(**{question: i}, cabintype="Economy").aggregate(count_economy=Count("cabintype"))['count_economy']
        count_business = getattr(models, model_name).objects.filter(**{question: i}, cabintype="Business").aggregate(count_business=Count("cabintype"))['count_business']
        count_first = getattr(models, model_name).objects.filter(**{question: i}, cabintype="First").aggregate(count_first=Count("cabintype"))['count_first']
        count_auh = getattr(models, model_name).objects.filter(**{question: i}, arrival="AUH").aggregate(count_auh=Count("arrival"))['count_auh']
        count_bah = getattr(models, model_name).objects.filter(**{question: i}, arrival="BAH").aggregate(count_bah=Count("arrival"))['count_bah']
        count_doh = getattr(models, model_name).objects.filter(**{question: i}, arrival="DOH").aggregate(count_doh=Count("arrival"))['count_doh']
        count_ryu = getattr(models, model_name).objects.filter(**{question: i}, arrival="RYU").aggregate(count_ryu=Count("arrival"))['count_ryu']
        count_cai = getattr(models, model_name).objects.filter(**{question: i}, arrival="CAI").aggregate(count_cai=Count("arrival"))['count_cai']

        # if (count_total):
        if 'count_total' in locals():
            dict_of_answer['count_total'] = count_total

        dict_of_answer['count_male'] = count_male
        dict_of_answer['count_female'] = count_female
        dict_of_answer['count_age18_24'] = count_age18_24
        dict_of_answer['count_age25_39'] = count_age25_39
        dict_of_answer['count_age40_59'] = count_age40_59
        dict_of_answer['count_age60'] = count_age60
        dict_of_answer['count_economy'] = count_economy
        dict_of_answer['count_business'] = count_business
        dict_of_answer['count_first'] = count_first
        dict_of_answer['count_auh'] = count_auh
        dict_of_answer['count_bah'] = count_bah
        dict_of_answer['count_doh'] = count_doh
        dict_of_answer['count_ryu'] = count_ryu
        dict_of_answer['count_cai'] = count_cai    

        dict_of_questions_data[i] = dict_of_answer

    return dict_of_questions_data
    

def view_reports_detailed(request):

    selected_month = "ReportMay"

    selected_age = '18'
    selected_gender ='M'

    if request.method == 'GET':
        if (isinstance(request.GET.get('month'), str)): #является ли selected_month строкой
            selected_month = request.GET.get('month')
        if (isinstance(request.GET.get('age'), str)): #является ли selected_age строкой
            selected_age = request.GET.get('age')
        if (isinstance(request.GET.get('gender'), str)): #является ли selected_gender строкой
            selected_gender = request.GET.get('gender')


    dict_of_question_data_1 = question_search_data('q1', selected_month, selected_age, selected_gender)
    dict_of_question_data_2 = question_search_data('q2', selected_month, selected_age, selected_gender)
    dict_of_question_data_3 = question_search_data('q3', selected_month, selected_age, selected_gender)
    dict_of_question_data_4 = question_search_data('q4', selected_month, selected_age, selected_gender)

    context = {'dict_of_question_data_1':dict_of_question_data_1.values(), 'dict_of_question_data_2':dict_of_question_data_2.values(), 'dict_of_question_data_3':dict_of_question_data_3.values(), 'dict_of_question_data_4':dict_of_question_data_4.values()}

    return render(request, 'reports_detailed.html', context)









def search_path(request):


    # Этапы разработки:
    # 1)Сделать функцию для записи в древо(НУЖНО КАК-ТО ПОНЯТЬ КУДА ЗАПИСЫВАТЬ(КООРДИНАТЫ))
    # 2)Сделать функцию самого построения древа, которая на данные будет вызывать функцию заполнения
    # 3)Сделать функцию парса древа, которая будет понимать,что ветка тупиковая.
    # 



    end_point = [6] #временная задана так переменная, потом получать из формы поста.
    start_point = [3] 
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
    # здесь написать функцию для записи в древо!(не забыть ее вызвать первый раз вне функции построения древа)
    #ААААААААААААААААААААААААА!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!минус мозг!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #Приблизительный образ это объект flight_route,хранящий sql и массив такихже объектов, из которых в него можно прилететь
    all_flights = [] #все полеты

    def build_routes_tree(flight_obj,all_points): #функция должна вернуть древо всех потенциальных маршрутов(придумать как удалить тупиковые ветви(или сделать это в функции парса))
        all_ways=[] #тут я собираю массив всех маршрутов до точки
        # routes_tree.append(flight_route())
        cursor.execute("SELECT DepartureAirportID FROM routes WHERE id = %s",[flight_obj.sql[4]])
        points_list = cursor.fetchall() #я получил все аэропорты из которых можно прилетить в исходный и это массив массивов из одного элемента
        points = []
        for point_list in points_list:
            points.append(point_list[0])
        if not(points):
            return [flight_route([False],[False,'1er'])]
        for point in points: #проверяю наличие таких аэропортов в точке вылета и что это не конечный аэропорт и заполняю аэропорты отправления
            if point == start_point[0]:
                cursor.execute("SELECT * FROM `schedules` WHERE RouteID IN (SELECT id FROM routes WHERE ArrivalAirportID = %s) and `Date` <= %s and IF(`Date` = %s,SEC_TO_TIME(HOUR(Time)*3600+MINUTE(Time)*60+SEC_TO_TIME((SELECT FlightTime FROM routes WHERE id = 11)*60)) <= %s,1)",[point,flight_obj.sql[1],flight_obj.sql[1],flight_obj.sql[2]]) #подучать над ArrivalAirportID
                ways = cursor.fetchall()
                for way in ways: #перебераю все пути отправления , загоняю в объекты , а потом запихиваю в массив
                    flight_obj = flight_route(way,[True])
                    all_ways.append(flight_obj) #собираем все пути, которые потом будут лежать в объекте.
                return all_ways
                # cursor.execute("SELECT DepartureAirportID FROM routes WHERE id = %s",[result[4]])
                #на этой строке запрос на получение всех расписаний, которые прилетают в этот аэропорт
                #вызвать функцию build_routes_tree и передать в нее все расписания(учесть , что расписаний может и не быть)
            if point in all_points:
                points.remove(point)#если уже есть точка в списке , то мы ее удаляем и переходим к следующей точке
                if points == []:
                    return [flight_route([False],[False,'2er',all_points])]
                continue
            # return (point,all_points,all_points.append(flight_obj.sql[0]),points)
            all_points.append(point)
            cursor.execute("SELECT * FROM `schedules` WHERE RouteID IN (SELECT id FROM routes WHERE ArrivalAirportID = %s) and `Date` <= %s and IF(`Date` = %s,SEC_TO_TIME(HOUR(Time)*3600+MINUTE(Time)*60+SEC_TO_TIME((SELECT FlightTime FROM routes WHERE id = 11)*60)) <= %s,1)",[point,flight_obj.sql[1],flight_obj.sql[1],flight_obj.sql[2]]) #Получаем все расписания , с учетом, что рейс прилетает в аэропорт раньше, чем отлетает до нужного
            # ("SELECT * FROM `schedules` WHERE RouteID IN (SELECT id FROM routes WHERE ArrivalAirportID = (SELECT DepartureAirportID FROM routes WHERE id = %s)) and Date <= %s and IF(Date = %s,SEC_TO_TIME(HOUR(Time)*3600+MINUTE(Time)*60+SEC_TO_TIME((SELECT FlightTime FROM routes WHERE id = 11)*60)) <= %s,1)",[result[4],result[1],result[1],]) сохранить на всякий
            ways = cursor.fetchall() #получаю все маршруты из данного аэропорта
            if ways == ():
                return [flight_route([False],[False,'3er',all_points])]
            # return [point,"TTTT",flight_obj.sql]
            for way in ways: #перебераю все пути отправления , загоняю в объекты , а потом запихиваю в массив
                flight_obj = flight_route(way,[])
                flight_obj.points = build_routes_tree(flight_obj,all_points) #вызываем рекрсивно функцию для заполения массивов
                all_ways.append(flight_obj) #собираем все пути, которые потом будут лежать в объекте.
        
        return all_ways

    for result in results: #перебираю все стартовые расписания
        flight_obj = flight_route(result,[]) #иничу базовые объекты расписания
        flight_obj.points = build_routes_tree(flight_obj,[end_point[0]])
        all_flights.append(flight_obj) #заполняю полеты, вызывая рекурсивную функцию (.points[0].points)


    def parse_tree(flight):
        schedules = []
        for point in flight.points:
            try:
                if type(point) != type(False):
                    if point.points[0] == True:
                        schedules.append([flight.sql])
                    if point.points[0] == False:
                        schedules.append(["False"])
                    return schedules
            except:
                schedules2 = parse_tree(point)
                schedules3 = []
                for schedule2 in schedules2:
                    schedule2.append(point.sql)
                    schedules3.append(schedule2)
                schedules.extend(schedules3)
        schedules.append(flight.sql)        
        return schedules
     
    # Парсинг древа возвращает массив массивов все доступных вариантов.
    shedules = []
    for flight in all_flights:
        shedules.extend(parse_tree(flight))
    
            
    # all_flights
    # all_flights[0].points
    # all_flights[0].points[0].points
    # [all_flights[0].points[0].points[0]]
    context = {'files': [all_flights[1].points[0].points[0].points] , 'readers':["readers"] } 
    return render(request, 'error_page.html', context) 

# SELECT * FROM `schedules` WHERE RouteID IN (SELECT id FROM routes WHERE ArrivalAirportID = (SELECT DepartureAirportID FROM routes WHERE id = 11)) and Date <= '2018-10-28' and IF(Date >= '2017-10-27',SEC_TO_TIME(Time+SEC_TO_TIME((SELECT FlightTime FROM routes WHERE id = 11)*60)) <= '17:00:00',1)

# SELECT * FROM `schedules` WHERE RouteID IN (SELECT id FROM routes WHERE ArrivalAirportID = (SELECT DepartureAirportID FROM routes WHERE id = 11)) and Date <= '2018-10-28' and IF(Date = '2017-10-27',SEC_TO_TIME(HOUR(Time)*3600+MINUTE(Time)*60+SEC_TO_TIME((SELECT FlightTime FROM routes WHERE id = 11)*60)) <= '24:00:00',1)

