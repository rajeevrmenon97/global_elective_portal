from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.db.models import Q
from .models import Student, Course, Elective, Elective_Seats, Faculty
from datetime import datetime

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
		fields = ['course_id','name','credits','pre_requisites','cot_requisite','cgpa_cutoff','mode_of_allotment']

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
		
	def save(self, dept, commit=True):
		self.instance.dept = dept
		return super().save()
		

class AddElectiveForm(forms.Form):
	elective_data = forms.CharField(max_length=5000, attrs={
				'class': 'form-control',
				'required': True,
			})
	
	def clean_elective_data(self):
		elective_data = self.cleaned_data.get('elective_data')
		try:
			json_data = json.loads(elective_data) 
		except:
			raise forms.ValidationError("Invalid data")

		for slot_data in json_data:
			slot = slot_data['slot']
			faculty = slot_data['faculty']
			print(slot)
			print(faculty)
			for dept, max_seat in max_seats.items():
				print(dept)
				print(max_seat)
		return elective_data
		
#	def save(self, course, commit=True):
#		self.instance.course = course
#		return super().save()

		

class ElectiveCreationForm(forms.ModelForm):	
	class Meta:
		model = Elective
		fields = ['slot','faculty']

	def __init__(self, *args, **kwargs):
		super(ElectiveCreationForm, self).__init__(*args, **kwargs)
		
		self.fields['slot'].widget.attrs.update({
				'class': 'form-control',
           })
		self.fields['faculty'].queryset = Faculty.objects.all().order_by('name')
		self.fields['faculty'].widget.attrs.update({
				'class': 'form-control',
			})
		
	def save(self, course, commit=True):
		self.instance.course = course
		return super().save()


class ElectiveSeatsCreationForm(forms.ModelForm):	
	class Meta:
		model = Elective_Seats
		fields = ['dept','max_seats']

	def __init__(self, *args, **kwargs):
		super(ElectiveSeatsCreationForm, self).__init__(*args, **kwargs)
		
		self.fields['dept'].widget.attrs.update({
				'class': 'form-control',
           })
		self.fields['max_seats'].widget.attrs.update({
				'class': 'form-control',
			})
		
	def save(self, elective, commit=True):
		self.instance.elective = elective
		return super().save()
	
#class AddElectiveForm(forms.Form):
#	slots = forms.SelectMultiple(attrs={
#				'class': 'form-control',
#				'required': True,
#			},choices=Elective.SLOT_CHOICES)
#	max_seats = 
	
	
#class ElectiveForm(MultiModelForm):
#	form_classes = {
#        'course': CourseCreationForm,
#        'elective': ElectiveCreationForm,
#        'elective_seat': ElectiveSeatForm,
#    }
#	
#		objects = super(ElectiveForm, self).save(commit=False)
#
#		if commit:
#			course = objects['course']
#			user.save()
#			for elective in objects['electives']:
#				elective.course = course
#				elective.save()
#				for elective_seat in objects['elective_seats']:
#					elective_seat.elective = elective
#					elective_seat.max_seats = elective_seat.max_seats / objects['electives'].length()
#					elective_seat.save()
#		return objects