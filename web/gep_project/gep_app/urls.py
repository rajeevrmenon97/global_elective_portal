from django.urls import path
from django.conf.urls import include
from . import views

urlpatterns = [
	path('accounts/',include('django.contrib.auth.urls')),
	path('',views.home,name='home'),
	path('change_password',views.change_password,name='change_password'),
	path('student/home',views.student_home,name='student_home'),
	path('faculty/home',views.faculty_home,name='faculty_home'),
	path('department/home',views.department_home,name='department_home'),
]
