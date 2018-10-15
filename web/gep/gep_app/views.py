from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from django.contrib.auth import authenticate, login as auth_login , logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Student, Elective, Course, Faculty, Department, Elective_Preference, COT_Allotment, Elective_Allotment, Elective_Seats, Mutually_Exclusive_Course_Group
from django.forms import formset_factory
from .forms import StudentAcademicsDataForm, CourseForm, ElectiveForm, ElectiveSeatsForm, UserForm, DepartmentForm, StudentForm, FacultyForm, MutuallyExclusiveCourseGroupForm, ElectivePreferenceForm
from datetime import datetime
from django.contrib import messages
from django.core import exceptions
from django.conf import settings
import csv
from io import BytesIO, StringIO
from zipfile import ZipFile
from .allotment import *

					##########################################
					#       User Passes Test Functions       #
					##########################################

def student_check(user):
	"""Check if user is a student"""
	return user.role == get_user_model().STUDENT

def faculty_check(user):
	"""Check if user is a faculty"""
	return user.role == get_user_model().FACULTY

def department_check(user):
	"""Check if user is a department"""
	return user.role == get_user_model().DEPARTMENT

def sac_check(user):
	"""Check if user is a SAC Admin"""
	return user.role == get_user_model().SAC

def academic_details_check(user):
	"""Check if student user has submitted academics details"""
	student = Student.objects.get(user=user)
	return student.faculty_advisor is not None

def preference_submission_check(user):
	"""Check if student user has submitted academics details"""
	student = Student.objects.get(user=user)
	return student.submission_datetime is not None

						##########################################
						#       Current Stage Check Functions    #
						##########################################

def academic_data_submission_stage_check():
	start_date = settings.APP_CONFIG['gep_app']['ACADEMIC_DATA_SUBMISSION_START_DATE']
	end_date = settings.APP_CONFIG['gep_app']['ACADEMIC_DATA_SUBMISSION_END_DATE']
	return datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S') < datetime.now() < datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')

def pre_academic_data_submission_stage_check():
	start_date = settings.APP_CONFIG['gep_app']['ACADEMIC_DATA_SUBMISSION_START_DATE']
	return datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S') > datetime.now()

def preference_submission_stage_check():
	start_date = settings.APP_CONFIG['gep_app']['PREFERENCE_SUBMISSION_START_DATE']
	end_date = settings.APP_CONFIG['gep_app']['PREFERENCE_SUBMISSION_END_DATE']
	return datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S') < datetime.now() < datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')

def pre_preference_submission_stage_check():
	start_date = settings.APP_CONFIG['gep_app']['PREFERENCE_SUBMISSION_START_DATE']
	return datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S') > datetime.now()

def allotment_publication_stage_check():
	start_date = settings.APP_CONFIG['gep_app']['ALLOTMENT_PUBLICATION_START_DATE']
	end_date = settings.APP_CONFIG['gep_app']['ALLOTMENT_PUBLICATION_END_DATE']
	return datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S') < datetime.now() < datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')

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

def remove_local_electives(student, electives):
#	print(electives.filter(~Q(course__dept=student.dept)))
	return electives.filter(~Q(course__dept=student.dept))

#def remove_taken_electives(student, electives):
#	return electives.filter(~Q(course__in=student.past_courses.all()))

def remove_electives_of_core_slots(student, electives):
#	print(electives.filter(~Q(slot__in=student.core_slots)))
	return electives.filter(~Q(slot__in=student.core_slots))

def remove_electives_with_insufficient_cgpa(student, electives):
#	print(electives.filter(course__cgpa_cutoff__lte=student.current_cgpa))
	return electives.filter(course__cgpa_cutoff__lte=student.current_cgpa)

def remove_taken_electives_and_mutually_exclusive_electives_of_taken_electives(student, electives):
	exclusive_course_groups = Mutually_Exclusive_Course_Group.objects.all()
	for course in student.past_courses.all():
		for exclusive_course_group in exclusive_course_groups:
			if course in exclusive_course_group.courses.all():
				electives = electives.filter(~Q(course__in=exclusive_course_group.courses.all()))
			else:
				electives = electives.filter(~Q(course=course))
