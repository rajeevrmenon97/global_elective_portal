from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse
from django.contrib.auth import authenticate, login as auth_login , logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Student, Elective, Course, Faculty, Department, Elective_Preference, COT_Allotment, Elective_Allotment, Elective_Seats
from django.forms import formset_factory
from .forms import StudentAcademicsForm, CourseCreationForm, ElectiveCreationForm, ElectiveSeatsCreationForm, UserForm, DepartmentForm, StudentForm, FacultyForm
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core import exceptions
					##########################################
					#       User Passes Test Functions       #
					##########################################

def student_check(user):
	"""Check if user is a student"""
	return user.is_student()

def faculty_check(user):
	"""Check if user is a student"""
	return user.is_faculty()

def department_check(user):
	"""Check if user is a department"""
	return user.is_department()

def sac_check(user):
	"""Check if user is a department"""
	return user.is_sac()

def academic_details_check(user):
	"""Check if student user has submitted academics details"""
	student = Student.objects.get(user=user)
	if student.FA is not None:
		return True
	return False

def preference_submission_check(user):
	"""Check if student user has submitted academics details"""
	student = Student.objects.get(user=user)
	if student.submission_datetime is not None:
		return True
	return False

						#####################################
						#              Login                #
						#####################################
def login(request):
	"""Authenticate the user credentials and logs in"""
	if request.method == 'POST':
		user = authenticate(request,username=request.POST['username'],password=request.POST['password'])
		if user is not None:
			auth_login(request, user)
			redirect('home')
	else:
		return render(request, 'registration/login.html')

						#####################################
						#              Logout               #
						#####################################
def logout(request):
	"""Logs out the current user"""
	auth_logout(request)
	return redirect('login')

						#####################################
						#              Home                 #
						#####################################

@login_required
def home(request):
	"""Redirect to corresponding portal of the logged in user"""
	user = request.user
	if student_check(user):
		return redirect('student_home')
	elif faculty_check(user):
		return redirect('faculty_home')
	elif department_check(user):
		return redirect('department_home')
	elif sac_check(user):
		return redirect('sac_home')
	else:
		raise Http404

						##########################################
						#             Student Portal             #
						##########################################

##########################################
#           Helper Functions             #
##########################################

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
	electives = [Elective.objects.get(pk=elective_id) for elective_id in elective_ids]
	#2) All electives for which student is eligible
	eligible_electives = get_eligible_electives(student)
	#3) Add recently added electives in the end
	recently_added_electives = list(set(eligible_electives) - set(electives))
	electives.extend(recently_added_electives)
	#4) Remove recently removed electives
	recently_removed_electives = list(set(electives) - set(eligible_electives))
	return [elective for elective in electives if elective not in recently_removed_electives]

##########################################
#    Academic Details Submission Stage   #
##########################################
@login_required
@user_passes_test(student_check)
def student_home(request):
	"""Submits the details for FA verification"""
	user = request.user
	student = Student.objects.get(user=user)
	
	if request.method == 'POST':
		form = StudentAcademicsForm(request.POST, instance=student)
		if form.is_valid():
			form.save()
			
	else:
		form = StudentAcademicsForm(instance=student)
		
	context = {
		'roll_number':user.username,
		'name': student.name,
		'form':form,
		'is_submitted':academic_details_check(student),
	}
	
	return render(request, 'student/home.html', context)

###################################################
#    Previous Stages Incomplete -  Failure Page   #
###################################################
@login_required
@user_passes_test(student_check)
def student_test_failure(request):
	"""Renders error page for the students who has not completed the previous stages"""
	return render(request, 'student/test_failure.html')

#############################################
#    Elective Preference Submission Stage   #
#############################################
@login_required
@user_passes_test(student_check)
@user_passes_test(academic_details_check, login_url='student_test_failure')
def student_preference_submission(request):
	"""Submits the elective preference list of the student"""
	user = request.user
	student = Student.objects.get(user=user)
	
	if request.method == 'POST':
		elective_ids = Elective.objects.all().values_list('id',flat=True)
		
		for key, value in request.POST.items():
			#Skip csrf token
			try:
				elective_id = int(key)
			except ValueError:
				continue
				
			#Save priority rank of valid elective_ids
			if elective_id in elective_ids:
				allotment,is_created = Elective_Preference.objects.get_or_create(student=student, elective_id=elective_id)
				allotment.priority_rank = value
				allotment.save()
		student.submission_datetime = datetime.now()
		student.save()
				
	electives = get_preference_list(student)
	context = {
		'electives':electives,
		'is_submitted':preference_submission_check(student),
	}
	
	return render(request, 'student/preference_submission.html', context)


