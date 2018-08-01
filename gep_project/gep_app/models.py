from django.db import models
from django.contrib.postgres.fields import ArrayField

class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100,default="123")

    def __str__(self):
        return self.name + ' (' + self.dept_id + ')'

class Faculty(models.Model):
    faculty_id = models.CharField(max_length=10,primary_key=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100,default="123")
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + ' (' + self.faculty_id + ')'

class Student(models.Model):
    SLOT_CHOICES = (('A','Slot A'),('B','Slot B'),('C','Slot C'),('D','Slot D'),('E','Slot E'),('F','Slot F'),('G','Slot G'),('H','Slot H'),('P','Slot P'),('Q','Slot Q'),('R','Slot R'),('S','Slot S'),('T','Slot T'),)
    SEMESTER_CHOICES = ((1,'Semester I'),(2,'Semester II'),(3,'Semester III'),(4,'Semester IV'),(5,'Semester V'),(6,'Semester VI'),(7,'Semester VII'),(8,'Semester VIII'),(9,'Semester IX'),(10,'Semester X'),)

    roll_number = models.CharField(max_length=10,primary_key=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100,default="123")
    date_of_birth = models.DateField()
    email_id = models.EmailField(max_length=100)
    FA = models.ForeignKey(Faculty, on_delete=models.PROTECT)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    current_CGPA = models.DecimalField(blank=True,null=True,max_digits=4,decimal_places=2)
    next_semester = models.IntegerField(blank=True,null=True,choices=SEMESTER_CHOICES)
    core_slots = ArrayField(models.CharField(max_length=1,choices=SLOT_CHOICES),blank=True,null=True)
    no_of_global_electives = models.IntegerField(blank=True,null=True)
    submission_datetime = models.DateTimeField(blank=True,null=True)

    def __str__(self):
        return self.name + ' (' + self.roll_number + ')'

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
    roll_number = models.ForeignKey(Student,db_column='roll_number', on_delete=models.CASCADE)
    course_slot = models.ForeignKey(Course_Slots, on_delete=models.CASCADE)

class Student_Elective_Allotment(models.Model):
    roll_number = models.ForeignKey(Student,db_column='roll_number', on_delete=models.CASCADE)
    course_slot = models.ForeignKey(Course_Slots, on_delete=models.CASCADE)

class Student_Elective_Preference(models.Model):
    roll_number = models.ForeignKey(Student,db_column='roll_number', on_delete=models.CASCADE)
    course_slot = models.ForeignKey(Course_Slots, on_delete=models.CASCADE)
    priority_rank = models.IntegerField()
