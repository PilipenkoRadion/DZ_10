from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class Step1Form(forms.Form):
    title = forms.CharField(max_length=20, label="Название книги")
    author = forms.CharField(label="Автор")
    price = forms.DecimalField(label="Цена")


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model  = CustomUser
        fields = ("username", "email", "password1", "password2")


class LoginForm(AuthenticationForm):
    pass