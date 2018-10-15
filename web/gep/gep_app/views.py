from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, StreamingHttpResponse, HttpResponse
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
from django.conf import settings
import csv
from io import BytesIO
from zipfile import ZipFile

class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

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
	return student.FA is not None

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

def get_data_from_csv(request,return_view,csv_file_name):
	"""Retrieve the file with the given file name from the request, decode it and return, If error redirect to the given return view"""
	try:
		csv_file = request.FILES[csv_file_name]
		
		#if file is not CSV, return
		if not csv_file.name.endswith('.csv'):
			messages.error(request,'File is not CSV type')
			return redirect(return_view)
		
        #if file is too large, return
		if csv_file.multiple_chunks():
			messages.error(request,"Uploaded file is too big (%.2f MB)." % (csv_file.size/(1000*1000),))
			return redirect(return_view)
		
		file_data = csv_file.read().decode("utf-8")
		return file_data
		
	except Exception as e:
		messages.error(request,"Unable to upload file. " + repr(e))
		return redirect(return_view)

def add_error_messages_to_request(request,form,line_number):
	""" Add error messages in the given form to given request for the given line number """
	errorlist = form.errors
	for field,errors in errorlist.items():
		for error in errors:
			messages.error(request,'In line %d %s: %s' %(line_number, field, error))
			

def convert_form_errors(form):
	""" Convert form errors to string"""
	errorlist = form.errors
	for field,errors in errorlist.items():
		for error in errors:
			return 'Error in %s: %s' %(field, error)
	
##########################################
#              Startup Page              #
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
def startup_dept(request):
	""" Uploads Department data to database """
	if request.method == 'POST':
		if pre_academic_data_submission_stage_check():
			# Clear Complete Database
			Student.objects.all().delete()
			Faculty.objects.all().delete()
			Department.objects.all().delete()
			get_user_model().objects.filter(~Q(role=get_user_model().SAC)).delete()

			# Get the department data from uploaded CSV
			departments_data = get_data_from_csv(request,'sac_home','department_file')

			lines = departments_data.split("\n")[1:]
			for index, line in enumerate(lines):
				fields = line.split(",")
				username = fields[0].strip()
				name = fields[1].strip()
				email = fields[2].strip()

				# Create user for department
				user_dict = {
					'username': username,
					'email': email,
					'role': get_user_model().DEPARTMENT,
				}
				user_form = UserForm(user_dict)
				if user_form.is_valid():
					user = form.save()
					# Set default password
					user.set_password('DEPTARTMENT')
					user.save()

					# Create department
					dept_dict = {
						'user':user.username,
						'name':name,
					}
					dept_form = DepartmentForm(dept_dict)
					if dept_form.is_valid():
						dept_form.save()			
					else:
						messages.error(request, 'Line ' + str(index+1) + convert_form_errors(dept_form))
						break
				else:
					messages.error(request, 'Line ' + str(index+1) + convert_form_errors(user_form))
					break
		else:
			messages.error(request, 'This data can be updated only before academic data submission stage')
				
	return redirect('sac_home')

##########################################
#           Upload Faculty Data          #
##########################################

@login_required
@user_passes_test(sac_check)
def startup_faculty(request):
	""" Uploads Faculty data to database """
	if request.method == 'POST':
		if pre_academic_data_submission_stage_check():
			# Clear the Student and Faculty Database
			Student.objects.all().delete()
			Faculty.objects.all().delete()
			get_user_model().objects.filter(role=get_user_model().FACULTY).delete()
			get_user_model().objects.filter(role=get_user_model().STUDENT).delete()

			# Get the faculty data from uploaded CSV
			faculties_data = get_data_from_csv(request,'sac_home','faculty_file')

			lines = faculties_data.split("\n")[1:]
			for index, line in enumerate(lines):
				fields = line.split(",")
				username = fields[0].strip()
				name = fields[1].strip()
				email = fields[2].strip()
				dept = fields[3].strip()

				# Create user for faculty
				user_dict = {
					'username': username,
					'email': email,
					'role': get_user_model().FACULTY,
				}
				user_form = UserForm(user_dict)
				if user_form.is_valid():
					user = user_form.save()
					# Set default password
					user.set_password('FACULTY')
					user.save()

					# Create student
					faculty_dict = {
						'user':user.username,
						'name':name,
						'dept':dept,
					}
					faculty_form = FacultyForm(faculty_dict)
					if faculty_form.is_valid():
						faculty_form.save()			
					else:
						messages.error(request, 'Line ' + str(index+1) + convert_form_errors(faculty_form))
						break
				else:
					messages.error(request, 'Line ' + str(index+1) + convert_form_errors(user_form))
					break
		else:
			messages.error(request, 'This data can be updated only before academic data submission stage')
				
	return redirect('sac_home')


