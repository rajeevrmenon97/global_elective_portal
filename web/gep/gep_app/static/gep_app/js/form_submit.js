$(document).ready(function() {	
	$('btn-submit').click(function(){
		var submit_button = $(this);
		var form = submit_button.closest('form');
		var main_container = $('.container-fluid:first');
		var loader = $('.loader:first');
		
		submit_button.attr('disabled','disabled');
		main_container.animate({opacity:'.5'});
		loader.fadeIn();
	});
});