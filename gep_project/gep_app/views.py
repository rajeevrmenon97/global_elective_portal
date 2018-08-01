from django.shortcuts import render
from django.shortcuts import redirect
from .forms import LoginForm
from .models import Student

def login(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			student = Student.objects.get(roll_number=cd.get('username'))
			return redirect('stage_1')
		else:
			context = {
				'error':True,
			}
			return render(request, 'login.html', context)
	else:
		context = {
			'error':False,
		}
		return render(request, 'login.html', context)

def change_password(request):
	context = {}
	return render(request, 'change_password.html', context)

def stage_1(request):
	student = Student.objects.get(roll_number='B150243CS')
	slots = Student.SLOT_CHOICES
	context = {
		'slots':slots,
		'student':student,
	}
	return render(request, 'stage_1.html', context)