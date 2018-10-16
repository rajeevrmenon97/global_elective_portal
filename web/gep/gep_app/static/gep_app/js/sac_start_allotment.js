$(document).ready(function() {	
	$('.start-allotment-btn').click(function(){
		var submit_button = $(this);
		var form = submit_button.closest('.start-allotment-form');
		var error_container = form.children('.start-allotment-form-error:first');
		var main_container = $('.container-fluid:first');
		var loader = $('.loader:first');
		
		submit_button.attr('disabled','disabled');
		main_container.animate({opacity:'.5'});
		loader.fadeIn();
		var URL = form.attr('action');
		var method = form.attr('method');
		
		$.ajax({
			url:URL,
			type:method,
			dataType:'json',
			success: function(response_data) {
				loader.fadeOut();
				main_container.animate({opacity:'1'});
				submit_button.removeAttr('disabled');
				
				if(response_data['success_status']) {
					error_container.text('');
				} else {
					error_container.text(response_data['error_message']);
				}
			},
			error: function(jXHR, textStatus, errorThrown) {
				loader.fadeOut();
				main_container.animate({opacity:'1'});
				submit_button.removeAttr('disabled');
				alert(errorThrown);
			}
		})
	});
});