from django import forms
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from .models import Student
from .widgets import DropdownMultipleWidget

class StudentAcademicsForm(ModelForm):
    class Meta:
        model = Student
        fields = ('current_CGPA','next_semester','core_slots','no_of_global_electives')
        widgets = {
           'core_slots':DropdownMultipleWidget(attrs={'class':'form-check-input'},choices=Student.SLOT_CHOICES)
        }
        
    def clean_current_CGPA(self):
        clean_data = self.cleaned_data
        current_CGPA = clean_data.get('current_CGPA')
        if current_CGPA is None:
            raise ValidationError(_('This field is required'), code='empty')
        return clean_data

    def clean_no_of_global_electives(self):
        clean_data = self.cleaned_data
        no_of_global_electives = clean_data.get('no_of_global_electives')
        if no_of_global_electives is None:
            raise ValidationError(_('This field is required'), code='empty')
        return clean_data

    def clean_next_semester(self):
        clean_data = self.cleaned_data
        next_semester = clean_data.get('next_semester')
        if next_semester is None:
            raise ValidationError(_('This field is required'), code='empty')
        return clean_data

#    def clean_password(self):
#        cleaned_data = super().clean()
#        password = cleaned_data.get('password')
#        validate_password(password)
	
#    def clean(self):
#        cleaned_data = super().clean()
#        username = cleaned_data.get('username')
#        password = cleaned_data.get('password')
#        try:
#            student = Student.objects.get(roll_number=username,password=password)
#        except ObjectDoesNotExist:
#            error_msg = 'Invalid username or password'
#            self.add_error('username',error_msg)
#            self.add_error('password',error_msg)

#        return cleaned_data