##########################################
#           Upload Student Data          #
##########################################

@login_required
@user_passes_test(sac_check)
def startup_student(request):
	""" Uploads Student data to database """
	if request.method == 'POST':
		if pre_academic_data_submission_stage_check():
			# Clear the Student Database
			Student.objects.all().delete()
			get_user_model().objects.filter(role=get_user_model().STUDENT).delete()

			# Get the student data from uploaded CSV
			students_data = get_data_from_csv(request,'sac_home','student_file')

			lines = students_data.split("\n")[1:]
			for index, line in enumerate(lines):
				fields = line.split(",")
				username = fields[0].strip()
				name = fields[1].strip()
				email = fields[2].strip()
				date_of_birth = fields[3].strip()
				dept = fields[4].strip()

				# Create user for student
				user_dict = {
					'username': username,
					'email': email,
					'role': get_user_model().STUDENT,
				}
				user_form = UserForm(user_dict)
				if user_form.is_valid():
					user = user_form.save()
					# Set default password
					user.set_password(user.username)
					user.save()

					# Create student
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
						messages.error(request, 'Line ' + str(index+1) + convert_form_errors(student_form))
						break
				else:
					messages.error(request, 'Line ' + str(index+1) + convert_form_errors(user_form))
					break
		else:
			messages.error(request, 'This data can be updated only before academic data submission stage')
				
	return redirect('sac_home')

##########################################
#             Upload COT Data            #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_consent_of_teacher(request):
	""" Uploads COT data to database """
	if request.method == 'POST':
		if pre_preference_submission_stage_check():
			# Clear the Database
			COT_Allotment.objects.all().delete()

			# Get the COT data from uploaded CSV
			cot_data = get_data_from_csv(request,'sac_home','cot_file')

			lines = cot_data.split("\n")[1:]
			for index, line in enumerate(lines):
				fields = line.split(",")
				course = fields[0].strip()
				slot = fields[1].strip()
				student = fields[2].strip()

				try:
					elective = Elective.objects.get(course=course,slot=slot)

					# Create COT allotment
					cot_dict = {
						'elective': elective,
						'student': student,
					}
					cot_allotment_form = COTAllotmentForm(cot_dict)

					if cot_allotment_form.is_valid():
						cot_allotment_form.save()				
					else:
						messages.error(request, 'Line ' + str(index+1) + convert_form_errors(cot_allotment_form))
						break
				except:
					messages.error(request, 'Invalid course or slot in line ' + str(index+1))
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
	""" Download Student's academic data as a zip file of csv files, one csv file per department """
	# Create a buffer to store the zip file
	in_memory = BytesIO()
	
	# Create a zip file
	zip = ZipFile(in_memory, "w")       
	
	# Create a csv file for each department containing academic data of students of that department
	depts = Department.objects.all().order_by('name')
	for dept in depts:
		# Create a buffer for csv file
		pseudo_buffer = Echo()
		writer = csv.writer(pseudo_buffer)
		
		# Write the titles into the csv as first row
		title_row = ['Faculty Advisor','Next Semester','Current CGPA']
		data = writer.writerow(title_row)
		
		# Write the academic data of each student into the csv
		students = Student.objects.filter(dept=dept).order_by('FA','next_semester','name')
		for student in students:
			row = [student.FA.name, student.next_semester , student.current_CGPA]
			data = writer.writerow(row)
		
		# Write the file into the zip file with the name of the file as the department name
		zip.writestr("%s.csv" %(dept.name) ,data)

	# Fix for Linux zip files read in Windows
	for file in zip.filelist:
		file.create_system = 0 

	# Close the zip file
	zip.close()

	# Return the zip file as a HttpResponse
	response = HttpResponse(content_type="application/zip")
	response["Content-Disposition"] = "attachment; filename=AcademicData.zip"
	in_memory.seek(0)    
	response.write(in_memory.read())
	return response

##########################################
#         Download Allotment Data        #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_allotment_data(request):
	""" Download Allotment data as a csv file """
	# Create a buffer for csv file
	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	
	# Write the titles into the csv as first row
	title_row = ['Course ID','Course Name','Slot','Roll Number','Student Name', 'Semester']
	data = writer.writerow(title_row)
	
	# Write the allotment data of all students to the csv file
	allotments = Elective_Allotment.objects.all().order_by('elective__course__dept','elective__course__name','elective__slot','student__next_semester','student__name')
	for allotment in allotments:
		row = [allotment.elective.course.course_id, allotment.elective.course.name, allotment.elective.slot, allotment.student.user.username, allotment.student.name, allotment.student.next_semester]
		data = writer.writerow(row)
	
	# Return the csv file as a HttpResponse
	response = StreamingHttpResponse(data, content_type="text/csv")
	response['Content-Disposition'] = 'attachment; filename="allotment.csv"'
	return response