#	print(electives)
	return electives

def remove_electives_with_cot_not_acquired(student, electives):
	for elective in electives:
		cot_requisite = COT_Allotment.objects.filter(student=student,elective=elective).exists()
		electives = electives.filter(course__cot_requisite=cot_requisite)
#	print(electives)
	return electives

def get_sorted_eligible_electives(student):
	electives = Elective.objects.all().order_by('slot', 'course__dept__name')
	return remove_electives_with_cot_not_acquired(student, remove_electives_with_insufficient_cgpa(student, remove_taken_electives_and_mutually_exclusive_electives_of_taken_electives(student, remove_electives_of_core_slots(student, remove_local_electives(student, electives)))))

def get_sorted_submitted_electives(student):
	sorted_submitted_elective_ids = Elective_Preference.objects.filter(student=student).order_by('priority_rank').values_list('elective',flat=True)
	return [Elective.objects.get(pk=elective_id) for elective_id in sorted_submitted_elective_ids]

def get_queryset_difference(first_queryset,second_queryset):
	return list(set(first_queryset) - set(second_queryset))

def get_updated_and_priority_sorted_elective_list(student):
	sorted_submitted_electives = get_sorted_submitted_electives(student)
#	print(sorted_submitted_electives)
	sorted_eligible_electives = get_sorted_eligible_electives(student)
#	print(sorted_eligible_electives)
	recently_added_electives = get_queryset_difference(sorted_eligible_electives,sorted_submitted_electives)
#	print(recently_added_electives)
	recently_removed_electives = get_queryset_difference(sorted_submitted_electives,sorted_eligible_electives)
#	print(recently_removed_electives)
	
	sorted_submitted_electives.extend(recently_added_electives)
	return [elective for elective in sorted_submitted_electives if elective not in recently_removed_electives]

##########################################
#             Student Home               #
##########################################
@login_required
@user_passes_test(student_check)
def student_home(request):
	if academic_data_submission_stage_check():
		return redirect('student_academic_data_submission')
	elif preference_submission_stage_check():
		return redirect('student_preference_submission')
	elif allotment_publication_stage_check():
		return redirect('student_allotment_publication')
	else:
		raise Http404

##########################################
#    Academic Details Submission Stage   #
##########################################
@login_required
@user_passes_test(student_check)
def student_academic_data_submission(request):
	user = request.user
	student = Student.objects.get(user=user)
	
	if request.method == 'POST':
		form = StudentAcademicsDataForm(request.POST, instance=student)
		if form.is_valid():
			form.save()
			
	else:
		form = StudentAcademicsDataForm(instance=student)
		
	context = {
		'roll_number':user.username,
		'name': student.name,
		'form':form,
		'has_submitted':academic_details_check(student),
	}
	
	return render(request, 'student/home.html', context)

###################################################
#    Previous Stages Incomplete -  Failure Page   #
###################################################
@login_required
@user_passes_test(student_check)
def student_incomplete_previous_stage(request):
	return render(request, 'student/test_failure.html')

#############################################
#    Elective Preference Submission Stage   #
#############################################
@login_required
@user_passes_test(student_check)
@user_passes_test(academic_details_check, login_url='student_incomplete_previous_stage')
def student_preference_submission(request):
	user = request.user
	student = Student.objects.get(user=user)
	
	if request.method == 'POST':
		Elective_Preference.objects.filter(student=student).delete()
		student.submission_datetime = None
		student.save()
		
		for key, value in request.POST.items():
			#Skip csrf token
			try:
				elective_id = int(key)
			except ValueError:
				continue
				
			elective_preference_data = {
				'student':student,
				'elective':elective_id,
				'priority_rank':value
			}
				
			try:
				elective_preference = Elective_Preference.objects.get(student=student,elective=elective_id)
				form = ElectivePreferenceForm(elective_preference_data,instance=elective_preference)
			except exceptions.ObjectDoesNotExist:
				form = ElectivePreferenceForm(elective_preference_data)
			
			if form.is_valid():
				form.save()
			else:
				raise Http404
				
		student.submission_datetime = datetime.now()
		student.save()
				
	electives = get_updated_and_priority_sorted_elective_list(student)
	context = {
		'electives':electives,
		'has_submitted':preference_submission_check(student),
	}
	
	return render(request, 'student/preference_submission.html', context)


