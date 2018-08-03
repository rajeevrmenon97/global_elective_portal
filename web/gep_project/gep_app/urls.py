from django.urls import path
from . import views

urlpatterns = [
	path('login',views.login,name='login'),
	path('change_password',views.change_password,name='change_password'),
	path('student/home',views.student_home,name='student_home'),
	path('faculty/home',views.faculty_home,name='faculty_home'),
	path('department/home',views.department_home,name='department_home'),
]
