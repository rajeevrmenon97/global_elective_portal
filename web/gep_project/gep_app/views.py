from django.shortcuts import render
from django.shortcuts import redirect
from django.http import Http404
from django.contrib.auth import authenticate, login as auth_login , logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Student
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
	return user.is_student()

def faculty_check(user):
	return user.is_faculty()

def department_check(user):
	return user.is_department()

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
	slots = Student.SLOT_CHOICES
	semesters = Student.SEMESTER_CHOICES
	
	if request.method == 'POST':
		form = StudentAcademicsForm(request.POST, instance=student)
		if form.is_valid():
			form.save()
		else:
			context = {
				'slots':slots,
				'semesters':semesters,
				'student': {
					'name':student.name,
					'roll_number':user.username,
				},
				'form' : form
			}
			return render(request, 'student/home.html', context)

	form = StudentAcademicsForm()
	context = {
		'slots':slots,
		'semesters':semesters,
		'student': {
			'name':student.name,
			'roll_number':user.username,
		},
		'form' : form
	}
	return render(request, 'student/home.html', context)

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