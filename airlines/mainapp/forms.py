from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import Users, Roles, Offices

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Users
        fields = ['RoleID', 'Email', 'FirstName', 'LastName', 'OfficeID', 'Birthdate', 'Active']


# class CustomUserCreationForm(UserCreationForm):
#     RoleID = forms.ModelChoiceField(queryset=Roles.objects.all()) 
#     OfficeID = forms.ModelChoiceField(queryset=Offices.objects.all())

#     Email = forms.CharField(max_length=150)
#     FirstName = forms.CharField(max_length=50, )
#     LastName = forms.CharField(max_length=50)
#     Birthdate = forms.DateField()
#     Active = forms.IntegerField()

#     class Meta:
#         model = Users
#         fields = ['RoleID', 'Email', 'FirstName', 'LastName', 'OfficeID', 'Birthdate', 'Active']


class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = Users
        fields = ['Email', 'Password']