from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from datetime import datetime


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
    RoleID = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column='RoleID')
    Email = models.CharField(max_length=150, unique=True)
    FirstName = models.CharField(max_length=50, null=True)
    LastName = models.CharField(max_length=50)
    OfficeID = models.ForeignKey(Offices, on_delete=models.CASCADE, null=True, db_column='OfficeID')
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
    user =  models.ForeignKey('Users',on_delete=models.CASCADE,related_name='user')
    session_start = models.DateField()
    last_confirmation = models.DateField(null=True)
    error_status = models.CharField(max_length=50,default="Lost connection.",null=True)
    session_end	 = models.DateField(null=True) 
    status = models.CharField(null=True,max_length=1) 