#############################################
#    Elective Allotment Publishing Stage    #
#############################################
@login_required
@user_passes_test(student_check)
@user_passes_test(academic_details_check, login_url='student_incomplete_previous_stage')
@user_passes_test(preference_submission_check, login_url='student_incomplete_previous_stage')
def student_allotment_publication(request):
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

def get_uploaded_file(request,csv_file_name):
	try:
		csv_file = request.FILES[csv_file_name]
		return csv_file
	except Exception as e:
		messages.error(request,"Unable to upload file. " + repr(e))
		return None	
		
def convert_csv_to_data(csv_file):		
	if not csv_file.name.endswith('.csv'):
		messages.error(request,'File is not CSV type')
		return None

	if csv_file.multiple_chunks():
		messages.error(request,"Uploaded file is too big (%.2f MB)." % (csv_file.size/(1000*1000),))
		return None

	file_data = csv_file.read().decode("utf-8")
	return file_data

def convert_form_errors_to_string(form):
	errorlist = form.errors
	for field,errors in errorlist.items():
		for error in errors:
			return 'Error: %s' %(error)
	
##########################################
#              Home Page              #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_home(request):
	return render(request, 'sac/home.html')

##########################################
#         Upload Department Data         #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_dept(request):
	if request.method == 'POST':
		if pre_academic_data_submission_stage_check():
			Student.objects.all().delete()
			Faculty.objects.all().delete()
			Department.objects.all().delete()
			get_user_model().objects.filter(~Q(role=get_user_model().SAC)).delete()

			uploaded_file = get_uploaded_file(request,'department_file')
			if uploaded_file is None:
				return redirect('sac_home')
			
			department_data = convert_csv_to_data(uploaded_file)
			if department_data is None:	
				return redirect('sac_home')
						
			lines = department_data.split("\n")[1:]
			for index, line in enumerate(lines):
				fields = line.split(",")
				try:
					username = fields[0].strip() #Extra \n and \r may be introduced during csv conversion
					name = fields[1].strip()
					email = fields[2].strip()
				except IndexError:
					messages.error(request, 'Line ' + str(index+1) + ' insufficient number of fields')
					break

				user_dict = {
					'username': username,
					'email': email,
					'role': get_user_model().DEPARTMENT,
				}
				user_form = UserForm(user_dict)
				
				if user_form.is_valid():
					user = user_form.save()
					user.set_password('DEPTARTMENT') #Default password
					user.save()

					dept_dict = {
						'user':user.username,
						'name':name,
					}
					dept_form = DepartmentForm(dept_dict)
					
					if dept_form.is_valid():
						dept_form.save()			
					else:
						messages.error(request, 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(dept_form))
						break
				else:
					messages.error(request, 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(user_form))
					break
		else:
			messages.error(request, 'This data can be updated only before academic data submission stage')
				
	return redirect('sac_home')

##########################################
#           Upload Faculty Data          #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_faculty(request):
	if request.method == 'POST':
		if pre_academic_data_submission_stage_check():
			Student.objects.all().delete()
			Faculty.objects.all().delete()
			get_user_model().objects.filter(role=get_user_model().FACULTY).delete()
			get_user_model().objects.filter(role=get_user_model().STUDENT).delete()

			uploaded_file = get_uploaded_file(request,'faculty_file')
			if uploaded_file is None:
				return redirect('sac_home')
			
			faculty_data = convert_csv_to_data(uploaded_file)
			if faculty_data is None:	
				return redirect('sac_home')
						
			lines = faculty_data.split("\n")[1:]
			for index, line in enumerate(lines):
				fields = line.split(",")
				try:
					username = fields[0].strip() #Extra \n and \r may be introduced during csv conversion
					name = fields[1].strip()
					email = fields[2].strip()
					dept = fields[3].strip()
				except IndexError:
					messages.error(request, 'Line ' + str(index+1) + ' insufficient number of fields')
					break

				user_dict = {
					'username': username,
					'email': email,
					'role': get_user_model().FACULTY,
				}
				user_form = UserForm(user_dict)
				
				if user_form.is_valid():
					user = user_form.save()
					user.set_password('FACULTY') #Default password
					user.save()

					faculty_dict = {
						'user':user.username,
						'name':name,
						'dept':dept,
					}
					faculty_form = FacultyForm(faculty_dict)
					
					if faculty_form.is_valid():
						faculty_form.save()			
					else:
						messages.error(request, 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(faculty_form))
						break
				else:
					messages.error(request, 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(user_form))
					break
		else:
			messages.error(request, 'This data can be updated only before academic data submission stage')
				
	return redirect('sac_home')


