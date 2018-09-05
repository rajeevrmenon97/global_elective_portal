from django.shortcuts import render
from django.shortcuts import redirect
from django.http import Http404
from django.contrib.auth import authenticate, login as auth_login , logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Student, Elective, Faculty, Department, Elective_Preference, COT_Allotment
from .forms import StudentAcademicsForm, CourseCreationForm, AddElectiveForm

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
		'user':user.username,
		'student_name': student.name,
		'form':form,
	}
	return render(request, 'student/home.html', context)

@login_required
@user_passes_test(student_check)
def test_failure(request):
	return render(request, 'student/test_failure.html')

def preference_list_check(student,elective_id=None):
	"""Checks whether the student has submitted the elective preference list"""
	if elective_id is None:
		return Elective_Preference.objects.filter(student=student).exists()
	else:
		return Elective_Preference.objects.filter(student=student,elective_id=elective_id).exists()

def get_eligible_electives(student):
	""" Return all electives eligible for which the student is eligible ordered by slot and department"""
	#1) All electives ordered by slot and department
	electives = Elective.objects.all().order_by('slot', 'course__dept__name')
	#2) Filter global electives
	global_electives = electives.filter(~Q(course__dept=student.dept))
	#3) Filter out electives that were already taken
	not_taken_electives = global_electives.filter(~Q(course__in=student.past_courses.all()))
	#4) Filter out electives offered in slots of core courses
	slot_satisfied_electives = not_taken_electives.filter(~Q(slot__in=student.core_slots))
	#5) Filter electives with CGPA requirement satisfied
	cgpa_satisfied_electives = slot_satisfied_electives.filter(course__cgpa_cutoff__lte=student.current_CGPA)
	#6) Filter electives with COT requirement satisfied
	cot_satisfied_electives = [elective for elective in cgpa_satisfied_electives if not elective.course.cot_requisite or COT_Allotment.objects.filter(student=student,elective=elective).exists()]
	return cot_satisfied_electives

def get_preference_list(student):
	"""Returns elective preference list submitted by the student along with new electives and after removing removed electives"""
	#1) All electives submitted by the student
	elective_ids = Elective_Preference.objects.filter(student=student).order_by('priority_rank').values_list('elective',flat=True)
	electives = list(Elective.objects.filter(pk__in=elective_ids))
	#2) Add recently added electives in the end
	recently_added_electives = list(set(get_eligible_electives(student)) - set(electives))
	electives.extend(recently_added_electives)
	#3) Remove recently removed electives
	recently_removed_electives = list(set(electives) - set(get_eligible_electives(student)))
	return [elective for elective in electives if elective not in recently_removed_electives]

@login_required
@user_passes_test(student_check)
@user_passes_test(academic_details_check, login_url='test_failure_page')
def preference_submission(request):
	user = request.user
	student = Student.objects.get(user=user)
	if request.method == 'POST':
		elective_ids = Elective.objects.all().values_list('id',flat=True)
		for key, value in request.POST.items():
			try:
				elective_id = int(key)
			except ValueError:
				continue
			if elective_id not in elective_ids:
				continue
			if preference_list_check(student,elective_id):
				allotment = Elective_Preference.objects.get(student=student, elective_id=elective_id)
				allotment.priority_rank = value
				allotment.save()
			else:
				allotment = Elective_Preference.objects.create(student=student, elective_id=elective_id, priority_rank=value)
				
	electives = get_preference_list(student)
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
	user = request.user
	user_dept = Department.objects.get(user=user)
	depts = Department.objects.all()	
	slots = Elective.SLOT_CHOICES
	faculties = Faculty.objects.all().order_by('name')	

	if request.method == 'POST':
		print(request.POST)
		course_form = CourseCreationForm(request.POST)
		hidden_form = AddElectiveForm(request.POST)
		if course_form.is_valid() and hidden_form.is_valid():
			course_form.save(user_dept)
	else:
		course_form = CourseCreationForm()
		hidden_form = AddElectiveForm()

	context = {
		'user_dept':user_dept,
		'depts':depts,
		'slots':slots,
		'faculties':faculties,
		'form':course_form,
		'hidden_form':hidden_form,
	}
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