from django.shortcuts import render

def login(request):
	context = {}
	return render(request, 'login.html', context)

def password_reset(request):
	context = {}
	return render(request, 'password_reset.html', context)

def stage_1(request):
	context = {}
	return render(request, 'stage1.html', context)