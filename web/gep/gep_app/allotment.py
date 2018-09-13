from .models import Student, Department, Course, Elective, Elective_Seats, Elective_Preference, Elective_Allotment
import os
import json

###############################################
#             Tentative Allotments            #
###############################################

class Allotment:
	def __init__(self):
		"""Creates a data structure for storing tentative allotments"""
		self.allotment = dict()
		
	def saveAllotment(self):
		"""Save the allotment permanantly"""
		for student in self.allotment:
			electives = self.allotment[student]
			for elective in electives:
				createElectiveAllotment(student,elective)
		
	def addAllotment(self,student,elective):
		"""Tentatively allots the elective to the student"""
		if student not in self.allotment:
			self.allotment[student] = []
		if elective not in self.allotment[student]:
			self.allotment[student].append(elective)
		
	def removeAllotment(self,student,elective):
		"""Cancel the tentative allotment of the elective to the student"""
		if student in self.allotment and elective in self.allotment[student]:
			self.allotment[student].remove(elective)		
		
	def getAllotedElectives(self,student):
		"""Returns the list of electives tentatively alloted to the student"""
		if student not in self.allotment:
			return []
		return self.allotment[student]	
		
	def checkElectiveAlloted(self,student,elective):
		"""Check whether the given elective is tentatively alloted to the student"""
		return (True if elective in self.getAllotedElectives(student) else False)
	

###############################################
#              Helper Functions               #
###############################################
	
def getAllotedSlots(allotment,student):
	"""Returns the list of slots tentatively alloted to the student"""
	return [elective.slot for elective in allotment.getAllotedElectives(student)]

def checkSlotAlloted(allotment,student,slot):
	"""Check whether the given slot is tentatively alloted to the student"""
	return (True if slot in getAllotedSlots(allotment,student) else False)

def getAllotedCourses(allotment,student):
	"""Returns the list of courses tentatively alloted to the student"""
	return [elective.course for elective in allotment.getAllotedElectives(student)]

def getAllotedElectiveOfSlot(allotment,student,slot):
	"""Returns the elective tentatively alloted to the student belonging to given slot"""
	for elective in allotment.getAllotedElectives(student):
		if elective.slot == slot:
			return elective
	return None

def getAllotedElectiveOfCourse(allotment,student,course):
	"""Returns the elective tentatively alloted to the student belonging to given course"""
	for elective in allotment.getAllotedElectives(student):
		if elective.course == course:
			return elective
	return None

def getAllotedExclusiveElectiveOfCourse(allotment,student,course):
	"""Returns the tentatively alloted exclusive course of the student for the given course"""
	exclusive_courses = getExclusiveCourses(course)
	electives = allotment.getAllotedElectives(student)
	for elective in electives:
		if elective.course in exclusive_courses:
			return elective
	return None

def checkExclusiveCourseAlloted(allotment,student,exclusive_course):
	"""Check any of the exclusive courses are already tentatively alloted to the student"""
	exclusive_courses = getExclusiveCourses(exclusive_course)
	courses = getAllotedCourses(allotment,student)
	for course in courses:
		if course in exclusive_courses:
			return True
	return False

def getLowestPreferredAllotedElective(allotment,student):
	"""Returns the lowest preferred elective amongst the electives tentatively alloted to the student"""
	lowest_priority = max([getElectivePriorityRank(student,elective) for elective in allotment.getAllotedElectives(student)])
	return getElectiveOfPriority(student,lowest_priority)

def getElectivePriorityRank(student,elective):
	"""Returns the priority rank assigned by the student to the elective"""
	return Elective_Preference.objects.get(student=student,elective=elective).priority_rank
	
def getElectiveOfPriority(student,priority):
	"""Returns the elective of the student with the given priority"""
	return Elective_Preference.objects.get(student=student,priority_rank=priority).elective

def hasHigherPriority(student,elective_A,elective_B):
	"""Returns True if student has assigned elective_A more priority rank than elective_B else False"""
	return getElectivePriorityRank(student,elective_A) < getElectivePriorityRank(student,elective_B)

def getExclusiveCourses(course):
	"""Returns the list of all exclusive courses of given course including the course itself"""
	module_dir = os.path.dirname(__file__)  # get current directory
	file_path = os.path.join(module_dir, 'rules.json')
	with open(file_path, 'r') as file:
		rules = json.load(file)
	
	exclusive_course_ids = []
	for exclusive_rule, exclusive_set in rules['exclusive_courses'].items():
		if course.course_id in exclusive_set:
			exclusive_course_ids.extend(exclusive_set)

	exclusive_courses = [Course.objects.get(course_id=course_id) for course_id in exclusive_course_ids]
	exclusive_courses.append(course)
	return exclusive_courses

def createElectiveAllotment(student,elective):
	"""Permanently allots the elective to the student"""
	Elective_Allotment.objects.create(student=student,elective=elective)


###############################################
#             Allotment Algorithm             #
###############################################
									 