##########################################
#            Manage Electives            #
##########################################

##########################################
#              View Courses              #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_view_electives(request):
	courses = Course.objects.all().order_by('dept__name','name')
	context = {
		'courses':courses,
	}
	return render(request, 'sac/view_electives.html', context)

##########################################
#               Add Course               #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_add_elective(request):	
	if request.method == 'POST':
		try:
			course_id = request.POST.get('course_id')
			course = Course.objects.get(course_id=course_id)
			form = CourseCreationForm(request.POST,instance=course)
		except:
			form = CourseCreationForm(request.POST)
			
		if form.is_valid():
			course = form.save()
			request.session['course_id'] = course.course_id
			return redirect('sac_view_elective_slots')
	else:
		form = CourseCreationForm()
		
	context = {
		'form':form,
	}
	
	return render(request, 'sac/add_elective.html', context)

##########################################
#              Edit Course               #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_edit_elective(request):
	if request.method == 'POST':
		try:
			course_id = request.POST.get('course_id')
			course = Course.objects.get(course_id=course_id)
			form = CourseCreationForm(instance=course)

			context = {
				'form':form,
			}
			return render(request, 'sac/add_elective.html', context)
		except:
			pass
		
	raise Http404

##########################################
#             Delete Course              #
##########################################
	
@login_required
@user_passes_test(sac_check)
def sac_delete_elective(request):
	if request.method == 'POST':
		try:
			course_id = request.POST.get('course_id')
			Course.objects.get(course_id=course_id).delete()
			return redirect('sac_view_electives')
		except:
			pass
	
	raise Http404

##########################################
#       View Electives of a Course       #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_view_elective_slots(request):
	try:
		#Get course
		course_id = request.session.get('course_id')
		course = Course.objects.get(course_id=course_id)			
		#Get electives
		electives = Elective.objects.filter(course=course)
		#Get elective seats
		elective_seats = Elective_Seats.objects.filter(elective__course=course).order_by('dept__name')

		#Create form for electives
		elective_form = ElectiveCreationForm(initial={course:course})
		#Create formset for Elective Seats of each department
		depts = Department.objects.all().order_by('name')
		ElectiveSeatsCreationFormSet = formset_factory(ElectiveSeatsCreationForm, extra=0)
		elective_seats_formset = ElectiveSeatsCreationFormSet(initial=[{'dept_name': dept.name} for dept in depts])

		context = {
			'course':course,
			'electives':electives,
			'elective_seats':elective_seats,
			'elective_form':elective_form,
			'elective_seats_formset':elective_seats_formset,
		}

		return render(request,'sac/add_elective_slots.html',context)

	except:
		raise Http404

##########################################
#        Add Elective of a Course        #
##########################################

@login_required
@user_passes_test(sac_check)
def sac_add_elective_slot(request):
	if request.method == 'POST':
		try:
			#Check course has been modified
			saved_course_id = request.session.get('course_id')
			course_id = request.POST.get('course_id')
			
			if saved_course_id == course_id:
				elective_form = ElectiveCreationForm(request.POST)
				depts = Department.objects.all().order_by('name')
				ElectiveSeatsCreationFormSet = formset_factory(ElectiveSeatsCreationForm, extra=0)
				elective_seats_formset = ElectiveSeatsCreationFormSet(request.POST)

				if elective_form.is_valid():
					if elective_seats_formset.is_valid():
							elective = elective_form.save()
							for elective_seat_form in elective_seats_formset:
								elective_seat_form.save(elective)
					else:
						messages.error(request, 'Invalid number of seats')
				else:
					messages.error(request,convert_form_errors(elective_form))
			else:
				messages.error(request, 'Incorrect course')
		except:
			raise Http404
	else:
		raise Http404
			
	return redirect('sac_view_elective_slots')

##########################################
#       Delete Elective of a Course      #
##########################################
	
@login_required
@user_passes_test(sac_check)
def sac_delete_elective_slot(request):
	if request.method == 'POST':
		try:
			#Get course
			course_id = request.POST.get('course_id')
			course = Course.objects.get(course_id=course_id)
			
			#Check course has been modified
			saved_course_id = request.session.get('course_id')
			if saved_course_id == course_id:
				try:
					slot = request.POST.get('slot')
					Elective.objects.get(course=course,slot=slot).delete()
				except:
					messages.error(request, 'Invalid slot')
			else:
				messages.error(request, 'Incorrect course')
		except:
			raise Http404
	else:
		raise Http404
		
	return redirect('sac_view_elective_slots')

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
