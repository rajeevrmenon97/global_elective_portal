from django.shortcuts import render

def login(request):
	context = {}
	return render(request, 'login.html', context)

def change_password(request):
	context = {}
	return render(request, 'change_password.html', context)

def stage_1(request):
	context = {}
	return render(request, 'stage_1.html', context)