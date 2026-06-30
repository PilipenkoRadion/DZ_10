from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class Step1Form(forms.Form):
    title = forms.CharField(max_length=20, label=_("Book title"))
    author = forms.CharField(label=_("Author"))
    price = forms.DecimalField(label=_("Price"))


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_("Email"))

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password1", "password2")
        labels = {
            "username": _("Username"),
            "password1": _("Password"),
            "password2": _("Password confirmation"),
        }


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = _("Username")
        self.fields['password'].label = _("Password")