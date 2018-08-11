from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from .models import Student
from datetime import datetime

class StudentAcademicsForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name','user','current_CGPA','next_semester','no_of_global_electives','core_slots','submission_datetime']

    def __init__(self, *args, **kwargs):
        super(StudentAcademicsForm, self).__init__(*args, **kwargs)
        self.fields['user'].widget = forms.TextInput(attrs={
                'readonly': True,
                'class': 'form-control',
            })
        self.fields['name'].widget.attrs.update({
                'readonly': True,
                'class': 'form-control',
           }) 
        self.fields['current_CGPA'].widget.attrs.update({
                'placeholder': 'CGPA',
                'class': 'form-control',
            })        
        self.fields['next_semester'].widget.attrs.update({
                'placeholder': 'Semester',
                'class': 'form-control',
            })
        self.fields['no_of_global_electives'].widget.attrs.update({
                'placeholder': 'Number of global electives',
                'class': 'form-control',
            })
        self.fields['core_slots'].widget = forms.SelectMultiple(attrs={
                'placeholder': 'No slots chosen',
                'class': 'form-control',
            },choices=self.Meta.model.SLOT_CHOICES)
 
    def clean_current_CGPA(self):
        current_CGPA = self.cleaned_data.get('current_CGPA')
        if current_CGPA is None:
            raise ValidationError(_('This field is required'), code='empty')
        return current_CGPA

    def clean_next_semester(self):
        next_semester = self.cleaned_data.get('next_semester')
        if next_semester is None:
            raise ValidationError(_('This field is required'), code='empty')
        return next_semester

    def clean_no_of_global_electives(self):
        no_of_global_electives = self.cleaned_data.get('no_of_global_electives')
        if no_of_global_electives is None:
            raise ValidationError(_('This field is required'), code='empty')
        return no_of_global_electives

    def clean_submission_datetime(self):
        submission_datetime = datetime.now()
        return submission_datetime

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
