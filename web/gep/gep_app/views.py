from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login as auth_login , logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Student, Elective, Course, Faculty, Department, Elective_Preference, COT_Allotment, Elective_Allotment, Elective_Seats, Mutually_Exclusive_Course_Group
from django.forms import formset_factory
from .forms import *
from datetime import datetime
from django.contrib import messages
from django.core import exceptions
from django.conf import settings
import csv
from io import BytesIO, StringIO
from zipfile import ZipFile
from .allotment import *

						##########################################
						#       Current Stage Check Functions    #
						##########################################

def is_academic_data_submission_stage():
	start_date = settings.APP_CONFIG['gep_app']['ACADEMIC_DATA_SUBMISSION_START_DATE']
	end_date = settings.APP_CONFIG['gep_app']['ACADEMIC_DATA_SUBMISSION_END_DATE']
	return datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S') < datetime.now() < datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')

def is_pre_academic_data_submission_stage():
	start_date = settings.APP_CONFIG['gep_app']['ACADEMIC_DATA_SUBMISSION_START_DATE']
	return datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S') > datetime.now()

def is_preference_submission_stage():
	start_date = settings.APP_CONFIG['gep_app']['PREFERENCE_SUBMISSION_START_DATE']
	end_date = settings.APP_CONFIG['gep_app']['PREFERENCE_SUBMISSION_END_DATE']
	return datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S') < datetime.now() < datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')

def is_pre_preference_submission_stage():
	start_date = settings.APP_CONFIG['gep_app']['PREFERENCE_SUBMISSION_START_DATE']
	return datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S') > datetime.now()

def is_allotment_publication_stage():
	start_date = settings.APP_CONFIG['gep_app']['ALLOTMENT_PUBLICATION_START_DATE']
	end_date = settings.APP_CONFIG['gep_app']['ALLOTMENT_PUBLICATION_END_DATE']
	return datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S') < datetime.now() < datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')

def is_pre_allotment_publication_stage():
	start_date = settings.APP_CONFIG['gep_app']['ALLOTMENT_PUBLICATION_START_DATE']
	return datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S') > datetime.now()

					##########################################
					#           Decorator Functions          #
					##########################################

def student_check(user):
	return user.role == get_user_model().STUDENT

def faculty_check(user):
	return user.role == get_user_model().FACULTY

def department_check(user):
	return user.role == get_user_model().DEPARTMENT

def sac_check(user):
	return user.role == get_user_model().SAC

def academic_data_submitted_check(user):
	student = Student.objects.get(user=user)
	return student.faculty_advisor is not None

def elective_preference_submitted_check(user):
	student = Student.objects.get(user=user)
	return student.submission_datetime is not None

						#####################################
						#              Login                #
						#####################################
def login(request):
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
	return electives.filter(~Q(course__dept=student.dept))

def remove_electives_with_ineligible_semesters(student, electives):
	for elective in electives:
		if student.next_semester not in elective.course.allowed_semesters:
			electives = electives.filter(~Q(pk=elective.pk))
	return electives

def remove_electives_of_core_slots(student, electives):
	return electives.filter(~Q(slot__in=student.core_slots))

def remove_electives_with_insufficient_cgpa(student, electives):
	return electives.filter(course__cgpa_cutoff__lte=student.current_cgpa)

def remove_taken_electives_and_mutually_exclusive_electives_of_taken_electives(student, electives):
	exclusive_course_groups = Mutually_Exclusive_Course_Group.objects.all()
	for course in student.past_courses.all():
		for exclusive_course_group in exclusive_course_groups:
			if course in exclusive_course_group.courses.all():
				electives = electives.filter(~Q(course__in=exclusive_course_group.courses.all()))
			else:
				electives = electives.filter(~Q(course=course))
	return electives

def remove_electives_with_cot_not_acquired(student, electives):
	for elective in electives:
		cot_requisite = COT_Allotment.objects.filter(student=student,elective=elective).exists()
		electives = electives.filter(course__cot_requisite=cot_requisite)
	return electives

def get_sorted_eligible_electives(student):
	electives = Elective.objects.all().order_by('slot', 'course__dept__name')
	return remove_electives_with_cot_not_acquired(student, remove_electives_with_insufficient_cgpa(student, remove_taken_electives_and_mutually_exclusive_electives_of_taken_electives(student, remove_electives_of_core_slots(student, remove_electives_with_ineligible_semesters(student, remove_local_electives(student, electives))))))

