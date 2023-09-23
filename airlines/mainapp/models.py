from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


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

class Users(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    RoleID = models.IntegerField()
    Email = models.CharField(max_length=150, unique=True)
    FirstName = models.CharField(max_length=50, null=True)
    LastName = models.CharField(max_length=50)
    OfficeID = models.IntegerField(null=True) 
    Birthdate = models.DateField(null=True)
    Active = models.SmallIntegerField(null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'Email'

    def __str__(self):
        return self.Email