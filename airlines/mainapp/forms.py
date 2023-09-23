from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import Users

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Users
        fields = ['RoleID', 'Email', 'FirstName', 'LastName', 'OfficeID', 'Birthdate', 'Active']


class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = Users
        fields = ['Email', 'Password']