#############################################
#    Elective Allotment Publishing Stage    #
#############################################
@login_required
@user_passes_test(student_check)
@user_passes_test(academic_details_check, login_url='student_test_failure')
@user_passes_test(preference_submission_check, login_url='student_test_failure')
def student_allotment(request):
	"""Displays the elective alloted to the student"""
	user = request.user
	student = Student.objects.get(user=user)
	
	allotments = Elective_Allotment.objects.filter(student=student)
	context = {
		'allotments':allotments,
	}
	
	return render(request, 'student/allotment.html', context)


					##########################################
					#                SAC Portal              #
					##########################################

##########################################
#           Helper Functions             #
##########################################

def get_data_from_csv(request,return_view,csv_file_name):
	"""Retrieve the file with the given file name from the request, decode it and return, If error redirect to the given return view"""
	try:
		csv_file = request.FILES[csv_file_name]
		
		#if file is not CSV, return
		if not csv_file.name.endswith('.csv'):
			messages.error(request,'File is not CSV type')
#			return redirect(return_view)
		
        #if file is too large, return
		if csv_file.multiple_chunks():
			messages.error(request,"Uploaded file is too big (%.2f MB)." % (csv_file.size/(1000*1000),))
#			return redirect(return_view)
		
		file_data = csv_file.read().decode("utf-8")
		return file_data
		
	except Exception as e:
		messages.error(request,"Unable to upload file. "+repr(e))
#		return redirect(return_view)
	
@login_required
@user_passes_test(sac_check)
def sac_home(request):
	return render(request, 'sac/home.html')

@login_required
@user_passes_test(sac_check)
def startup_dept(request):
	""" Uploads Department data to database """
	if request.method == 'POST':
		# Clear the Database
		Student.objects.all().delete()
		Faculty.objects.all().delete()
		Department.objects.all().delete()
		get_user_model().objects.filter(~Q(role=get_user_model().SAC)).delete()
		
		# Get the department data from uploaded CSV
		departments_data = get_data_from_csv(request,'sac_home','departments_file')

		lines = departments_data.split("\n")[1:]
		for index, line in enumerate(lines):
			fields = line.split(",")
			
			# Create user for department
			user_dict = {
				'username': fields[0].strip(),
				'email': fields[2].strip(),
				'role': get_user_model().DEPARTMENT,
			}
			form = UserForm(user_dict)
			if form.is_valid():
				user = form.save()
				user.set_password('DEPT_' + user.username)
				user.save()
				
				# Create department
				dept_dict = {
					'user':user.username,
					'name':fields[1].strip(),
				}
				form = DepartmentForm(dept_dict)
				if form.is_valid():
					form.save()			
				else:
					messages.error(request,'Error in line ' + str(index + 1) + form.errors.as_json())
					break
			else:
				messages.error(request,'Error in line ' + str(index + 1) + form.errors.as_json())
				break
				
	return redirect('sac_home')

@login_required
@user_passes_test(sac_check)
def startup_student(request):
	""" Uploads Student data to database """
	if request.method == 'POST':
		# Clear the Database
		Student.objects.all().delete()
		get_user_model().objects.filter(role=get_user_model().STUDENT).delete()
		
		# Get the student data from uploaded CSV
		students_data = get_data_from_csv(request,'sac_home','students_file')

		lines = students_data.split("\n")[1:]
		for index, line in enumerate(lines):
			fields = line.split(",")
			
			# Create user for student
			user_dict = {
				'username': fields[0].strip(),
				'email': fields[2].strip(),
				'role': get_user_model().STUDENT,
			}
			user_form = UserForm(user_dict)
			if user_form.is_valid():
				user = user_form.save()
				user.set_password(user.username)
				user.save()
				
				# Create student
				student_dict = {
					'user':user.username,
					'name':fields[1].strip(),
					'date_of_birth':fields[3].strip(),
					'dept':fields[4].strip(),
				}
				student_form = StudentForm(student_dict)
				if student_form.is_valid():
					student_form.save()			
				else:
					messages.error(request,'Error in line ' + str(index + 1) + student_form.errors.as_json())
					break
			else:
				messages.error(request,'Error in line ' + str(index + 1) + user_form.errors.as_json())
				break
				
	return redirect('sac_home')

