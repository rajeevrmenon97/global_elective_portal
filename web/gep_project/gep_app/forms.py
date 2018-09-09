from django import forms
from django.forms import formset_factory
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.db.models import Q
from .models import Student, Course, Elective, Elective_Seats, Faculty, Department
from datetime import datetime
import json

class StudentAcademicsForm(forms.ModelForm):
	class Meta:
		model = Student
		fields = ['current_CGPA','next_semester','required_elective_count','core_slots','past_courses','submission_datetime']

	def __init__(self, *args, **kwargs):
		super(StudentAcademicsForm, self).__init__(*args, **kwargs)
		self.fields['current_CGPA'].widget.attrs.update({
				'placeholder': 'CGPA',
				'class': 'form-control',
			})
		self.fields['next_semester'].widget.attrs.update({
				'placeholder': 'Semester',
				'class': 'form-control',
			})
		self.fields['required_elective_count'].widget.attrs.update({
				'placeholder': 'Number of global electives to be taken',
				'class': 'form-control',
			})
		self.fields['past_courses'].widget.queryset = Course.objects.all().order_by('name')
		self.fields['past_courses'].widget.attrs.update({
				'placeholder': 'No courses choosen',
				'class': 'form-control',
			})
		self.fields['core_slots'].widget = forms.SelectMultiple(attrs={
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

	def clean_required_elective_count(self):
		required_elective_count = self.cleaned_data.get('required_elective_count')
		if required_elective_count is None:
			raise ValidationError(_('This field is required'), code='empty')
		return required_elective_count

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

class CourseCreationForm(forms.ModelForm):	
	class Meta:
		model = Course
		fields = ['course_id','name','dept','credits','pre_requisites','cot_requisite','cgpa_cutoff','mode_of_allotment']

	def __init__(self, *args, **kwargs):
		super(CourseCreationForm, self).__init__(*args, **kwargs)
		
		self.fields['course_id'].label = 'Course ID'
		self.fields['course_id'].widget.attrs.update({
				'placeholder': 'Course ID',
				'class': 'form-control',
           })
		self.fields['name'].label = 'Course Name'
		self.fields['name'].widget.attrs.update({
				'placeholder': 'Course Name',
				'class': 'form-control',
			})
		self.fields['dept'].label = 'Department'
		self.fields['dept'].widget.attrs.update({
				'class': 'form-control',
			})
		self.fields['credits'].label = 'Number of credits'
		self.fields['credits'].widget.attrs.update({
				'placeholder': 'Credits',
				'class': 'form-control',
			})
		self.fields['pre_requisites'].label = 'Pre requisites (If any)'
		self.fields['pre_requisites'].widget.attrs.update({
				'placeholder': 'Enter the pre requisites...',
				'class': 'form-control',
				'rows':'4',
			})
		self.fields['cot_requisite'].label = 'Consent Of Teacher required or not'
		self.fields['cot_requisite'].widget.attrs.update({
				'class': 'checkbox-big',
			})
		self.fields['cgpa_cutoff'].label = 'CGPA cutoff (If any)'
		self.fields['cgpa_cutoff'].widget.attrs.update({
				'placeholder': 'CGPA cutoff',
				'class': 'form-control',
			})
		self.fields['mode_of_allotment'].label = 'Mode of allotment'
		self.fields['mode_of_allotment'].widget.attrs.update({
				'class': 'form-control',
			})		

class ElectiveCreationForm(forms.ModelForm):	
	class Meta:
		model = Elective
		fields = ['course','slot','faculty']
	
	def __init__(self, *args, **kwargs):
		super(ElectiveCreationForm, self).__init__(*args, **kwargs)
		
		self.fields['slot'].label = 'Slot'
		self.fields['slot'].widget.attrs.update({
				'class': 'form-control',
           })
		self.fields['faculty'].queryset = Faculty.objects.all().order_by('name')
		self.fields['faculty'].label = 'Faculty'
		self.fields['faculty'].widget.attrs.update({
				'class': 'form-control',
			})

class ElectiveSeatsCreationForm(forms.Form):
	dept = forms.CharField(max_length=100)
	max_seats = forms.IntegerField(min_value=0)
		
	def __init__(self, *args, **kwargs):
		super(ElectiveSeatsCreationForm, self).__init__(*args, **kwargs)
		self.fields['max_seats'].label = 'Maximum Seats'
		self.fields['max_seats'].widget.attrs.update({
				'class': 'form-control',
           })
		self.fields['dept'].widget = forms.TextInput()
		self.fields['dept'].widget.attrs.update({
				'class': 'form-control',
				'readonly': True,
           })
		
	def clean_dept(self):
		dept = self.cleaned_data.get('dept')
		if dept in Department.objects.all():
			return dept
		else:
			raise ValidationError(_('Invalid department'), code='invalid')
		return None		
	
	def save(self, elective, commit=True):
		data = self.cleaned_data
		elective_seat = Elective_Seats(elective=elective,dept=data.get('dept'),max_seats=data.get('max_seats'))		
		if commit == True:
			elective_seat.save()
		return elective_seat