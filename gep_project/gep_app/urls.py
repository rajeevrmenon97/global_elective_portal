from django.urls import path
from . import views

urlpatterns = [
	path('login',views.login,name='login'),
	path('change_password',views.change_password,name='change_password'),
	path('stage_1',views.stage_1,name='stage_1'),
]
