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
	path('student/error',views.student_test_failure,name='student_test_failure'),
	
	###########################
	#     SAC Portal Views    #
	###########################
	path('sac/home',views.sac_home,name='sac_home'),
	path('sac/startup/department',views.startup_dept,name='startup_dept'),
	path('sac/startup/student',views.startup_student,name='startup_student'),
	path('sac/startup/faculty',views.startup_faculty,name='startup_faculty'),
	path('sac/elective',views.sac_view_electives,name='sac_view_electives'),
	path('sac/elective/add',views.sac_add_elective,name='sac_add_elective'),
	path('sac/elective/slot',views.sac_add_elective_slot,name='sac_add_elective_slot'),
	
	###########################
	#   Faculty Portal Views  #
	###########################
	path('faculty/home',views.faculty_home,name='faculty_home'),
	
	###########################
	# Department Portal Views #
	###########################
	path('department/home',views.department_home,name='department_home'),
]