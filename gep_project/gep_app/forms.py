from django import forms
from django.forms import ModelForm
from .models import Student
from django.core.exceptions import ObjectDoesNotExist

class LoginForm(forms.Form):
    username = forms.CharField(required=True,max_length=10)
    password = forms.CharField(required=True,max_length=100)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        try:
            student = Student.objects.get(roll_number=username,password=password)
        except ObjectDoesNotExist:
            error_msg = 'Invalid username or password'
            self.add_error('username',error_msg)
            self.add_error('password',error_msg)

        return cleaned_data