def do_allotment():
	"""Performs Student-Elective allotment"""
	#All students participating in allotment
	students = Student.objects.all()
	
	#Initialise number of electives currently allocated to each student as Zero
	current_alloted_elective_count = dict()
	for student in students:
		current_alloted_elective_count[student] = 0
	
	#All students participating in allotment sorted CGPA wise
	cgpa_list = students.order_by('-current_CGPA','next_semester','submission_datetime','date_of_birth','name')
	#All students participating in allotment sorted submission datetime wise
	fcfs_list = students.order_by('submission_datetime','next_semester','-current_CGPA','date_of_birth','name')
	
	#All deparments participating in allotment
	depts = Department.objects.all()
	
	#All electives offered as global electives
	electives = Elective.objects.all()
	
	#Initialize free seats left in each elective per department as maximum seats available in it
	free_seats = dict()
	for dept in depts:
		free_seats[dept] = dict()
		for elective in electives:
			free_seats[dept][elective] = Elective_Seats.objects.get(dept=dept,elective=elective).max_seats
			
	#Keep tracks of allotment changes
	has_converged = False
	
	def addAllotment(allotment,student,elective):
		"""Tentatively allots the elective to the student"""
		allotment.addAllotment(student, elective)
		free_seats[student.dept][elective] = free_seats[student.dept][elective] - 1
		current_alloted_elective_count[student] = current_alloted_elective_count[student] + 1
		has_converged = False

	def removeAllotment(allotment,student,elective):
		"""Removes the tentative allotment of the elective to the student"""
		allotment.removeAllotment(student, elective)
		free_seats[student.dept][elective] = free_seats[student.dept][elective] + 1
		current_alloted_elective_count[student] = current_alloted_elective_count[student] - 1
		has_converged = False
			
	mode_of_allotment = 'FCFS'
	allotment = Allotment()
	#Repeats until the most stable allotment is attained
	while not has_converged:
		has_converged = True
		students = fcfs_list if (mode_of_allotment == 'FCFS') else cgpa_list

		for student in students:
			#Retrives a list of ids of all eligible electives of the student sorted priority rank-wise
			preferred_electives = Elective_Preference.objects.filter(student=student).order_by('priority_rank').values_list('elective', flat=True)
			max_elective_count = student.required_elective_count
			dept = student.dept
			
			for elective_id in preferred_electives:
				preferred_elective = Elective.objects.get(pk=elective_id)
				
				#Allows only the Electives which are not already alloted to the student, have free seats left in the student's department and has the current mode of allotment
				if not allotment.checkElectiveAlloted(student,preferred_elective) and free_seats[dept][preferred_elective] > 0 and preferred_elective.course.mode_of_allotment == mode_of_allotment:
					
					#IF any of the exclusive courses of the new elective is already alloted to the student,
					#AND there IS NO SLOT CLASH between the new elective and already alloted electives,
					#AND the new elective has a higher priority than the elective of exclusive course,
					#THEN allot the new elective and remove the elective of exclusive course
					if checkExclusiveCourseAlloted(allotment,student,preferred_elective.course) and not checkSlotAlloted(allotment,student,preferred_elective.slot):
						alloted_exclusive_elective = getAllotedExclusiveElectiveOfCourse(allotment,student,preferred_elective.course)
						if hasHigherPriority(student,preferred_elective,alloted_exclusive_elective):
							removeAllotment(allotment, student, alloted_exclusive_elective)
							addAllotment(allotment, student, preferred_elective)
					#IF any of the exclusive courses of the new elective is already alloted to the student,
					#AND there IS SLOT CLASH between the new elective and already alloted electives,
					#AND the new elective has a higher priority than: the elective of exclusive course and the elective with slot clash,
					#THEN allot the new elective and remove the elective of exclusive course and the elective with slot clash
					elif checkExclusiveCourseAlloted(allotment,student,preferred_elective.course):
						alloted_exclusive_elective = getAllotedExclusiveElectiveOfCourse(allotment,student,preferred_elective.course)
						alloted_elective = getAllotedElectiveOfSlot(allotment,student,preferred_elective.slot)
						if hasHigherPriority(student,preferred_elective,alloted_exclusive_elective) and hasHigherPriority(student,preferred_elective,alloted_elective):
							removeAllotment(allotment, student, alloted_exclusive_elective)
							removeAllotment(allotment, student, alloted_elective)
							addAllotment(allotment, student, preferred_elective)
					#IF there IS SLOT CLASH between the new elective and already alloted electives,
					#AND the new elective has a higher priority than the elective with slot clash,
					#THEN allot the new elective and remove the elective with slot clash
					elif checkSlotAlloted(allotment,student,preferred_elective.slot):
						alloted_elective = getAllotedElectiveOfSlot(allotment,student,preferred_elective.slot)
						if hasHigherPriority(student,preferred_elective,alloted_elective):
							removeAllotment(allotment, student, alloted_elective)
							addAllotment(allotment, student, preferred_elective)
					#IF the student hasn't been alloted the required number of electives
					#AND there IS NO SLOT CLASH between the new elective and already alloted electives,
					#THEN allot the new elective
					elif current_alloted_elective_count[student] < max_elective_count and not checkSlotAlloted(allotment,student,preferred_elective.slot):
						addAllotment(allotment, student, preferred_elective)
					#IF the student has been alloted the required number of electives,
					#AND there IS NO SLOT CLASH between the new elective and already alloted electives,
					#AND the new elective has a higher priority than the already alloted elective with lowest priority,
					#THEN allot the new elective and remove the already alloted elective with lowest priority
					elif current_alloted_elective_count[student] == max_elective_count and not checkSlotAlloted(allotment,student,preferred_elective.slot):
						alloted_elective = getLowestPreferredAllotedElective(allotment,student)
						if hasHigherPriority(student,preferred_elective,alloted_elective):
							removeAllotment(allotment, student, alloted_elective)
							addAllotment(allotment, student, preferred_elective)
						
		mode_of_allotment = 'CGPA' if (mode_of_allotment == 'FCFS') else 'FCFS'
	allotment.saveAllotment()
	