##########################################
#           Upload Student Data          #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_student(request):
	""" Uploads Student data to database """
	if request.method == 'POST':
		if pre_academic_data_submission_stage_check():
			Student.objects.all().delete()
			get_user_model().objects.filter(role=get_user_model().STUDENT).delete()

			uploaded_file = get_uploaded_file(request,'student_file')
			if uploaded_file is None:
				return redirect('sac_home')
			
			student_data = convert_csv_to_data(uploaded_file)
			if student_data is None:	
				return redirect('sac_home')
						
			lines = student_data.split("\n")[1:]
			for index, line in enumerate(lines):
				fields = line.split(",")
				try:
					username = fields[0].strip() #Extra \n and \r may be introduced during csv conversion
					name = fields[1].strip()
					email = fields[2].strip()
					date_of_birth = fields[3].strip()
					dept = fields[4].strip()
				except IndexError:
					messages.error(request, 'Line ' + str(index+1) + ' insufficient number of fields')
					break

				user_dict = {
					'username': username,
					'email': email,
					'role': get_user_model().STUDENT,
				}
				user_form = UserForm(user_dict)
				
				if user_form.is_valid():
					user = user_form.save()
					user.set_password(user.username) #Default password
					user.save()

					student_dict = {
						'user':user.username,
						'name':name,
						'date_of_birth':date_of_birth,
						'dept':dept,
					}
					student_form = StudentForm(student_dict)
					
					if student_form.is_valid():
						student_form.save()			
					else:
						messages.error(request, 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(student_form))
						break
				else:
					messages.error(request, 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(user_form))
					break
		else:
			messages.error(request, 'This data can be updated only before academic data submission stage')
				
	return redirect('sac_home')

##########################################
#             Upload COT Data            #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_cot(request):
	if request.method == 'POST':
		if pre_preference_submission_stage_check():
			COT_Allotment.objects.all().delete()

			uploaded_file = get_uploaded_file(request,'cot_file')
			if uploaded_file is None:
				return redirect('sac_home')
			
			cot_data = convert_csv_to_data(uploaded_file)
			if cot_data is None:	
				return redirect('sac_home')

			lines = cot_data.split("\n")[1:]
			for index, line in enumerate(lines):
				fields = line.split(",")
				try:
					course = fields[0].strip() #Extra \n and \r may be introduced during csv conversion
					slot = fields[1].strip()
					student = fields[2].strip()
				except IndexError:
					messages.error(request, 'Line ' + str(index+1) + ' insufficient number of fields')
					break

				try:
					elective = Elective.objects.get(course=course,slot=slot)
				except exceptions.ObjectDoesNotExist:
					messages.error(request, 'Invalid course or slot in line ' + str(index+1))
					break
				
				cot_dict = {
					'elective': elective,
					'student': student,
				}
				cot_allotment_form = COTAllotmentForm(cot_dict)

				if cot_allotment_form.is_valid():
					cot_allotment_form.save()				
				else:
					messages.error(request, 'Line ' + str(index+1) + convert_form_errors_to_string(cot_allotment_form))
					break

		else:
			messages.error(request, 'This data can be updated only before preference submission stage')

	return redirect('sac_home')

