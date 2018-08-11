from django.shortcuts import render
from django.shortcuts import redirect
from django.http import Http404
from django.contrib.auth import authenticate, login as auth_login , logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Student, Elective, Student_Elective_Preference
from .forms import StudentAcademicsForm

def login(request):
	if request.method == 'POST':
		user = authenticate(request,username=request.POST['username'],password=request.POST['password'])
		if user is not None:
			auth_login(request, user)
			redirect('home')
	else:
		return render(request, 'registration/login.html')

def student_check(user):
	"""Check if user is a student"""
	return user.is_student()

def faculty_check(user):
	"""Check if user is a student"""
	return user.is_faculty()

def department_check(user):
	"""Check if user is a department"""
	return user.is_department()

def academic_details_check(user):
	"""Check if student user has submitted academics details"""
	student = Student.objects.get(user=user)
	return student.has_submitted()

@login_required
def home(request):
	user = request.user
	if student_check(user):
		return redirect('student_home')
	elif faculty_check(user):
		return redirect('faculty_home')
	elif department_check(user):
		return redirect('department_home')
	else:
		raise Http404

@login_required
@user_passes_test(student_check)
def student_home(request):
	user = request.user
	student = Student.objects.get(user=user)
	
	if request.method == 'POST':
		form = StudentAcademicsForm(request.POST, instance=student)
		if form.is_valid():
			form.save()
	else:
		form = StudentAcademicsForm(instance=student)
		
	context = {
		'student': student,
		'form':form,
	}
	return render(request, 'student/home.html', context)

def get_eligible_electives(student):
	""" Return all electives eligible for which the student is eligible ordered by slot and department"""
	#All electives ordered by slot and department
	electives = Elective.objects.all().order_by('slot', 'course__dept__name')
	#Filter global electives
	global_electives = electives.filter(~Q(course__dept=student.dept))
	#Filter out electives offered in slots of core courses
	slot_satisfied_electives = global_electives.filter(~Q(slot__in=student.core_slots))
	#Filter electives with CGPA requirement satisfied
	cgpa_satisfied_electives = slot_satisfied_electives.filter(course__cgpa_cutoff__lte=student.current_CGPA)
	#Filter electives with COT requirement satisfied
	cot_satisfied_electives = [elective for elective in cgpa_satisfied_electives if not elective.course.cot_requisite or Student_COT_Allotment.objects.filter(student=student,elective=elective).exists()]
	return electives

@login_required
@user_passes_test(student_check)
def test_failure(request):
	return render(request, 'student/test_failure.html')

def preference_list_check(student):
	"""Checks whether the student has submitted the elective preference list"""
	return Student_Elective_Preference.objects.filter(student=student).exists()

def get_preference_list(student):
	"""Returns elective preference list submitted by the student"""
	elective_ids = Student_Elective_Preference.objects.filter(student=student).order_by('priority_rank').values_list('elective',flat=True)
	return Elective.objects.filter(pk__in=elective_ids)

@login_required
@user_passes_test(student_check)
@user_passes_test(academic_details_check, login_url='test_failure_page')
def preference_submission(request):
	user = request.user
	student = Student.objects.get(user=user)
	if request.method == 'POST':
		for key, value in request.POST.items():
			if key not in Elective.objects.all().values_list('id',flat=True):
				continue
			if preference_list_check(student):
				allotment = Student_Elective_Preference.objects.get(student=student, elective_id=key)
				allotment.priority_rank = value
				allotment.save()
			else:
				allotment = Student_Elective_Preference.objects.create(student=student, elective_id=key, priority_rank=value)
	electives = get_preference_list(student) if preference_list_check(student) else get_eligible_electives(student)
	context = {
		'electives':electives,
	}
	return render(request, 'student/preference_submission.html', context)

@login_required
@user_passes_test(faculty_check)
def faculty_home(request):
	return render(request, 'faculty/home.html', context)

@login_required
@user_passes_test(department_check)
def department_home(request):
	return render(request, 'department/home.html', context)
	
def change_password(request):
	context = {}
	form = LoginForm(request.POST)
	if form.is_valid():
		cd = form.cleaned_data
	return render(request, 'change_password.html', context)

def logout(request):
	auth_logout(request)
	return redirect('login')