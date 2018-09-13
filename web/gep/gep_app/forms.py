from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.db.models import Q
from .models import Student, Course, Elective, Elective_Seats, Faculty, Department
from django.contrib.auth import get_user_model

class UserForm(forms.ModelForm):
	"""Form for User"""
	class Meta:
		model = get_user_model()
		fields = ['username','password','email','role']

	def clean_email(self):
		"""Raise validation error if email is empty"""
		email = self.cleaned_data.get('email')
		if email is None:
			raise ValidationError(_('This field is required'), code='empty')
		return email
 
	def clean_role(self):
		"""Raise validation error if role is empty"""
		role = self.cleaned_data.get('role')
		if role is None:
			raise ValidationError(_('This field is required'), code='empty')
		return role
	
class DepartmentForm(forms.ModelForm):
	"""Form for Department"""
	class Meta:
		model = Department
		fields = ['user','name']

class StudentForm(forms.ModelForm):
	"""Form for Student"""
	class Meta:
		model = Student
		fields = ['user','name','date_of_birth','dept']

class FacultyForm(forms.ModelForm):
	"""Form for Faculty"""
	class Meta:
		model = Faculty	
		fields = ['user','name','dept']

class StudentAcademicsForm(forms.ModelForm):
	"""Form for the details submitted for FA validation"""
	class Meta:
		model = Student
		fields = ['FA','current_CGPA','next_semester','required_elective_count','core_slots','past_courses']

	def __init__(self, *args, **kwargs):
		super(StudentAcademicsForm, self).__init__(*args, **kwargs)
		
		if self.instance and self.instance.dept:
			self.fields['FA'].queryset = Faculty.objects.filter(dept=self.instance.dept).order_by('name')
		else:
			self.fields['FA'].queryset = Faculty.objects.all().order_by('name')

		self.fields['FA'].widget.attrs.update({
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
		
		self.fields['required_elective_count'].widget.attrs.update({
				'placeholder': 'Number of global electives to be taken',
				'class': 'form-control',
			})
		
		if self.instance and self.instance.dept:
			self.fields['past_courses'].queryset = Course.objects.filter(~Q(dept=self.instance.dept)).order_by('name')
		else:
			self.fields['past_courses'].queryset = Course.objects.all().order_by('name')
		self.fields['past_courses'].widget.attrs.update({
				'placeholder': 'No courses choosen',
				'class': 'form-control',
			})
		
		self.fields['core_slots'].widget = forms.SelectMultiple(attrs={
				'class': 'form-control',
			},choices=self.Meta.model.SLOT_CHOICES)
 
	def clean_FA(self):
		"""Raise validation error if FA is empty"""
		FA = self.cleaned_data.get('FA')
		if FA is None:
			raise ValidationError(_('This field is required'), code='empty')
		return FA
 
	def clean_current_CGPA(self):
		"""Raise validation error if current CGPA is empty"""
		current_CGPA = self.cleaned_data.get('current_CGPA')
		if current_CGPA is None:
			raise ValidationError(_('This field is required'), code='empty')
		return current_CGPA

	def clean_next_semester(self):
		"""Raise validation error if next semester is empty"""
		next_semester = self.cleaned_data.get('next_semester')
		if next_semester is None:
			raise ValidationError(_('This field is required'), code='empty')
		return next_semester

	def clean_required_elective_count(self):
		"""Raise validation error if required elective count is empty"""
		required_elective_count = self.cleaned_data.get('required_elective_count')
		if required_elective_count is None:
			raise ValidationError(_('This field is required'), code='empty')
		return required_elective_count

class CourseCreationForm(forms.ModelForm):
	"""Form for editing or adding a course"""
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
	"""Form for editing or adding an elective"""	
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
	"""Form for editing or adding elective seats"""
	dept_name = forms.CharField(max_length=100)
	max_seats = forms.IntegerField(min_value=0)
		
	def __init__(self, *args, **kwargs):
		super(ElectiveSeatsCreationForm, self).__init__(*args, **kwargs)
		
		self.fields['max_seats'].label = 'Maximum Seats'
		self.fields['max_seats'].widget.attrs.update({
				'class': 'form-control',
           })
		
		self.fields['dept_name'].widget = forms.HiddenInput()
		self.fields['dept_name'].widget.attrs.update({
				'class': 'form-control',
				'readonly': True,
           })
		
	def clean_dept_name(self):
		dept_name = self.cleaned_data.get('dept_name')
		try:
			self.dept = Department.objects.get(name=dept_name)
		except:
			raise ValidationError(_('Invalid department'), code='invalid')
		return dept_name
	
	def save(self, elective, commit=True):
		max_seats = self.cleaned_data.get('max_seats')
		elective_seat = Elective_Seats(elective=elective,dept=self.dept,max_seats=max_seats)		
		if commit == True:
			Elective_Seats.objects.filter(elective=elective,dept=self.dept).delete()
			elective_seat.save()
		return elective_seat
	
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