def get_sorted_submitted_electives(student):
	sorted_submitted_elective_ids = Elective_Preference.objects.filter(student=student).order_by('priority_rank').values_list('elective',flat=True)
	return [Elective.objects.get(pk=elective_id) for elective_id in sorted_submitted_elective_ids]

def get_queryset_difference(first_queryset,second_queryset):
	return list(set(first_queryset) - set(second_queryset))

def get_updated_and_priority_sorted_elective_list(student):
	sorted_submitted_electives = get_sorted_submitted_electives(student)
	sorted_eligible_electives = get_sorted_eligible_electives(student)
	recently_added_electives = get_queryset_difference(sorted_eligible_electives,sorted_submitted_electives)
	recently_removed_electives = get_queryset_difference(sorted_submitted_electives,sorted_eligible_electives)
	sorted_submitted_electives.extend(recently_added_electives)
	return [elective for elective in sorted_submitted_electives if elective not in recently_removed_electives]

##########################################
#             Student Home               #
##########################################
@login_required
@user_passes_test(student_check)
def student_home(request):
	user = request.user
	student = Student.objects.get(user=user)
	
	if is_academic_data_submission_stage():
		if academic_data_submitted_check(student):
			return redirect('student_academic_data_submission_done')
		else:
			return redirect('student_academic_data_submission')
	elif is_preference_submission_stage():
		if elective_preference_submitted_check(student):
			return redirect('student_preference_submission_done')
		else:
			return redirect('student_preference_submission')
	elif is_allotment_publication_stage():
		return redirect('student_allotment_publication')
	else:
		raise Http404

##########################################
#    Academic Details Submission Stage   #
##########################################
@login_required
@user_passes_test(student_check)
def student_academic_data_submission(request):
	if is_academic_data_submission_stage():
		user = request.user
		student = Student.objects.get(user=user)

		if request.method == 'POST':
			form = StudentAcademicsDataForm(request.POST, instance=student)
			if form.is_valid():
				form.save()
				return redirect('student_academic_data_submission_done')
		else:
			form = StudentAcademicsDataForm(instance=student)

		context = {
			'roll_number':user.username,
			'name': student.name,
			'form':form,
		}

		return render(request, 'student/academic_data_submission.html', context)
	
	return redirect('student_home')

@login_required
@user_passes_test(student_check)
def student_academic_data_submission_done(request):
	if is_academic_data_submission_stage():
		return render(request, 'student/academic_data_submission_done.html')
	
	return redirect('student_home')
	
###################################################
#    Previous Stages Incomplete -  Failure Page   #
###################################################
@login_required
@user_passes_test(student_check)
def student_incomplete_previous_stage(request):
	return render(request, 'student/incomplete_previous_stage.html')

#############################################
#    Elective Preference Submission Stage   #
#############################################
@login_required
@user_passes_test(student_check)
@user_passes_test(academic_data_submitted_check, login_url='student_incomplete_previous_stage')
def student_preference_submission(request):
	if is_preference_submission_stage():
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
			return redirect('student_preference_submission_done')

		electives = get_updated_and_priority_sorted_elective_list(student)
		context = {
			'electives':electives,
		}

		return render(request, 'student/preference_submission.html', context)
	
	return redirect('student_home')

@login_required
@user_passes_test(student_check)
@user_passes_test(academic_data_submitted_check, login_url='student_incomplete_previous_stage')
def student_preference_submission_done(request):
	if is_preference_submission_stage():
		return render(request, 'student/preference_submission_done.html')

	return redirect('student_home')
	
#############################################
#    Elective Allotment Publishing Stage    #
#############################################
@login_required
@user_passes_test(student_check)
@user_passes_test(academic_data_submitted_check, login_url='student_incomplete_previous_stage')
@user_passes_test(elective_preference_submitted_check, login_url='student_incomplete_previous_stage')
def student_allotment_publication(request):
	if is_allotment_publication_stage():
		user = request.user
		student = Student.objects.get(user=user)

		elective_allotments = Elective_Allotment.objects.filter(student=student)
		context = {
			'elective_allotments':elective_allotments,
		}

		return render(request, 'student/allotment.html', context)

	return redirect('student_home')


					##########################################
					#                SAC Portal              #
					##########################################

##########################################
#           Helper Functions             #
##########################################

def get_uploaded_file(request,csv_file_name):
	try:
		csv_file = request.FILES[csv_file_name]
		return csv_file, None
	except Exception as e:
		error_message = 'Unable to upload file. ' + repr(e)
		return None, error_message
		
