from django.db import models
from django.contrib.postgres.fields import ArrayField

class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100,default="123")

class Faculty(models.Model):
    faculty_id = models.CharField(max_length=10,primary_key=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100,default="123")
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)

class Student(models.Model):
    roll_number = models.CharField(max_length=10,primary_key=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100,default="123")
    date_of_birth = models.DateField()
    email_id = models.EmailField(max_length=100)
    FA = models.ForeignKey(Faculty, on_delete=models.PROTECT)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    current_CGPA = models.DecimalField(blank=True,null=True,max_digits=4,decimal_places=2)
    next_semester = models.IntegerField(blank=True,null=True)
    core_slots = ArrayField(models.CharField(max_length=1,choices=(('A','A'),('B','B'),('C','C'),('D','D'),('E','E'),('F','F'),('G','G'),('H','H'),('P','P'),('Q','Q'),('R','R'),('S','S'),('T','T'),)),blank=True,null=True)
    no_of_global_electives = models.IntegerField(blank=True,null=True)
    submission_datetime = models.DateTimeField(blank=True,null=True)

class Course(models.Model):
    course_id = models.CharField(max_length=10,primary_key=True)
    name = models.CharField(max_length=200,unique=True)
    credits = models.IntegerField()
    pre_requisites = models.TextField(max_length=500,blank=True,null=True)
    cot_requisite = models.BooleanField(default=False)
    cgpa_cutoff = models.IntegerField(default=0)
    mode_of_allotment = models.CharField(max_length=4,blank=True,null=True,choices=(('FCFS','First Come First Served'),
                                                                                    ('CGPA','Current CGPA'),))
    faculty = models.ForeignKey(Faculty,blank=True,null=True, on_delete=models.SET_NULL)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)

class Course_Slots(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    slot = models.CharField(max_length=1,choices=(('A','A'),('B','B'),('C','C'),('D','D'),('E','E'),('F','F'),('G','G'),('H','H'),('P','P'),('Q','Q'),('R','R'),('S','S'),('T','T'),))

class Course_Departments(models.Model):
    course_slot =  models.ForeignKey(Course_Slots, on_delete=models.CASCADE) 
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    max_count = models.IntegerField()

class COT_Allotment(models.Model):
    roll_number = models.ForeignKey(Student,db_column='roll_number', on_delete=models.CASCADE)
    course_slot = models.ForeignKey(Course_Slots, on_delete=models.CASCADE)

class Allotment(models.Model):
    roll_number = models.ForeignKey(Student,db_column='roll_number', on_delete=models.CASCADE)
    course_slot = models.ForeignKey(Course_Slots, on_delete=models.CASCADE)

class Elective_Preference(models.Model):
    roll_number = models.ForeignKey(Student,db_column='roll_number', on_delete=models.CASCADE)
    course_slot = models.ForeignKey(Course_Slots, on_delete=models.CASCADE)
    priority_rank = models.IntegerField()
