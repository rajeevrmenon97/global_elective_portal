$(document).ready(function() {
	$("#add-elective").click(function(){
		URL = $('#elective-form').attr('action');
		method = $('#elective-form').attr('method');
		data = $('#elective-form').serialize() + "&course_id=" + $('#course').text();
		console.log(data)
		$.ajax({
			url:URL,
			type:method,
			data:data,
			success:function(data) {
				if (data['valid'] == true) {
				}
					console.log(data)
			},
			error:function(jXHR, textStatus, errorThrown) {
				console.log("kopp")
			}
		})
	});
});
