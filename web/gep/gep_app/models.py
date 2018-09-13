from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.core.validators import MaxValueValidator, MinValueValidator

class User(AbstractUser):
	STUDENT = 'S'
	FACULTY = 'F'
	DEPARTMENT = 'D'
	SAC = 'A'
	ROLE_CHOICES = ((STUDENT,'Student'),(FACULTY,'Faculty'),(SAC,'Sac'),(DEPARTMENT,'Department'))

	username = models.CharField(max_length=100,primary_key=True)
	password = models.CharField(max_length=100,blank=True,null=True)
	role = models.CharField(max_length=1,choices=ROLE_CHOICES)
	email = models.EmailField(max_length=100)
	USERNAME_FIELD = 'username'

	def __str__(self):
		return '%s (%s)' % (getattr(self, self.USERNAME_FIELD), self.get_role_display())

class Department(models.Model):
	user = models.OneToOneField(get_user_model(),on_delete=models.CASCADE,primary_key=True)
	name = models.CharField(max_length=100,unique=True)

	def __str__(self):
		return '%s (%s)' % (self.name, self.user.username)

class Faculty(models.Model):
	user = models.OneToOneField(get_user_model(),on_delete=models.CASCADE,primary_key=True)
	name = models.CharField(max_length=100)
	dept = models.ForeignKey(Department, on_delete=models.CASCADE)

	def __str__(self):
		return '%s (%s)' % (self.name,self.user.username)

class Course(models.Model):
	MODE_OF_ALLOTMENT_CHOICES = (('FCFS','First Come First Served'),('CGPA','Current CGPA'),)
	course_id = models.CharField(max_length=10,primary_key=True)
	name = models.CharField(max_length=200,unique=True)
	dept = models.ForeignKey(Department, on_delete=models.CASCADE)
	credits = models.IntegerField(validators=[MinValueValidator(0)])
	pre_requisites = models.TextField(max_length=500,blank=True,null=True)
	cot_requisite = models.BooleanField(default=False)
	cgpa_cutoff = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])
	mode_of_allotment = models.CharField(max_length=4,choices=MODE_OF_ALLOTMENT_CHOICES)

	def __str__(self):
		return '%s (%s)' % (self.name, self.course_id)
	
class Student(models.Model):
	SLOT_CHOICES = (('A','Slot A'),('B','Slot B'),('C','Slot C'),('D','Slot D'),('E','Slot E'),('F','Slot F'),('G','Slot G'),('H','Slot H'),('P','Slot P'),('Q','Slot Q'),('R','Slot R'),('S','Slot S'),('T','Slot T'),)
	SEMESTER_CHOICES = ((1,'Semester I'),(2,'Semester II'),(3,'Semester III'),(4,'Semester IV'),(5,'Semester V'),(6,'Semester VI'),(7,'Semester VII'),(8,'Semester VIII'),(9,'Semester IX'),(10,'Semester X'),)

	user = models.OneToOneField(get_user_model(),on_delete=models.CASCADE,primary_key=True)
	name = models.CharField(max_length=100)
	date_of_birth = models.DateField()
	dept = models.ForeignKey(Department, on_delete=models.CASCADE)
	FA = models.ForeignKey(Faculty,blank=True,null=True,on_delete=models.PROTECT)
	current_CGPA = models.DecimalField(blank=True,null=True,decimal_places=2,max_digits=4,validators=[MinValueValidator(0),MaxValueValidator(10)])
	next_semester = models.IntegerField(blank=True,null=True,choices=SEMESTER_CHOICES)
	core_slots = ArrayField(models.CharField(max_length=1,choices=SLOT_CHOICES),blank=True,null=True)
	past_courses = models.ManyToManyField(Course,blank=True)
	required_elective_count = models.IntegerField(blank=True,null=True,validators=[MinValueValidator(0)])
	submission_datetime = models.DateTimeField(blank=True,null=True)

	def __str__(self):
		return '%s (%s)' % (self.name, self.user.username)

class Mutually_Exclusive_Courses(models.Model):
	course_group = models.ManyToManyField(Course)
	
class Elective(models.Model):
	SLOT_CHOICES = (('A','Slot A'),('B','Slot B'),('C','Slot C'),('D','Slot D'),('E','Slot E'),('F','Slot F'),('G','Slot G'),('H','Slot H'),('P','Slot P'),('Q','Slot Q'),('R','Slot R'),('S','Slot S'),('T','Slot T'),)

	course = models.ForeignKey(Course, on_delete=models.CASCADE)
	slot = models.CharField(max_length=1,choices=SLOT_CHOICES)
	faculty = models.ForeignKey(Faculty,blank=True,null=True, on_delete=models.SET_NULL)

	class Meta:
		unique_together = ('course', 'slot')

	def __str__(self):
		return '%s-%s' % (self.course.name, self.slot)

class Elective_Seats(models.Model):
	elective =  models.ForeignKey(Elective, on_delete=models.CASCADE) 
	dept = models.ForeignKey(Department, on_delete=models.CASCADE)
	max_seats = models.IntegerField()

	class Meta:
		unique_together = ('elective', 'dept')

	def __str__(self):
		return '%s-%s-%s (%d)' % (self.dept.name, self.elective.course.name, self.elective.slot, self.max_seats)

class COT_Allotment(models.Model):
	student = models.ForeignKey(Student, on_delete=models.CASCADE)
	elective = models.ForeignKey(Elective, on_delete=models.CASCADE)

	class Meta:
		unique_together = ('student', 'elective')
		
	def __str__(self):
		return '%s-%s-%s' % (self.student.name, self.elective.course.name, self.elective.slot)

class Elective_Allotment(models.Model):
	student = models.ForeignKey(Student, on_delete=models.CASCADE)
	elective = models.ForeignKey(Elective, on_delete=models.CASCADE)

	class Meta:
		unique_together = ('student', 'elective')

	def __str__(self):
		return '%s-%s-%s' % (self.student.name, self.elective.course.name, self.elective.slot)

class Elective_Preference(models.Model):
	student = models.ForeignKey(Student, on_delete=models.CASCADE)
	elective = models.ForeignKey(Elective, on_delete=models.CASCADE)
	priority_rank = models.IntegerField(validators=[MinValueValidator(0)])

	class Meta:
		unique_together = ('student', 'elective')

	def __str__(self):
		return '%s-%s-%s (%d)' % (self.student.name, self.elective.course.name, self.elective.slot, self.priority_rank)