##########################################
#         Download Academic Data         #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_academic_data(request):
	buffer_for_zip = BytesIO()
	zip = ZipFile(buffer_for_zip, "w")       
	
	depts = Department.objects.all().order_by('name')
	for dept in depts:
		buffer_for_submitted_students_csv = StringIO()
		writer_for_submitted_students = csv.writer(buffer_for_submitted_students_csv)
		
		buffer_for_not_submitted_students_csv = StringIO()
		writer_for_not_submitted_students = csv.writer(buffer_for_not_submitted_students_csv)
		
		title_row = ['Roll Number','Name','Faculty Advisor','Next Semester','Current CGPA','Number of global electives','Past Courses','Core slots']
		writer_for_submitted_students.writerow(title_row)
		
		title_row = ['Roll Number','Name']
		writer_for_not_submitted_students.writerow(title_row)
		
		students = Student.objects.filter(dept=dept).order_by('faculty_advisor','next_semester','name')
		for student in students:
			if academic_details_check(student.user):
				past_courses = ''
				for course in student.past_courses.all():
					past_courses = past_courses + course.name + ', '
				core_slots = ''
				for slot in student.core_slots:
					core_slots = core_slots + slot + ', '
				row = [student.user.username, student.name, student.faculty_advisor.name, student.next_semester , student.current_cgpa, student.required_elective_count, past_courses, core_slots]
				writer_for_submitted_students.writerow(row)
			else:
				row = [student.user.username, student.name]
				writer_for_not_submitted_students.writerow(row)
		
		zip.writestr("%s-submitted.csv" %(dept.name), buffer_for_submitted_students_csv.getvalue())
		zip.writestr("%s-not-submitted.csv" %(dept.name), buffer_for_not_submitted_students_csv.getvalue())

	# Fix for Linux zip files read in Windows
	for file in zip.filelist:
		file.create_system = 0 

	zip.close()

	response = HttpResponse(content_type="application/zip")
	response["Content-Disposition"] = "attachment; filename=AcademicData.zip"
	buffer_for_zip.seek(0)    
	response.write(buffer_for_zip.read())
	return response

##########################################
#         Download Allotment Data        #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_allotment_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="Allotment.csv"'
	
	writer = csv.writer(response)
	
	title_row = ['Course ID','Course Name','Slot','Roll Number','Student Name', 'Semester']
	writer.writerow(title_row)
	
	allotments = Elective_Allotment.objects.all().order_by('elective__course__dept','elective__course__name','elective__slot','student__next_semester','student__name')
	for allotment in allotments:
		row = [allotment.elective.course.course_id, allotment.elective.course.name, allotment.elective.get_slot_display(), allotment.student.user.username, allotment.student.name, allotment.student.get_next_semester_display()]
		writer.writerow(row)
	
	return response
	
##########################################
#     Start Global Elective Allotment    #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_start_allotment(request):
	start_global_elective_allotment()	
	return redirect('sac_home')

##########################################
#            Manage Electives            #
##########################################

##########################################
#              View Courses              #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_view_courses(request):
	courses = Course.objects.all().order_by('dept__name','name')
	context = {
		'courses':courses,
	}
	return render(request, 'sac/view_courses.html', context)

##########################################
#               Add Course               #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_add_course(request):	
	if request.method == 'POST':
		try:
			course_id = request.POST.get('course_id')
			course = Course.objects.get(course_id=course_id)
			form = CourseForm(request.POST,instance=course)
		except:
			form = CourseForm(request.POST)
			
		if form.is_valid():
			course = form.save()
			request.session['course_id'] = course.course_id
			return redirect('sac_view_electives_of_course')
	else:
		form = CourseForm()
		
	context = {
		'form':form,
	}
	
	return render(request, 'sac/add_course.html', context)

##########################################
#              Edit Course               #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_edit_course(request):
	if request.method == 'POST':
		try:
			course_id = request.POST.get('course_id')
			course = Course.objects.get(course_id=course_id)
		except:
			raise Http404
			
		form = CourseForm(instance=course)
		context = {
			'form':form,
		}
		
		return render(request, 'sac/add_course.html', context)
		
	raise Http404

##########################################
#             Delete Course              #
##########################################
	
@login_required
@user_passes_test(sac_check)
def sac_delete_course(request):
	if request.method == 'POST':
		try:
			course_id = request.POST.get('course_id')
			Course.objects.get(course_id=course_id).delete()
		except:
			raise Http404
		
		return redirect('sac_view_courses')
	
	raise Http404

