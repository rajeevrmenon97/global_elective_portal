from django.urls import path
from django.conf.urls import include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
	###########################
	#   Authentication Views  #
	###########################
	path('accounts/',include('django.contrib.auth.urls')),
	path('',views.home,name='home'),
	
	###########################
	#   Student Portal Views  #
	###########################
	path('student/home',views.student_home,name='student_home'),
	path('student/home/academic',views.student_academic_data_submission,name='student_academic_data_submission'),
	path('student/home/electives',views.student_preference_submission,name='student_preference_submission'),
	path('student/home/allotment',views.student_allotment_publication,name='student_allotment_publication'),
	path('student/error',views.student_incomplete_previous_stage,name='student_incomplete_previous_stage'),
	
	###########################
	#     SAC Portal Views    #
	###########################
	path('sac/home',views.sac_home,name='sac_home'),
	path('sac/department',views.sac_dept,name='sac_dept'),
	path('sac/student',views.sac_student,name='sac_student'),
	path('sac/faculty',views.sac_faculty,name='sac_faculty'),
	path('sac/course',views.sac_view_courses,name='sac_view_courses'),
	path('sac/course/add',views.sac_add_course,name='sac_add_course'),
	path('sac/course/edit',views.sac_edit_course,name='sac_edit_course'),
	path('sac/course/delete',views.sac_delete_course,name='sac_delete_course'),
	path('sac/elective',views.sac_view_electives_of_course,name='sac_view_electives_of_course'),
	path('sac/elective/add',views.sac_add_elective_of_course,name='sac_add_elective_of_course'),
	path('sac/elective/delete',views.sac_delete_elective_of_course,name='sac_delete_elective_of_course'),
	path('sac/course/exclusive',views.sac_add_exclusive_courses,name='sac_add_exclusive_courses'),
	path('sac/course/exclusive/delete',views.sac_delete_exclusive_courses,name='sac_delete_exclusive_courses'),
	path('sac/cot',views.sac_cot,name='sac_cot'),	
	path('sac/academic',views.sac_academic_data,name='sac_academic_data'),
	path('sac/allotment',views.sac_allotment_data,name='sac_allotment_data'),
	path('sac/allotment/start',views.sac_start_allotment,name='sac_start_allotment'),
	
	###########################
	#   Faculty Portal Views  #
	###########################
	path('faculty/home',views.faculty_home,name='faculty_home'),
	
	###########################
	# Department Portal Views #
	###########################
	path('department/home',views.department_home,name='department_home'),
]
