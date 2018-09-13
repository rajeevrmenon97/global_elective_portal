$(document).ready(function() {
	$("#add-elective").click(function(){
		URL = $('#elective-form').attr('action');
		method = $('#elective-form').attr('method');
		data = $('#elective-form').serialize() + "&course=" + $('#course_id').text();
		console.log(data)
		$.ajax({
			url:URL,
			type:method,
			data:data,
			success:function(data) {
				if (data['valid'] == true) {
					location.reload();
				} else {
					console.log(data)
					$('#elective-error').text(data['error']);
				}
			},
			error:function(jXHR, textStatus, errorThrown) {
				$('#elective-error').text(textStatus);
			}
		})
	});
});
