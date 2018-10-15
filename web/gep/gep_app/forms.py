from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Student, Faculty, Department, Course, Elective, Elective_Seats, Mutually_Exclusive_Course_Group, Elective_Preference

class UserForm(forms.ModelForm):
	class Meta:
		model = get_user_model()
		fields = ['username','password','email','role']

	def clean_email(self):
		email = self.cleaned_data.get('email')
		if email is None:
			raise ValidationError(_('This field is required'), code='empty')
		return email
 
	def clean_role(self):
		role = self.cleaned_data.get('role')
		if role is None:
			raise ValidationError(_('This field is required'), code='empty')
		return role
	
class DepartmentForm(forms.ModelForm):
	class Meta:
		model = Department
		fields = ['user','name']

class StudentForm(forms.ModelForm):
	class Meta:
		model = Student
		fields = ['user','name','date_of_birth','dept']

class FacultyForm(forms.ModelForm):
	class Meta:
		model = Faculty	
		fields = ['user','name','dept']

class StudentAcademicsDataForm(forms.ModelForm):
	class Meta:
		model = Student
		fields = ['faculty_advisor','current_cgpa','next_semester','required_elective_count','core_slots','past_courses']

	def __init__(self, *args, **kwargs):
		super(StudentAcademicsDataForm, self).__init__(*args, **kwargs)
		
		self.fields['faculty_advisor'].queryset = Faculty.objects.filter(dept=self.instance.dept).order_by('name')
		self.fields['faculty_advisor'].widget.attrs.update({
				'class': 'form-control',
			})
		
		self.fields['current_cgpa'].widget.attrs.update({
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
		
		self.fields['past_courses'].queryset = Course.objects.filter(~Q(dept=self.instance.dept)).order_by('name')
		self.fields['past_courses'].widget.attrs.update({
				'placeholder': 'No courses choosen',
				'class': 'form-control',
			})
		
		self.fields['core_slots'].widget = forms.SelectMultiple(attrs={
				'class': 'form-control',
			},choices=self.Meta.model.SLOT_CHOICES)
 
	def clean_faculty_advisor(self):
		faculty_advisor = self.cleaned_data.get('faculty_advisor')
		if faculty_advisor is None:
			raise ValidationError(_('This field is required'), code='empty')
		return faculty_advisor
 
	def clean_current_cgpa(self):
		current_cgpa = self.cleaned_data.get('current_cgpa')
		if current_cgpa is None:
			raise ValidationError(_('This field is required'), code='empty')
		return current_cgpa

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

class CourseForm(forms.ModelForm):
	class Meta:
		model = Course
		fields = ['course_id','name','dept','credits','pre_requisites','cot_requisite','cgpa_cutoff','mode_of_allotment','allowed_semesters']

	def __init__(self, *args, **kwargs):
		super(CourseForm, self).__init__(*args, **kwargs)
		
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
		
		self.fields['allowed_semesters'].label = 'Allowed semesters'
		self.fields['allowed_semesters'].widget = forms.SelectMultiple(attrs={
				'class': 'form-control',
			},choices=self.Meta.model.SEMESTER_CHOICES)

class ElectiveForm(forms.ModelForm):
	class Meta:
		model = Elective
		fields = ['course','slot','faculty']
	
	def __init__(self, *args, **kwargs):
		super(ElectiveForm, self).__init__(*args, **kwargs)
		
		self.fields['slot'].label = 'Slot'
		self.fields['slot'].widget.attrs.update({
				'class': 'form-control',
           })

		self.fields['faculty'].queryset = Faculty.objects.all().order_by('name')
		self.fields['faculty'].label = 'Faculty'
		self.fields['faculty'].widget.attrs.update({
				'class': 'form-control',
			})
		
class ElectiveSeatsForm(forms.ModelForm):
	class Meta:
		model = Elective_Seats
		fields = ['elective','max_seats','dept']
		
class MaxSeatsForm(forms.ModelForm):
	class Meta:
		model = Elective_Seats
		fields = ['max_seats','dept']
		
	def __init__(self, *args, **kwargs):
		super(MaxSeatsForm, self).__init__(*args, **kwargs)
		
		self.fields['max_seats'].label = 'Maximum Seats'
		self.fields['max_seats'].widget.attrs.update({
				'class': 'form-control',
           })
		
		self.fields['dept'].widget = forms.HiddenInput()
		self.fields['dept'].widget.attrs.update({
				'class': 'form-control',
           })
		
	def clean_max_seats(self):
		max_seats = self.cleaned_data.get('max_seats')
		if max_seats is None:
			raise ValidationError(_('Number of seats cannot be empty'), code='empty')
		return max_seats
	
	def save(self, elective, commit=True):
		max_seats = self.cleaned_data.get('max_seats')
		dept = self.cleaned_data.get('dept')
		elective_seat = Elective_Seats(elective=elective,dept=dept,max_seats=max_seats)		
		if commit == True:
			Elective_Seats.objects.filter(elective=elective,dept=dept).delete()
			elective_seat.save()
		return elective_seat
	
class MutuallyExclusiveCourseGroupForm(forms.ModelForm):
	class Meta:
		model = Mutually_Exclusive_Course_Group
		fields = ['courses']
		
	def __init__(self, *args, **kwargs):
		super(MutuallyExclusiveCourseGroupForm, self).__init__(*args, **kwargs)
		
		self.fields['courses'].label = 'Select mutually exclusive courses'
		self.fields['courses'].widget.attrs.update({
				'class': 'form-control',
           })
	
class ElectivePreferenceForm(forms.ModelForm):
	class Meta:
		model = Elective_Preference
		fields = ['student','elective','priority_rank']