def convert_csv_to_data(csv_file):		
	if not csv_file.name.endswith('.csv'):
		error_message = 'File is not CSV type'
		return None, error_message

	if csv_file.multiple_chunks():
		error_message = 'Uploaded file is too big (%.2f MB).' % (csv_file.size/(1000*1000),)
		return None, error_message

	file_data = csv_file.read().decode("utf-8")
	return file_data, None

def convert_form_errors_to_string(form):
	errorlist = form.errors
	for field,errors in errorlist.items():
		for error in errors:
			error_message = 'Error: %s' %(error)
			return error_message
	
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
def sac_upload_department_data(request):
	response_data = dict()
	response_data['success_status'] = True

	if request.method == 'POST':
		if is_pre_academic_data_submission_stage():
			Student.objects.all().delete()
			Faculty.objects.all().delete()
			Department.objects.all().delete()
			get_user_model().objects.filter(~Q(role=get_user_model().SAC)).delete()

			uploaded_file,error_message = get_uploaded_file(request,'department_file')
			if uploaded_file is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
			
			department_data,error_message = convert_csv_to_data(uploaded_file)
			if department_data is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
						
			lines = department_data.split("\n")[1:]
			for index, line in enumerate(lines):
				fields = line.split(",")
				try:
					username = fields[0].strip() #Extra \n and \r may be introduced during csv conversion
					name = fields[1].strip()
					email = fields[2].strip()
				except IndexError:
					response_data['error_message'] = 'Line ' + str(index+1) + ' insufficient number of fields'
					response_data['success_status'] = False
					return JsonResponse(response_data)

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
						response_data['error_message'] = 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(dept_form)
						response_data['success_status'] = False
						return JsonResponse(response_data)
				else:
					response_data['error_message'] = 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(user_form)
					response_data['success_status'] = False
					return JsonResponse(response_data)
		else:
			response_data['error_message'] = 'This data can be updated only before academic data submission stage'
			response_data['success_status'] = False
			return JsonResponse(response_data)
				
	return JsonResponse(response_data)

##########################################
#           Upload Faculty Data          #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_upload_faculty_data(request):
	response_data = dict()
	response_data['success_status'] = True
	
	if request.method == 'POST':
		if is_pre_academic_data_submission_stage():
			Student.objects.all().delete()
			Faculty.objects.all().delete()
			get_user_model().objects.filter(role=get_user_model().FACULTY).delete()
			get_user_model().objects.filter(role=get_user_model().STUDENT).delete()

			uploaded_file,error_message = get_uploaded_file(request,'faculty_file')
			if uploaded_file is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
			
			faculty_data,error_message = convert_csv_to_data(uploaded_file)
			if faculty_data is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
						
			lines = faculty_data.split("\n")[1:]
			for index, line in enumerate(lines):
				fields = line.split(",")
				try:
					username = fields[0].strip() #Extra \n and \r may be introduced during csv conversion
					name = fields[1].strip()
					email = fields[2].strip()
					dept = fields[3].strip()
				except IndexError:
					response_data['error_message'] = 'Line ' + str(index+1) + ' insufficient number of fields'
					response_data['success_status'] = False
					return JsonResponse(response_data)

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
						response_data['error_message'] = 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(faculty_form)
						response_data['success_status'] = False
						return JsonResponse(response_data)
				else:
					response_data['error_message'] = 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(user_form)
					response_data['success_status'] = False
					return JsonResponse(response_data)
		else:
			response_data['error_message'] = 'This data can be updated only before academic data submission stage'
				
	return JsonResponse(response_data)


##########################################
#           Upload Student Data          #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_upload_student_data(request):
	response_data = dict()
	response_data['success_status'] = True
	
	if request.method == 'POST':
		if is_pre_academic_data_submission_stage():
			Student.objects.all().delete()
			get_user_model().objects.filter(role=get_user_model().STUDENT).delete()

			uploaded_file,error_message = get_uploaded_file(request,'student_file')
			if uploaded_file is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
			
			student_data,error_message = convert_csv_to_data(uploaded_file)
			if student_data is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
						
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
					response_data['error_message'] = 'Line ' + str(index+1) + ' insufficient number of fields'
					response_data['success_status'] = False
					return JsonResponse(response_data)

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
						response_data['error_message'] = 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(student_form)
						response_data['success_status'] = False
						return JsonResponse(response_data)
				else:
					response_data['error_message'] = 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(user_form)
					response_data['success_status'] = False
					return JsonResponse(response_data)
		else:
			response_data['error_message'] = 'This data can be updated only before academic data submission stage'
				
	return JsonResponse(response_data)

