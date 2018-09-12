$(document).ready(function() {
	$("course_submit").click(function(){
		URL = 'student/course_submit'
		data = {
			'course_id':
			'name':
			'credits':
			
		}
		$.post(URL,data,callback);
	});
});