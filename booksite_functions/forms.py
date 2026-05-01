from django import forms

class Step1Form(forms.Form):
    title = forms.CharField(max_length=20, label="Название книги")
    author = forms.CharField(label="Автор")
    price = forms.DecimalField(label="Цена")