##########################################
#          Upload Elective Data          #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_upload_elective_data(request):
	response_data = dict()
	response_data['success_status'] = True
	
	if request.method == 'POST':
		if is_pre_preference_submission_stage():
			Course.objects.all().delete()

			uploaded_file,error_message = get_uploaded_file(request,'elective_file')
			if uploaded_file is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
			
			elective_data,error_message = convert_csv_to_data(uploaded_file)
			if elective_data is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
			
			lines = elective_data.split("\n")
			for index, line in enumerate(lines):
				fields = line.split(",")
				
				if index == 0:
					depts = [field.strip() for field in fields[11:]]
					all_depts = Department.objects.all()
					for dept in all_depts:
						if not dept.user.username in depts:
							response_data['error_message'] = 'Department data incomplete'
							response_data['success_status'] = False
							return JsonResponse(response_data)
					continue
				
				try:
					course_id = fields[0].strip() #Extra \n and \r may be introduced during csv conversion
					name = fields[1].strip()
					dept = fields[2].strip()
					credits = fields[3].strip()
					pre_requisites =  None if fields[4].strip() == 'None' else fields[4].strip()
					cot_requisite = fields[5].strip()
					cgpa_cutoff = fields[6].strip()
					mode_of_allotment = fields[7].strip()
					allowed_semesters = fields[8].strip().split("/")
					faculty = None if fields[9].strip() == 'None' else fields[9].strip()
					slots = fields[10].strip().split("/")
					seats_available_in_dept = dict()
					for index, value in enumerate(depts):
						seats_available_in_dept[value] = fields[11+index].strip()
				except IndexError:
					response_data['error_message'] = 'Line ' + str(index+1) + ' insufficient number of fields'
					response_data['success_status'] = False
					return JsonResponse(response_data)
				
				course_dict = {
					'course_id':course_id,
					'name':name,
					'dept':dept,
					'credits':credits,
					'pre_requisites':pre_requisites,
					'cot_requisite':cot_requisite,
					'cgpa_cutoff':cgpa_cutoff,
					'mode_of_allotment':mode_of_allotment,
					'allowed_semesters':allowed_semesters,
				}
				
				course_form = CourseForm(course_dict)

				if course_form.is_valid():
					course = course_form.save()				
				else:
					response_data['error_message'] = 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(course_form)
					response_data['success_status'] = False
					return JsonResponse(response_data)
					
				for slot in slots:
					elective_dict = {
						'course':course.course_id,
						'slot':slot,
						'faculty':faculty,
					}
				
					elective_form = ElectiveForm(elective_dict)

					if elective_form.is_valid():
						elective = elective_form.save()
						
						for dept,max_seats in seats_available_in_dept.items():
							elective_seats_dict = {
								'elective':elective.pk,
								'dept':dept,
								'max_seats':max_seats,
							}
							
							elective_seats_form = ElectiveSeatsForm(elective_seats_dict)
							
							if elective_seats_form.is_valid():
								elective_seats_form.save()
							else:
								response_data['error_message'] = 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(elective_seats_form)
								response_data['success_status'] = False
								return JsonResponse(response_data)
					else:
						response_data['error_message'] = 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(elective_form)
						response_data['success_status'] = False
						return JsonResponse(response_data)
						
		else:
			response_data['error_message'] = 'This data can be updated only before preference submission stage'
				
	return JsonResponse(response_data)

