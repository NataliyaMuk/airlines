from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import Users, Roles, Offices

class CustomUserCreationForm(UserCreationForm):
    RoleID = forms.ModelChoiceField(queryset=Roles.objects.filter(id=2), required=True)
    OfficeID = forms.ModelChoiceField(queryset=Offices.objects.all(), required=True)
    Email = forms.CharField(max_length=150, required=True)
    FirstName = forms.CharField(max_length=50, required=True)
    LastName = forms.CharField(max_length=50, required=True)
    Birthdate = forms.DateField(required=True)
    Active = forms.IntegerField(required=True)

    class Meta:
        model = Users
        fields = ['RoleID', 'Email', 'FirstName', 'LastName', 'OfficeID', 'Birthdate', 'Active']


class CustomAuthenticationForm(AuthenticationForm):
    # def confirm_login_allowed(self, user):
    #     if not user.is_active:
    #         raise forms.ValidationError(
    #             "Вы не можете войти, так как заблокированы админом."
    #         )
        

    class Meta:
        model = Users
        fields = ['Email', 'Password']
