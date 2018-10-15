from .models import Student, Department, Course, Elective, Elective_Seats, Elective_Preference, Elective_Allotment, Mutually_Exclusive_Course_Group

###############################################
#               Database APIs                 #
###############################################

def get_elective_priority_rank(student,elective):
	return Elective_Preference.objects.get(student=student,elective=elective).priority_rank
	
def get_elective_of_higher_priority(student,first_elective,second_elective):
	return first_elective if has_higher_priority(student,first_elective,second_elective) else second_elective

def has_higher_priority(student,expected_higher_priority_elective,expected_lower_priority_elective):
	return get_elective_priority_rank(student,expected_higher_priority_elective) < get_elective_priority_rank(student,expected_lower_priority_elective)

def get_mutually_exclusive_course_list(course):
	exclusive_courses = set()
	exclusive_course_groups = Mutually_Exclusive_Course_Group.objects.all()
	
	for exclusive_course_group in exclusive_course_groups:
		if course in exclusive_course_group.courses.all():
			exclusive_courses.update(exclusive_course_group.courses.all())
			
	exclusive_courses.discard(course)
	return list(exclusive_courses)
	
def get_mode_of_allotment_list():
	return [choice[0] for choice in Course.MODE_OF_ALLOTMENT_CHOICES]

def get_maximum_seats_available(dept,elective):
	return Elective_Seats.objects.get(dept=dept,elective=elective).max_seats

def get_prioritywise_sorted_elective_list_of_student(student):
	prioritywise_sorted_elective_ids = Elective_Preference.objects.filter(student=student).order_by('priority_rank').values_list('elective', flat=True)
	return [Elective.objects.get(pk=elective_id) for elective_id in prioritywise_sorted_elective_ids]

def insert_allotment_to_database(student,elective):
	Elective_Allotment.objects.create(student=student,elective=elective)
	
###############################################
#             Tentative Allotments            #
###############################################

class Tentative_Allotment:
	def __init__(self,participating_depts,participating_students,participating_electives):
		self.allotment = dict()
		for student in participating_students:
			self.allotment[student] = set()
			
		self.current_alloted_elective_count_of_student = dict()
		for student in participating_students:
			self.current_alloted_elective_count_of_student[student] = 0

		self.free_elective_seats_in_dept = dict()
		for dept in participating_depts:
			self.free_elective_seats_in_dept[dept] = dict()
			for elective in participating_electives:
				self.free_elective_seats_in_dept[dept][elective] = get_maximum_seats_available(dept,elective)
		
		self.convergence_status = False
		
	def get_allotment(self):
		return self.allotment
		
	def has_allotment_converged(self):
		return self.convergence_status
	
	def set_allotment_converged(self):
		self.convergence_status = True
	
	def check_free_elective_seats_in_dept(self,dept,elective):
		return self.free_elective_seats_in_dept[dept][elective] > 0
	
	def has_enough_electives_alloted(self,student):
		return self.current_alloted_elective_count_of_student[student] == student.required_elective_count
	
	def add_allotment(self,student,elective):
		self.allotment[student].add(elective)
		self.free_elective_seats_in_dept[student.dept][elective] = self.free_elective_seats_in_dept[student.dept][elective] - 1
		self.current_alloted_elective_count_of_student[student] = self.current_alloted_elective_count_of_student[student] + 1
		self.convergence_status = False
		
	def remove_allotment(self,student,elective):
		self.allotment[student].discard(elective)
		self.free_elective_seats_in_dept[student.dept][elective] = self.free_elective_seats_in_dept[student.dept][elective] + 1
		self.current_alloted_elective_count_of_student[student] = self.current_alloted_elective_count_of_student[student] - 1
		self.convergence_status = False
		
	def get_alloted_elective_set(self,student):
		return self.allotment[student]	
		
	def check_elective_alloted(self,student,elective):
		return elective in self.get_alloted_elective_set(student)

	def get_alloted_slot_set(self,student):
		return set([elective.slot for elective in self.get_alloted_elective_set(student)])

	def check_slot_alloted(self,student,slot):
		return slot in self.get_alloted_slot_set(student)

	def get_alloted_course_set(self,student):
		return set([elective.course for elective in self.get_alloted_elective_set(student)])

	def get_alloted_elective_of_slot(self,student,slot):
		for elective in self.get_alloted_elective_set(student):
			if elective.slot == slot:
				return elective
		return None

	def get_alloted_elective_of_course(self,student,course):
		for elective in self.get_alloted_elective_set(student):
			if elective.course == course:
				return elective
		return None

	def get_alloted_exclusive_elective_of_course(self,student,course):
		exclusive_courses = get_mutually_exclusive_course_list(course)
		alloted_electives = self.get_alloted_elective_set(student)
		for elective in alloted_electives:
			if elective.course in exclusive_courses or elective.course == course:
				return elective
		return None

	def check_exclusive_course_or_course_alloted(self,student,course):
		return self.get_alloted_exclusive_elective_of_course(student,course) is not None

	def get_lowest_preferred_alloted_elective(self,student):
		lowest_preferred_alloted_elective = None
		for elective in self.get_alloted_elective_set(student):
			if lowest_preferred_alloted_elective is None:
				lowest_preferred_alloted_elective = elective
			else:
				lowest_preferred_alloted_elective = get_elective_of_higher_priority(student,elective,lowest_preferred_alloted_elective)
		return lowest_preferred_alloted_elective
	
