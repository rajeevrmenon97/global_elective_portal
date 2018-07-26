from django.urls import path
from . import views

urlpatterns = [
	path('login',views.login,name='login'),
	path('password_reset',views.password_reset,name='password_reset'),
	path('stage_1',views.stage_1,name='stage_1'),
]
