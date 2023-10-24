from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import math

from datetime import datetime ,timezone
# from django.db import migrations


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Countries(models.Model):
    id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)

    class Meta:
        managed = False  # Это указывает Django не создавать эту таблицу
        db_table = 'countries'

    def __str__(self):
        return self.Name


class Roles(models.Model):
    id = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=50)

    class Meta:
        managed = False  # Это указывает Django не создавать эту таблицу
        db_table = 'roles'

    def __str__(self):
        return self.Title


class Offices(models.Model):
    id = models.AutoField(primary_key=True)
    CountryID = models.ForeignKey(Countries, on_delete=models.CASCADE, db_column='CountryID')
    Title = models.CharField(max_length=50)
    Phone = models.CharField(max_length=50)
    Contact = models.CharField(max_length=250)

    class Meta:
        managed = False  # Это указывает Django не создавать эту таблицу
        db_table = 'offices'

    def __str__(self):
        return self.Title


class Users(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    RoleID = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column='RoleID', default=0)
    Email = models.CharField(max_length=150, unique=True)
    FirstName = models.CharField(max_length=50, null=True)
    LastName = models.CharField(max_length=50)
    OfficeID = models.ForeignKey(Offices, on_delete=models.CASCADE, null=True, db_column='OfficeID', default=1)
    Birthdate = models.DateField(null=True)
    Active = models.SmallIntegerField(null=True)

    # Метод для вычисления возраста
    def calculate_age(self):
        today = datetime.today()
        dob = self.Birthdate
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age

    objects = CustomUserManager()

    USERNAME_FIELD = 'Email'

    def __str__(self):
        return self.Email


class Sessions(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='user')
    session_start = models.DateTimeField()
    last_confirmation = models.DateTimeField(null=True)
    error_status = models.CharField(max_length=50, default="Lost connection.", null=True)
    session_end = models.DateTimeField(null=True)
    status = models.CharField(null=True, max_length=1)


class AddedTables(models.Model):
    id = models.AutoField(primary_key=True)
    table_name = models.CharField(max_length=500)


class Aircrafts(models.Model):
    ID = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    MakeModel = models.CharField(max_length=10)
    TotalSeats = models.IntegerField(max_length=11)
    EconomySeats = models.IntegerField(max_length=11)
    BusinessSeats = models.IntegerField(max_length=11)

    class Meta:
        managed = False  # Это указывает Django не создавать эту таблицу
        db_table = 'aircrafts'

    def __str__(self):
        return self.Name


class Airports(models.Model):
    ID = models.AutoField(primary_key=True)
    CountryID = models.IntegerField(max_length=11)
    IATACode = models.CharField(max_length=3)
    Name = models.CharField(max_length=50, null=True)

    class Meta:
        managed = False  # Это указывает Django не создавать эту таблицу
        db_table = 'airports'

    def __str__(self):
        return self.IATACode


class Routes(models.Model):
    ID = models.AutoField(primary_key=True)
    DepartureAirportID = models.ForeignKey(Airports, on_delete=models.CASCADE, db_column='DepartureAirportID',
                                           default=0, related_name='departure_routes')
    ArrivalAirportID = models.ForeignKey(Airports, on_delete=models.CASCADE, db_column='ArrivalAirportID', default=0,
                                         related_name='arrival_routes')
    Distance = models.IntegerField(max_length=11)
    FlightTime = models.IntegerField(max_length=11)

    class Meta:
        managed = False  # Это указывает Django не создавать эту таблицу
        db_table = 'routes'

    def __str__(self):
        return f"{self.DepartureAirportID} -> {self.ArrivalAirportID}"


class Schedules(models.Model):
    ID = models.AutoField(primary_key=True)
    Date = models.DateField()
    Time = models.TimeField()

    AircraftID = models.ForeignKey(Aircrafts, on_delete=models.CASCADE, db_column='AircraftID', default=0)
    RouteID = models.ForeignKey(Routes, on_delete=models.CASCADE, db_column='RouteID', default=0)

    EconomyPrice = models.FloatField()
    Confirmed = models.SmallIntegerField()
    FlightNumber = models.CharField(max_length=10, null=True)

    # Метод для вычисления цены бизнес класса
    def calculate_business_price(self):
        econom_price = self.EconomyPrice
        business_price = math.floor(econom_price + econom_price * 0.35)
        return business_price

    def calculate_first_class_price(self):
        econom_price = self.EconomyPrice
        first_class_price = math.floor(
            (econom_price + econom_price * 0.35) + (econom_price + econom_price * 0.35) * 0.3)
        return first_class_price

    class Meta:
        managed = False  # Это указывает Django не создавать эту таблицу
        db_table = 'schedules'

    def __str__(self):
        return self.ID


class Files(models.Model):
    id = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=50)


class ReportMay(models.Model):
    departure = models.CharField(max_length=10)
    arrival = models.CharField(max_length=10)
    age =  models.CharField(default=0, max_length=30)
    gender = models.CharField(max_length=10)
    cabintype = models.CharField(max_length=30)
    q1 = models.IntegerField(default=0)
    q2 = models.IntegerField(default=0)
    q3 = models.IntegerField(default=0)
    q4 = models.IntegerField(default=0)


class ReportJune(models.Model):
    departure = models.CharField(max_length=10)
    arrival = models.CharField(max_length=10)
    age =  models.CharField(default=0, max_length=30)
    gender = models.CharField(max_length=10)
    cabintype = models.CharField(max_length=30)
    q1 = models.IntegerField(default=0)
    q2 = models.IntegerField(default=0)
    q3 = models.IntegerField(default=0)
    q4 = models.IntegerField(default=0)


class ReportJuly(models.Model):
    departure = models.CharField(max_length=10)
    arrival = models.CharField(max_length=10)
    age =  models.CharField(default=0, max_length=30)
    gender = models.CharField(max_length=10)
    cabintype = models.CharField(max_length=30)
    q1 = models.IntegerField(default=0)
    q2 = models.IntegerField(default=0)
    q3 = models.IntegerField(default=0)
    q4 = models.IntegerField(default=0)
