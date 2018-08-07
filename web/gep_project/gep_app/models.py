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
    ROLE_CHOICES = ((STUDENT,'Student'),(FACULTY,'Faculty'),(DEPARTMENT,'Department'))
    
    username = models.CharField(max_length=10,primary_key=True)
    password = models.CharField(max_length=100,default="12345")
    role = models.CharField(max_length=1,choices=ROLE_CHOICES)
    email = models.EmailField(max_length=100)
    USERNAME_FIELD = 'username'

    def is_student(self):
        return (self.role == get_user_model().STUDENT)

    def is_faculty(self):
        return (self.role == get_user_model().FACULTY)

    def is_department(self):
        return (self.role == get_user_model().DEPARTMENT)

    def __str__(self):
        return  getattr(self, self.USERNAME_FIELD) + ' (' +  self.get_role_display() + ')'

class Department(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name + ' (' + self.user.username + ')'

class Faculty(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + ' (' + self.user.username + ')'

class Student(models.Model):
    SLOT_CHOICES = (('A','Slot A'),('B','Slot B'),('C','Slot C'),('D','Slot D'),('E','Slot E'),('F','Slot F'),('G','Slot G'),('H','Slot H'),('P','Slot P'),('Q','Slot Q'),('R','Slot R'),('S','Slot S'),('T','Slot T'),)
    SEMESTER_CHOICES = ((1,'Semester I'),(2,'Semester II'),(3,'Semester III'),(4,'Semester IV'),(5,'Semester V'),(6,'Semester VI'),(7,'Semester VII'),(8,'Semester VIII'),(9,'Semester IX'),(10,'Semester X'),)

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    FA = models.ForeignKey(Faculty, on_delete=models.PROTECT)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    current_CGPA = models.DecimalField(blank=True,null=True,decimal_places=2,max_digits=4,validators=[MinValueValidator(Decimal('0')),MaxValueValidator(Decimal('10'))])
    next_semester = models.IntegerField(blank=True,null=True,choices=SEMESTER_CHOICES)
    core_slots = ArrayField(models.CharField(blank=True,null=True,max_length=1,choices=SLOT_CHOICES))
    no_of_global_electives = models.IntegerField(blank=True,null=True,validators=[MinValueValidator(0)])
    submission_datetime = models.DateTimeField(blank=True,null=True)

    def __str__(self):
        return self.name + ' (' + self.user.username + ')'

    def has_submitted(self):
        return self.submission_datetime is not None

class Course(models.Model):
    course_id = models.CharField(max_length=10,primary_key=True)
    name = models.CharField(max_length=200,unique=True)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    credits = models.IntegerField(validators=[MinValueValidator(0)])
    pre_requisites = models.TextField(max_length=500,blank=True,null=True)
    cot_requisite = models.BooleanField(default=False)
    cgpa_cutoff = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(10)])
    mode_of_allotment = models.CharField(max_length=4,choices=(('FCFS','First Come First Served'),
                                                               ('CGPA','Current CGPA'),))
    faculty = models.ForeignKey(Faculty,blank=True,null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name + ' (' + self.course_id + ')'

class Course_Slots(models.Model):
    SLOT_CHOICES = (('A','Slot A'),('B','Slot B'),('C','Slot C'),('D','Slot D'),('E','Slot E'),('F','Slot F'),('G','Slot G'),('H','Slot H'),('P','Slot P'),('Q','Slot Q'),('R','Slot R'),('S','Slot S'),('T','Slot T'),)

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    slot = models.CharField(max_length=1,choices=SLOT_CHOICES)

class Course_Departments(models.Model):
    course_slot =  models.ForeignKey(Course_Slots, on_delete=models.CASCADE) 
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    max_count = models.IntegerField()

class Student_COT_Allotment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_slot = models.ForeignKey(Course_Slots, on_delete=models.CASCADE)

class Student_Elective_Allotment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_slot = models.ForeignKey(Course_Slots, on_delete=models.CASCADE)

class Student_Elective_Preference(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_slot = models.ForeignKey(Course_Slots, on_delete=models.CASCADE)
    priority_rank = models.IntegerField(validators=[MinValueValidator(0)])