##########################################
#       View Electives of a Course       #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_view_electives_of_course(request):
	try:
		course_id = request.session.get('course_id')
		course = Course.objects.get(course_id=course_id)
	except:
		raise Http404
		
	depts = Department.objects.all().order_by('name')
	electives = Elective.objects.filter(course=course).order_by('slot')
	elective_seats = Elective_Seats.objects.filter(elective__course=course).order_by('elective__slot','dept__name')

	elective_form = ElectiveForm(initial={course:course})
	ElectiveSeatsFormSet = formset_factory(ElectiveSeatsForm, extra=0)
	elective_seats_formset = ElectiveSeatsFormSet(initial=[{'dept': dept} for dept in depts])

	context = {
		'depts':depts,
		'course':course,
		'electives':electives,
		'elective_seats':elective_seats,
		'elective_form':elective_form,
		'elective_seats_formset':elective_seats_formset,
	}

	return render(request,'sac/add_electives_of_course.html',context)


##########################################
#        Add Elective of a Course        #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_add_elective_of_course(request):
	if request.method == 'POST':
		try:
			course_id = request.POST.get('course')
			course = Course.objects.get(course_id=course_id)
		except:
			raise Http404
			
		#Check course id was modified in browser
		saved_course_id = request.session.get('course_id')
		if saved_course_id == course_id:
			elective_form = ElectiveForm(request.POST)
			depts = Department.objects.all().order_by('name')
			ElectiveSeatsFormSet = formset_factory(ElectiveSeatsForm, extra=0)
			elective_seats_formset = ElectiveSeatsFormSet(request.POST)

			if elective_form.is_valid():
				if elective_seats_formset.is_valid():
					elective = elective_form.save()
					for elective_seat_form in elective_seats_formset:
						elective_seat_form.save(elective)
				else:
					for elective_seat_form in elective_seats_formset:
						messages.error(request, convert_form_errors_to_string(elective_seat_form))
			else:
				messages.error(request, convert_form_errors_to_string(elective_form))
		else:
			messages.error(request, 'Incorrect course')
			
		return redirect('sac_view_electives_of_course')
	
	raise Http404
			
##########################################
#       Delete Elective of a Course      #
##########################################
	
@login_required
@user_passes_test(sac_check)
def sac_delete_elective_of_course(request):
	if request.method == 'POST':
		try:
			course_id = request.POST.get('course_id')
			course = Course.objects.get(course_id=course_id)
		except:
			raise Http404
			
		#Check course id was modified in browser
		saved_course_id = request.session.get('course_id')
		if saved_course_id == course_id:
			try:
				slot = request.POST.get('slot')
				Elective.objects.get(course=course,slot=slot).delete()
			except:
				messages.error(request, 'Invalid slot')
		else:
			messages.error(request, 'Incorrect course')
			
		return redirect('sac_view_electives_of_course')
	
	raise Http404
		
##########################################
#      Add Mutually Exclusive Courses    #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_add_exclusive_courses(request):
	exclusive_course_groups = Mutually_Exclusive_Course_Group.objects.all()
	
	if request.method == 'POST':
		form = MutuallyExclusiveCourseGroupForm(request.POST)
		if form.is_valid():
			form.save()
	else:
		form = MutuallyExclusiveCourseGroupForm()
	
	context = {
		'exclusive_course_groups':exclusive_course_groups,
		'form':form,
	}

	return render(request, 'sac/add_exclusive_courses.html', context)
	
##########################################
#    Delete Mutually Exclusive Courses   #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_delete_exclusive_courses(request):
	if request.method == 'POST':
		try:
			exclusive_course_group_id = request.POST.get('exclusive_course_group_id')
			Mutually_Exclusive_Course_Group.objects.get(id=exclusive_course_group_id).delete()
		except:
			messages.error(request, 'Invalid mutually exclusive courses')
		
		return redirect('sac_add_exclusive_courses')
	
	raise Http404

						##########################################
						#             Faculty Portal             #
						##########################################
	
@login_required
@user_passes_test(department_check)
def department_home(request):
	raise Http404

						##########################################
						#            Department Portal           #
						##########################################
	
@login_required
@user_passes_test(faculty_check)
def faculty_home(request):
	raise Http404