##########################################
#        Upload COT Allotment Data       #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_upload_cot_allotment_data(request):
	response_data = dict()
	response_data['success_status'] = True
	
	if request.method == 'POST':
		if is_pre_preference_submission_stage():
			COT_Allotment.objects.all().delete()

			uploaded_file,error_message = get_uploaded_file(request,'cot_allotment_file')
			if uploaded_file is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
			
			cot_allotment_data,error_message = convert_csv_to_data(uploaded_file)
			if cot_allotment_data is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
			
			lines = cot_allotment_data.split("\n")[1:]
			for index, line in enumerate(lines):
				fields = line.split(",")
				try:
					course = fields[0].strip() #Extra \n and \r may be introduced during csv conversion
					slot = fields[1].strip()
					student = fields[2].strip()
				except IndexError:
					response_data['error_message'] = 'Line ' + str(index+1) + ' insufficient number of fields'
					response_data['success_status'] = False
					return JsonResponse(response_data)

				try:
					elective = Elective.objects.get(course=course,slot=slot)
				except exceptions.ObjectDoesNotExist:
					response_data['error_message'] = 'Invalid course or slot in line ' + str(index+1)
					response_data['success_status'] = False
					return JsonResponse(response_data)
				
				cot_allotment = {
					'elective': elective.pk,
					'student': student,
				}
				cot_allotment_form = COTAllotmentForm(cot_allotment)

				if cot_allotment_form.is_valid():
					cot_allotment_form.save()				
				else:
					response_data['error_message'] = 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(cot_allotment_form)
					response_data['success_status'] = False
					return JsonResponse(response_data)

		else:
			response_data['error_message'] = 'This data can be updated only before preference submission stage'

	return JsonResponse(response_data)

###########################################
# Upload Mutually Exclusive Elective Data #
###########################################

@login_required
@user_passes_test(sac_check)
def sac_upload_mutually_exclusive_course_group_data(request):
	response_data = dict()
	response_data['success_status'] = True
	
	if request.method == 'POST':
		if is_pre_preference_submission_stage():
			Mutually_Exclusive_Course_Group.objects.all().delete()
			
			uploaded_file,error_message = get_uploaded_file(request,'mutually_exclusive_course_group_file')
			if uploaded_file is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
			
			mutually_exclusive_course_group_data,error_message = convert_csv_to_data(uploaded_file)
			if mutually_exclusive_course_group_data is None:
				response_data['error_message'] = error_message
				response_data['success_status'] = False
				return JsonResponse(response_data)
			
			lines = mutually_exclusive_course_group_data.split("\n")
			for index, line in enumerate(lines):
				fields = line.split(",")
				mutually_exclusive_courses = [field.strip() for field in fields]

				mutually_exclusive_course_group = {
					'courses': mutually_exclusive_courses,
				}
				
				mutually_exclusive_course_group_form = MutuallyExclusiveCourseGroupForm(mutually_exclusive_course_group)
				if mutually_exclusive_course_group_form.is_valid():
					mutually_exclusive_course_group_form.save()			
				else:
					response_data['error_message'] = 'Line ' + str(index+1) + ' ' + convert_form_errors_to_string(mutually_exclusive_course_group_form)
					response_data['success_status'] = False
					return JsonResponse(response_data)

		else:
			response_data['error_message'] = 'This data can be updated only before allotment publication stage'

	return JsonResponse(response_data)

##########################################
#         Download Academic Data         #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_download_academic_data(request):
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
			if academic_data_submitted_check(student.user):
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
def sac_download_allotment_data(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="Allotment.csv"'
	
	writer = csv.writer(response)
	
	response_data = dict()
	response_data['success_status'] = True
	title_row = ['Course ID','Course Name','Slot','Roll Number','Student Name', 'Semester']
	writer.writerow(title_row)
	
	elective_allotments = Elective_Allotment.objects.all().order_by('elective__course__dept','elective__course__name','elective__slot','student__next_semester','student__name')
	for elective_allotment in elective_allotments:
		row = [elective_allotment.elective.course.course_id, elective_allotment.elective.course.name, elective_allotment.elective.get_slot_display(), elective_allotment.student.user.username, elective_allotment.student.name, elective_allotment.student.get_next_semester_display()]
		writer.writerow(row)
	
	return response
	
##########################################
#     Start Global Elective Allotment    #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_start_allotment(request):
	response_data = dict()
	response_data['success_status'] = True
	start_global_elective_allotment()
#	try:
#		start_global_elective_allotment()
#	except Exception as e:
#		response_data['success_status'] = False
#		response_data['error_message'] = 'Allotment failed ' + repr(e)
		
	return JsonResponse(response_data)

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
	MaxSeatsFormSet = formset_factory(MaxSeatsForm, extra=0)
	elective_seats_formset = MaxSeatsFormSet(initial=[{'dept': dept} for dept in depts])

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
		course_id_in_session = request.session.get('course_id')
		if course_id_in_session == course_id:
			elective_form = ElectiveForm(request.POST)
			depts = Department.objects.all().order_by('name')
			MaxSeatsFormSet = formset_factory(MaxSeatsForm, extra=0)
			elective_seats_formset = MaxSeatsFormSet(request.POST)

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
		course_id_in_session = request.session.get('course_id')
		if course_id_in_session == course_id:
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