###############################################
#             Allotment Algorithm             #
###############################################
									 
def start_global_elective_allotment():
	Elective_Allotment.objects.all().delete()
	students = Student.objects.all()
	depts = Department.objects.all()
	electives = Elective.objects.all()
	
	modes_of_allotment = get_mode_of_allotment_list()
	student_priority_list_of_modes_of_allotment = dict() #Most preferred student will be the first element of each list.
	student_priority_list_of_modes_of_allotment['FCFS'] = students.order_by('submission_datetime','-next_semester','-current_cgpa','date_of_birth','name')
	student_priority_list_of_modes_of_allotment['CGPA'] = students.order_by('-current_cgpa','-next_semester','submission_datetime','date_of_birth','name')
	
	tentative_allotment = Tentative_Allotment(depts,students,electives)
			
	while not tentative_allotment.has_allotment_converged():
		tentative_allotment.set_allotment_converged()
		
		for mode_of_allotment in modes_of_allotment:
			student_priority_list_of_current_mode_of_allotment = student_priority_list_of_modes_of_allotment[mode_of_allotment]

			for student in student_priority_list_of_current_mode_of_allotment:
				preferred_electives = get_prioritywise_sorted_elective_list_of_student(student)

				for preferred_elective in preferred_electives:
					if tentative_allotment.check_elective_alloted(student,preferred_elective) or not tentative_allotment.check_free_elective_seats_in_dept(student.dept,preferred_elective) or not preferred_elective.course.mode_of_allotment == mode_of_allotment:
						continue

					if tentative_allotment.check_exclusive_course_or_course_alloted(student,preferred_elective.course) and not tentative_allotment.check_slot_alloted(student,preferred_elective.slot):
						alloted_exclusive_elective = tentative_allotment.get_alloted_exclusive_elective_of_course(student,preferred_elective.course)
						
						if has_higher_priority(student,preferred_elective,alloted_exclusive_elective):
							tentative_allotment.remove_allotment(student,alloted_exclusive_elective)
							tentative_allotment.add_allotment(student,preferred_elective)

					elif tentative_allotment.check_exclusive_course_or_course_alloted(student,preferred_elective.course):
						alloted_exclusive_elective = tentative_allotment.get_alloted_exclusive_elective_of_course(student,preferred_elective.course)
						alloted_elective_of_slot = tentative_allotment.get_alloted_elective_of_slot(student,preferred_elective.slot)

						if has_higher_priority(student,preferred_elective,alloted_exclusive_elective) and has_higher_priority(student,preferred_elective,alloted_elective_of_slot):
							tentative_allotment.remove_allotment(student, alloted_exclusive_elective)
							tentative_allotment.remove_allotment(student, alloted_elective_of_slot)
							tentative_allotment.add_allotment(student, preferred_elective)

					elif tentative_allotment.check_slot_alloted(student,preferred_elective.slot):
						alloted_elective_of_slot = tentative_allotment.get_alloted_elective_of_slot(student,preferred_elective.slot)

						if has_higher_priority(student,preferred_elective,alloted_elective_of_slot):
							tentative_allotment.remove_allotment(student, alloted_elective_of_slot)
							tentative_allotment.add_allotment(student, preferred_elective)

					elif tentative_allotment.has_enough_electives_alloted(student):
						lowest_preferred_alloted_elective = tentative_allotment.get_lowest_preferred_alloted_elective(student)

						if has_higher_priority(student,preferred_elective,lowest_preferred_alloted_elective):
							tentative_allotment.remove_allotment(student, lowest_preferred_alloted_elective)
							tentative_allotment.add_allotment(student, preferred_elective)
					
					else:
						tentative_allotment.add_allotment(student, preferred_elective)

	permanent_allotment = tentative_allotment.get_allotment()
	
	for student in permanent_allotment:
		electives = permanent_allotment[student]
		for elective in electives:
			insert_allotment_to_database(student,elective)
	