@login_required
@user_passes_test(sac_check)
def startup_faculty(request):
	""" Uploads Student data to database """
	if request.method == 'POST':
		# Clear the Database
		Faculty.objects.all().delete()
		get_user_model().objects.filter(role=get_user_model().FACULTY).delete()
		
		# Get the student data from uploaded CSV
		faculties_data = get_data_from_csv(request,'sac_home','faculties_file')

		lines = faculties_data.split("\n")[1:]
		for index, line in enumerate(lines):
			fields = line.split(",")
			
			# Create user for faculty
			user_dict = {
				'username': fields[0].strip(),
				'email': fields[2].strip(),
				'role': get_user_model().FACULTY,
			}
			user_form = UserForm(user_dict)
			if user_form.is_valid():
				user = user_form.save()
				user.set_password('FACULTY')
				user.save()
				
				# Create student
				faculty_dict = {
					'user':user.username,
					'name':fields[1].strip(),
					'dept':fields[3].strip(),
				}
				faculty_form = FacultyForm(faculty_dict)
				if faculty_form.is_valid():
					faculty_form.save()			
				else:
					messages.error(request,'Error in line ' + str(index + 1) + faculty_form.errors.as_json())
					break
			else:
				messages.error(request,'Error in line ' + str(index + 1))
				break
				
	return redirect('sac_home')

@login_required
@user_passes_test(sac_check)
def sac_course(request):	
	#Create formset for Elective Seats of each department
	depts = Department.objects.all().order_by('name')
	ElectiveSeatsCreationFormSet = formset_factory(ElectiveSeatsCreationForm, extra=0)
	elective_seats_formset = ElectiveSeatsCreationFormSet(initial=[{'dept_name': dept.name} for dept in depts])

	context = {
		'is_course_submitted':False,
		'elective_seats_formset':elective_seats_formset,
	}
	
	if request.method == 'POST':
		try:
			course = Course.objects.get(course_id=request.POST.get('course_id'))
			course_form = CourseCreationForm(request.POST,instance=course)
			context['course'] = course
		except:
			course_form = CourseCreationForm(request.POST)
		if course_form.is_valid():
			course = course_form.save()
			context['course'] = course
			context['electives'] = Elective.objects.filter(course=course)
			context['elective_seats'] = Elective_Seats.objects.filter(elective__course=course).order_by('dept__name')
			context['elective_form'] = ElectiveCreationForm(initial={course:course})
			context['is_course_submitted'] = True
	else:
		course_form = CourseCreationForm()
		context['elective_form'] = ElectiveCreationForm()
		
	context['course_form'] = course_form
	return render(request, 'department/home.html', context)

@login_required
@user_passes_test(sac_check)
def add_elective(request):
	#Create formset for Elective Seats of each department
	depts = Department.objects.all().order_by('name')
	ElectiveSeatsCreationFormSet = formset_factory(ElectiveSeatsCreationForm, extra=0)
	elective_seats_formset = ElectiveSeatsCreationFormSet(initial=[{'dept_name': dept.name} for dept in depts])

	data = dict()
	data['valid'] = False
	
	if request.method == 'POST':
		try:
			course = Course.objects.get(course_id=request.POST.get('course'))
		except:
			data['error'] = 'Invalid course ' + request.POST.get('course')
			return JsonResponse(data)
		
		try:
			elective = Elective.cts.get(course=course,slot=request.POST.get('slot'))
			elective_form = ElectiveCreationForm(request.POST,instance=elective)
		except:
			elective_form = ElectiveCreationForm(request.POST)
			
		elective_seats_formset = ElectiveSeatsCreationFormSet(request.POST)
	
		if elective_form.is_valid() and elective_seats_formset.is_valid() and not elective_seats_formset.has_changed():
			data['valid'] = True
			elective = elective_form.save()
			for elective_seat_form in elective_seats_formset:
				elective_seat_form.save(elective)
			
		elif elective_seats_formset.has_changed():
			data['error'] = 'Corrupted data, please reload' 
		elif 'max_seats' in elective_seats_formset.errors:
			data['error'] = 'Invalid seat number' 
		elif 'dept' in elective_seats_formset.errors:
			data['error'] = 'Invalid department' 
		elif 'slot' in elective_form.errors:
			data['error'] = 'Invalid slot' 
		elif 'faculty' in elective_form.errors:
			data['error'] = 'Invalid faculty'
	print(data)
	return JsonResponse(data)


	
@login_required
@user_passes_test(department_check)
def department_home(request):
	return render(request, 'department/home.html', context)
	
@login_required
@user_passes_test(faculty_check)
def faculty_home(request):
	return render(request, 'faculty/home.html', context)