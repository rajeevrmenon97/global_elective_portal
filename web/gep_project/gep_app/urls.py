from django.urls import path
from django.conf.urls import include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
	path('accounts/',include('django.contrib.auth.urls')),
	path('',views.home,name='home'),
	path('student/home',views.student_home,name='student_home'),
	path('student/home/electives',views.student_preference_submission,name='student_preference_submission'),
	path('student/home/allotment',views.student_allotment,name='student_allotment'),
	path('student/error',views.student_test_failure,name='student_test_failure'),
	path('sac/home',views.sac_home,name='sac_home'),
	path('sac/startup/department',views.startup_dept,name='startup_dept'),
	path('sac/startup/student',views.startup_student,name='startup_student'),
	path('sac/startup/faculty',views.startup_faculty,name='startup_faculty'),
	path('faculty/home',views.faculty_home,name='faculty_home'),
	path('department/home',views.department_home,name='department_home'),
	path('ajax/sac/add_elective',views.add_elective,name='add_elective'),
]